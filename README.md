# MonoForce

[![Arxiv](http://img.shields.io/badge/paper-arxiv.2303.01123-critical.svg?style=plastic)](https://arxiv.org/abs/2309.09007)
[![Slides](http://img.shields.io/badge/presentation-slides-orange.svg?style=plastic)](https://docs.google.com/presentation/d/1pJFHBYVeOULi-w19_mLEbDTqvvk6klcVrrYc796-2Hw/edit?usp=sharing)
[![Video](http://img.shields.io/badge/video-1min-blue.svg?style=plastic)](https://drive.google.com/file/d/1tTt1Oi5k1jKPDYn3CnzArhV3NPSNxKvD/view?usp=sharing)

Robot-terrain interaction prediction from only RGB images as input.

![](./docs/imgs/monoforce.gif)

<img src="docs/imgs/pipeline.png"/>

## Installation
Please, follow the [INSTALL.md](./docs/INSTALL.md) for the installation instructions.

## Data

Traversability data structure and processing are described in the [DATA.md](./docs/DATA.md).

## Running

To predict terrain shape and robot's trajectory from RGB images, please run:
```commandline
python scripts/run
```

If you have [ROS](http://wiki.ros.org/noetic/Installation/Ubuntu) and [Docker](https://docs.docker.com/engine/install/ubuntu/) installed you can run the demo:
```commandline
cd docker/ && ./run.sh
```

## Differentiable Physics
![](./docs/imgs/diffphysics.png)

Run the differentiable physics simulation with a robot model and the provided dataset:
```commandline
python scripts/robot_control
```

![](./docs/imgs/hm_learning.gif)
Terrain properties optimization from the ground-truth trajectories followed by the robot:
```commandline
python scripts/fit_terrain
```

## Terrain Encoder

The Terrain Encoder is a model that predicts the shape of the supporting terrain from input RGB images.
The demo video is available via the [link](https://drive.google.com/file/d/17GtA_uLyQ2o3tHiBuhxenZ0En7SzLAad/view?usp=sharing).

<img src="docs/imgs/hm_prediction_demo.png" height="280"/> <img src="docs/imgs/images_to_heightmap.png" height="280"/>

### Training

![](./docs/imgs/terrain_encoder_training.png)

1. Using the Differentiable Physics module, the terrain shape under the robot trajectory is optimized in order to match the ground-truth trajectory as closely as possible.
2. The optimized terrain shape is used as a label to train the terrain shape predictor. This model takes as input an RGB-image and predicts the shape of the supporting terrain in front of a robot.
We utilize the [Lift-Splat-Shoot (LSS)](https://github.com/nv-tlabs/lift-splat-shoot) model as the Terrain Encoder.
3. Lidar scans are used in order to provide initial height map estimates during training.

To train the LSS model, please run:
```commandline
cd scripts/
python train
```

### Weights

The pretrained weights for the LSS terrain encoder can be downloaded from:
- RobinGas: [lss_robingas_2024_03_04_09_42_47/train_lss.pt](https://drive.google.com/file/d/168W8ftzlLFOquIb1mLTrSkjgMLHDOks0/view?usp=sharing)
- RELLIS-3D: [lss_rellis3d_2024_03_06_16_07_52/train_lss.pt](https://drive.google.com/file/d/12WUNFXFHsm3hM1Ov-Ap1yRybOif6-Vi4/view?usp=sharing)

## ROS Integration

We provide a ROS node that integrates the trained Terrain Encoder model with the Differentiable Physics module.
Given the input RGB images and cameras calibration, the Terrain Encoder predicts the terrain shape,
which is then used to simulate robot trajectories.

```commandline
roslaunch monoforce lss_demo.launch
```

## Citation

Consider citing the paper if you find it relevant to your research:

```bibtex
@article{agishev2023monoforce,
    title={MonoForce: Self-supervised Learning of Physics-aware Model for Predicting Robot-terrain Interaction},
    author={Ruslan Agishev and Karel Zimmermann and Vladimír Kubelka and Martin Pecka and Tomáš Svoboda},
    year={2023},
    eprint={2309.09007},
    archivePrefix={arXiv},
    primaryClass={cs.RO}
}
```
