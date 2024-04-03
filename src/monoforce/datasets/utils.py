import os

import matplotlib as mpl
import numpy as np
import torch
import yaml
from tqdm import tqdm

from monoforce.cloudproc import hm_to_cloud
from monoforce.models.lss.model import compile_model
from monoforce.models.lss.tools import ego_to_cam, get_only_in_img_mask, denormalize_img

from ..config import DPhysConfig
from ..transformations import xyz_rpy_to_matrix
from ..vis import set_axes_equal
from matplotlib import pyplot as plt
from scipy.spatial.transform import Rotation
from mpl_toolkits.mplot3d import Axes3D


__all__ = [
    'get_robingas_data',
    'get_kkt_data',
    'get_simple_data',
    'vis_dem_data',
    'load_calib',
    'explore_data'
]


def get_robingas_data(cfg: DPhysConfig(),
                      path='/home/ruslan/data/robingas/data/22-08-12-cimicky_haj/marv/ugv_2022-08-12-15-18-34/',
                      i=None):
    from monoforce.datasets.robingas import DEMPathData
    # Load traversability data
    assert os.path.exists(path)
    ds = DEMPathData(path, dphys_cfg=cfg)
    i = np.random.choice(range(len(ds))) if i is None else i
    print('Selected data sample #{}'.format(i))
    sample = ds[i]
    cloud, traj, height = sample
    traj['stamps'] = traj['stamps'] - traj['stamps'][0]
    return height, traj


def get_kkt_data(cfg: DPhysConfig(), i=None,
                 path='/home/ruslan/workspaces/traversability_ws/src/pose-consistency-KKT-loss/', dt=3.):
    import sys
    sys.path.append(os.path.join(path, 'scripts'))
    import dataset_real_rpz

    # non-configurable parameters (constants) of the dataset
    assert cfg.grid_res == 0.1
    assert cfg.d_min == -12.75
    assert cfg.d_max == 12.85

    dataset = dataset_real_rpz.Dataset(os.path.join(path, 'data', 's2d_tst/'))

    i = np.random.choice(range(len(dataset))) if i is None else i
    print('Selected data sample #{}'.format(i))
    data = dataset[i]

    # get height map
    height = data['label_dem'].squeeze()

    # get trajectory
    roll_label = data['label_rpz'][0].T
    pitch_label = data['label_rpz'][1].T
    z_label = data['label_rpz'][2].T
    yaw_label = data['yaw'].T
    xy_grid = 1. - np.isnan(z_label)
    # find non zero elements ids of the 2D array
    x_grid, y_grid = np.where(xy_grid)
    z = z_label[x_grid, y_grid]
    roll = roll_label[x_grid, y_grid]
    pitch = pitch_label[x_grid, y_grid]
    yaw = yaw_label[x_grid, y_grid]
    x = x_grid * cfg.grid_res + cfg.d_min
    y = y_grid * cfg.grid_res + cfg.d_min
    xyz_rpy = np.vstack((x, y, z, roll, pitch, yaw)).T

    # transform xyz_rpy to transformation matrices (N x 4 x 4)
    poses = np.asarray([xyz_rpy_to_matrix(p) for p in xyz_rpy])

    traj = {'poses': poses, 'stamps': np.arange(poses.shape[0]) * dt}
    height = height.T

    return height, traj


def get_simple_data(cfg: DPhysConfig):
    h, w = (cfg.d_max - cfg.d_min) / cfg.grid_res, (cfg.d_max - cfg.d_min) / cfg.grid_res
    h, w = int(h), int(w)
    height = np.zeros((h, w))
    poses = np.asarray([np.eye(4) for _ in range(10)])
    N = 10
    poses[:, 0, 3] = np.linspace(0, 0.6 * cfg.d_max, N)
    poses[:, 1, 3] = np.linspace(0, 0.2 * cfg.d_max, N) ** 1.
    Rs = [Rotation.from_euler('z', np.arctan((poses[i+1, 1, 3] - poses[i, 1, 3]) / (poses[i+1, 0, 3] - poses[i, 0, 3]))).as_matrix() for i in range(N-1)]
    Rs.append(Rs[-1])
    poses[:, :3, :3] = np.asarray(Rs)
    stamps = np.arange(N)
    traj = {'poses': poses, 'stamps': stamps}
    return height, traj


def vis_dem_data(height, traj, img=None, cfg=DPhysConfig()):
    assert len(height.shape) == 2, 'Height map should be 2D'
    assert len(traj['poses'].shape) == 3, 'Trajectory should be 3D'
    plt.figure(figsize=(20, 10))
    # add subplot
    ax = plt.subplot(131)
    ax.set_title('Height map')
    ax.imshow(height.T, cmap='jet', origin='lower', vmin=-1, vmax=1)
    x, y = traj['poses'][:, 0, 3], traj['poses'][:, 1, 3]
    h, w = height.shape
    x_grid, y_grid = x / cfg.grid_res + w / 2, y / cfg.grid_res + h / 2
    plt.plot(x_grid, y_grid, 'rx-', label='Robot trajectory')
    time_ids = np.linspace(1, len(x_grid), len(x_grid), dtype=int)
    # plot time indices for each waypoint in a trajectory
    for i, txt in enumerate(time_ids):
        ax.annotate(txt, (x_grid[i], y_grid[i]))
    plt.legend()

    # visualize heightmap as a surface in 3D
    X = np.arange(-cfg.d_max, cfg.d_max, cfg.grid_res)
    Y = np.arange(-cfg.d_max, cfg.d_max, cfg.grid_res)
    X, Y = np.meshgrid(X, Y)
    Z = height
    ax = plt.subplot(132, projection='3d')
    ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap='viridis', edgecolor='none')
    ax.set_title('Height map')
    set_axes_equal(ax)

    if img is not None:
        # visualize image
        ax = plt.subplot(133)
        ax.imshow(img)
        ax.set_title('Camera view')
        ax.axis('off')

    plt.show()


def load_calib(calib_path):
    calib = {}
    # read camera calibration
    cams_path = os.path.join(calib_path, 'cameras')
    if not os.path.exists(cams_path):
        print('No cameras calibration found in path {}'.format(cams_path))
        return None

    for file in os.listdir(cams_path):
        if file.endswith('.yaml'):
            with open(os.path.join(cams_path, file), 'r') as f:
                cam_info = yaml.load(f, Loader=yaml.FullLoader)
                calib[file.replace('.yaml', '')] = cam_info
            f.close()
    # read cameras-lidar transformations
    trans_path = os.path.join(calib_path, 'transformations.yaml')
    with open(trans_path, 'r') as f:
        transforms = yaml.load(f, Loader=yaml.FullLoader)
    f.close()
    calib['transformations'] = transforms
    calib['clearance'] = np.abs(np.asarray(calib['transformations']['T_base_link__base_footprint']['data'], dtype=np.float32).reshape((4, 4))[2, 3])

    return calib


if __name__ == '__main__':
    cfg = DPhysConfig()
    # cfg.d_min, cfg.d_max = -12.75, 12.85
    # cfg.grid_res = 0.1

    cfg.d_min, cfg.d_max = -8., 8.
    cfg.grid_res = 0.2

    hm, traj = get_robingas_data(cfg)
    vis_dem_data(hm['z'], traj, cfg)
    # height, traj = get_kkt_data(cfg)
    # visualize_data(height, traj, cfg)
    # height, traj = get_simple_data(cfg)
    # visualize_data(height, traj, cfg)


def explore_data(ds, modelf=None, sample_range='random', save=False):
    lss_cfg = ds.lss_cfg
    dphys_cfg = ds.dphys_cfg
    grid_conf = lss_cfg['grid_conf']
    data_aug_conf = lss_cfg['data_aug_conf']
    model = compile_model(grid_conf, data_aug_conf, outC=1)
    if modelf is not None:
        model.load_state_dict(torch.load(modelf))
        print('Loaded LSS model from', modelf)
        model.eval()

    H, W = ds.get_raw_img_size()
    cams = ds.cameras

    if sample_range == 'random':
        sample_range = [np.random.choice(range(len(ds)))]
    elif sample_range == 'all':
        sample_range = tqdm(range(len(ds)), total=len(ds))
    else:
        assert isinstance(sample_range, list) or isinstance(sample_range, np.ndarray) or isinstance(sample_range, range)

    for sample_i in sample_range:
        n_rows, n_cols = 2, int(np.ceil(len(cams) / 2) + 2)
        fig = plt.figure(figsize=(5 * n_cols, 5 * n_rows))
        gs = mpl.gridspec.GridSpec(n_rows, n_cols)
        gs.update(wspace=0.0, hspace=0.0, left=0.0, right=1.0, top=1.0, bottom=0.0)

        sample = ds[sample_i]
        sample = [s[np.newaxis] for s in sample]
        # print('sample', sample_i, 'id', ds.ids[sample_i])
        imgs, rots, trans, intrins, post_rots, post_trans, hm_rigid, pts = sample
        height_rigid, mask_rigid = hm_rigid[:, 0], hm_rigid[:, 1]
        if modelf is not None:
            with torch.no_grad():
                # replace height maps with model output
                inputs = [imgs, rots, trans, intrins, post_rots, post_trans]
                inputs = [torch.as_tensor(i, dtype=torch.float32) for i in inputs]
                height_rigid = model(*inputs)
                # replace lidar cloud with model height map output
                pts = hm_to_cloud(height_rigid.squeeze(), dphys_cfg).T
                pts = pts.unsqueeze(0)

        frustum_pts = model.get_geometry(rots, trans, intrins, post_rots, post_trans)

        for si in range(imgs.shape[0]):
            plt.clf()
            final_ax = plt.subplot(gs[:, -1:])
            for imgi, img in enumerate(imgs[si]):
                cam_pts = ego_to_cam(pts[si], rots[si, imgi], trans[si, imgi], intrins[si, imgi])
                mask = get_only_in_img_mask(cam_pts, H, W)
                plot_pts = post_rots[si, imgi].matmul(cam_pts) + post_trans[si, imgi].unsqueeze(1)

                ax = plt.subplot(gs[imgi // int(np.ceil(len(cams) / 2)), imgi % int(np.ceil(len(cams) / 2))])
                showimg = denormalize_img(img)

                plt.imshow(showimg)
                plt.scatter(plot_pts[0, mask], plot_pts[1, mask], c=pts[si, 2, mask],
                            s=1, alpha=0.2, cmap='jet', vmin=-1, vmax=1)
                plt.axis('off')
                # camera name as text on image
                plt.text(0.5, 0.9, cams[imgi].replace('_', ' '),
                         horizontalalignment='center', verticalalignment='top',
                         transform=ax.transAxes, fontsize=10)

                plt.sca(final_ax)
                plt.plot(frustum_pts[si, imgi, :, :, :, 0].view(-1), frustum_pts[si, imgi, :, :, :, 1].view(-1), '.',
                         label=cams[imgi].replace('_', ' '))

            plt.legend(loc='upper right')
            final_ax.set_aspect('equal')
            plt.xlim((-dphys_cfg.d_max, dphys_cfg.d_max))
            plt.ylim((-dphys_cfg.d_max, dphys_cfg.d_max))

            ax = plt.subplot(gs[:, -2:-1])
            plt.imshow(height_rigid[si].T, origin='lower', cmap='jet', vmin=-1., vmax=1.)
            plt.axis('off')
            plt.colorbar()

            if save:
                save_dir = os.path.join(ds.path, 'visuals_pred' if modelf is not None else 'visuals')
                os.makedirs(save_dir, exist_ok=True)
                imname = f'{ds.ids[sample_i]}.jpg'
                imname = os.path.join(save_dir, imname)
                # print('saving', imname)
                plt.savefig(imname)
                plt.close(fig)
            else:
                plt.show()
