import os
import numpy as np
from numpy.lib.recfunctions import structured_to_unstructured
from timeit import default_timer as timer
import torch
import yaml


__all__ = [
    'slots',
    'timing',
    'normalize',
    'skew_symmetric',
    'read_yaml',
    'write_to_yaml',
    'str2bool',
    'position',
    'color',
    'load_calib'
]


def slots(msg):
    """Return message attributes (slots) as list."""
    return [getattr(msg, var) for var in msg.__slots__]


def timing(f):
    def timing_wrapper(*args, **kwargs):
        t0 = timer()
        ret = f(*args, **kwargs)
        t1 = timer()
        print('%s %.6f s' % (f.__name__, t1 - t0))
        # rospy.logdebug('%s %.6f s' % (f.__name__, t1 - t0))
        return ret
    return timing_wrapper


def normalize(x, qlow=0., qhigh=1., eps=1e-6, ):
    assert qlow < qhigh
    assert qlow >= 0 and qhigh <= 1
    assert eps > 0
    """Scale to range 0..1"""
    if isinstance(x, torch.Tensor):
        x_max = torch.quantile(x, qhigh).item()
        x_min = torch.quantile(x, qlow).item()
        x = (x - x_min) / np.max([(x_max - x_min), eps])
        x = x.clamp(0, 1)
    else:
        x_max = np.percentile(x, 100 * qhigh)
        x_min = np.percentile(x, 100 * qlow)
        x = (x - x_min) / np.max([(x_max - x_min), eps])
        x = x.clip(0, 1)
    return x


def skew_symmetric(x):
    U = torch.as_tensor([[0., -x[2], x[1]],
                         [x[2], 0., -x[0]],
                         [-x[1], x[0], 0.]], device=x.device)
    return U


def read_yaml(path):
    with open(path, 'r') as f:
        data = yaml.load(f, Loader=yaml.Loader)
    return data


def write_to_yaml(cfg: dict, path):
    with open(path, 'w') as f:
        yaml.dump(cfg, f, default_flow_style=False)


def str2bool(v):
    return v.lower() in ('1', 'yes', 'true', 't', 'y')

def position(cloud):
    """Cloud to point positions (xyz)."""
    if cloud.dtype.names:
        x = structured_to_unstructured(cloud[['x', 'y', 'z']])
    else:
        x = cloud
    return x

def color(cloud):
    """Color to rgb."""
    if cloud.dtype.names:
        rgb = structured_to_unstructured(cloud[['r', 'g', 'b']])
    else:
        rgb = cloud
    return rgb


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
    T = np.asarray(calib['transformations']['T_base_link__base_footprint']['data'], dtype=np.float32).reshape((4, 4))
    calib['clearance'] = np.abs(T[2, 3])

    return calib


def compile_data(dataset, robot, lss_cfg, dphys_cfg, val_fraction=0.1, small_data=False, vis=False, **kwargs):
    from torch.utils.data import ConcatDataset, Subset
    from monoforce.datasets import Rellis3D, Rellis3DPoints, rellis3d_seq_paths
    from monoforce.datasets import RobinGas, RobinGasPoints, robingas_seq_paths
    from monoforce.datasets.utils import explore_data
    """
    Compile datasets for LSS model training

    :param dataset: str, dataset name
    :param robot: str, robot name
    :param lss_cfg: dict, LSS model configuration
    :param dphys_cfg: DPhysConfig, physical robot-terrain interaction configuration
    :param val_fraction: float, fraction of the dataset to use for validation
    :param small_data: bool, debug mode: use small datasets
    :param vis: bool, visualize training samples
    :param kwargs: additional arguments

    :return: train_ds, val_ds
    """
    train_datasets = []
    val_datasets = []
    if dataset == 'rellis3d':
        Data = Rellis3D
        DataVis = Rellis3DPoints
        data_paths = rellis3d_seq_paths
    elif dataset == 'robingas':
        Data = RobinGas
        DataVis = RobinGasPoints
        data_paths = robingas_seq_paths[robot]
    else:
        raise ValueError(f'Unknown dataset: {dataset}. Supported datasets are rellis3d and robingas.')
    print('Data paths:', data_paths)
    for path in data_paths:
        assert os.path.exists(path)
        train_ds = Data(path, is_train=True, lss_cfg=lss_cfg, dphys_cfg=dphys_cfg, **kwargs)
        val_ds = Data(path, is_train=False, lss_cfg=lss_cfg, dphys_cfg=dphys_cfg, **kwargs)

        if vis:
            train_ds_vis = DataVis(path, is_train=True, lss_cfg=lss_cfg, dphys_cfg=dphys_cfg, **kwargs)
            explore_data(train_ds_vis)

        # randomly select a subset of the dataset
        val_ds_size = int(val_fraction * len(train_ds))
        val_ids = np.random.choice(len(train_ds), val_ds_size, replace=False)
        train_ids = np.setdiff1d(np.arange(len(train_ds)), val_ids)
        assert len(train_ids) + len(val_ids) == len(train_ds)
        # check that there is no overlap between train and val ids
        assert len(np.intersect1d(train_ids, val_ids)) == 0

        train_ds = train_ds[train_ids]
        val_ds = val_ds[val_ids]
        print(f'Train dataset from path {path} size is {len(train_ds)}')
        print(f'Validation dataset from path {path} size is {len(val_ds)}')

        train_datasets.append(train_ds)
        val_datasets.append(val_ds)

    # concatenate datasets
    train_ds = ConcatDataset(train_datasets)
    val_ds = ConcatDataset(val_datasets)
    if small_data:
        print('Debug mode: using small datasets')
        train_ds = Subset(train_ds, np.random.choice(len(train_ds), min(32, len(train_ds)), replace=False))
        val_ds = Subset(val_ds, np.random.choice(len(val_ds), min(8, len(val_ds)), replace=False))
    print('Concatenated datasets length: train %i, valid: %i' % (len(train_ds), len(val_ds)))

    return train_ds, val_ds
