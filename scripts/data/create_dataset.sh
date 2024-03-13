#!/bin/bash

# This script creates a dataset from a bag file
# It saves point clouds and trajectories from a bag file
# It also adds calibrations: camera info and transforms

INPUT_STEP=10
VIS=False
SAVE=True

# list of bag files in a directory
BAG_PATHS='/media/ruslan/data/ORU/2024_02_07_Husky_campus_forest_bushes/bags/radarize__2024-02-07-10-47-13_0.bag
           /media/ruslan/data/ORU/2024_02_07_Husky_campus_forest_bushes/bags/radarize__2024-02-07-10-48-58_1.bag
           /media/ruslan/data/ORU/2024_02_07_Husky_campus_forest_bushes/bags/radarize__2024-02-07-10-51-05_2.bag
           /media/ruslan/data/ORU/2024_02_07_Husky_campus_forest_bushes/bags/radarize__2024-02-07-10-52-55_3.bag
           /media/ruslan/data/ORU/2024_02_07_Husky_campus_forest_bushes/bags/radarize__2024-02-07-10-54-50_4.bag
           /media/ruslan/data/ORU/2024_02_07_Husky_campus_forest_bushes/bags/radarize__2024-02-07-10-57-02_5.bag
           /media/ruslan/data/ORU/2024_02_07_Husky_campus_forest_bushes/bags/radarize__2024-02-07-10-59-07_6.bag
           /media/ruslan/data/ORU/2024_02_07_Husky_campus_forest_bushes/bags/radarize__2024-02-07-11-00-59_7.bag
           /media/ruslan/data/ORU/2024_02_07_Husky_campus_forest_bushes/bags/radarize__2024-02-07-11-02-34_8.bag
           /media/ruslan/data/ORU/2024_02_07_Husky_campus_forest_bushes/bags/radarize__2024-02-07-11-04-24_9.bag
           /media/ruslan/data/ORU/2024_02_07_Husky_campus_forest_bushes/bags/radarize__2024-02-07-11-06-24_10.bag
           /media/ruslan/data/ORU/2024_02_07_Husky_campus_forest_bushes/bags/postproc/map2odom.bag
           /media/ruslan/data/ORU/2024_02_07_Husky_campus_forest_bushes/bags/postproc/points.bag'
#BAG_PATHS='/media/ruslan/data/ORU/2024_02_07_Husky_campus_forest_bushes/bags/radarize__2024-02-07-10-47-13_0.bag
#           /media/ruslan/data/ORU/2024_02_07_Husky_campus_forest_bushes/bags/postproc/map2odom.bag
#           /media/ruslan/data/ORU/2024_02_07_Husky_campus_forest_bushes/bags/postproc/points.bag'
CLOUD_TOPIC='ouster/points_deskewed'
LIDAR_FRAME='os_sensor'
CAMERA_TOPICS='/ids_camera/image_raw/compressed'
CAMERA_INFO_TOPICS='/ids_camera/camera_info'

#BAG_PATHS='/media/ruslan/data/bags/husky_sim/husky_cubes_random_walk_2024-02-12-15-08-00.bag'
#CLOUD_TOPIC='points'
#LIDAR_FRAME='os_sensor'
#CAMERA_TOPICS='/realsense_front/color/image_raw/compressed
#               /realsense_left/color/image_raw/compressed
#               /realsense_rear/color/image_raw/compressed
#               /realsense_right/color/image_raw/compressed'
#CAMERA_INFO_TOPICS='/realsense_front/color/camera_info
#                    /realsense_left/color/camera_info
#                    /realsense_rear/color/camera_info
#                    /realsense_right/color/camera_info'

#BAG_PATHS='/media/ruslan/data/robingas/data/22-10-27-unhost-final-demo/husky_2022-10-27-15-33-57.bag
#           /media/ruslan/data/robingas/data/22-10-27-unhost-final-demo/husky_2022-10-27-15-33-57_loc.bag'
##BAG_PATHS='/media/ruslan/data/robingas/data/22-09-27-unhost/husky/husky_2022-09-27-10-33-15.bag
##           /media/ruslan/data/robingas/data/22-09-27-unhost/husky/husky_2022-09-27-10-33-15_loc.bag'
##BAG_PATHS='/media/ruslan/data/robingas/data/22-09-27-unhost/husky/husky_2022-09-27-15-01-44.bag'
#CLOUD_TOPIC='points'
#LIDAR_FRAME='os_sensor'
#CAMERA_TOPICS='/camera_front/image_color/compressed
#               /camera_left/image_color/compressed
#               /camera_rear/image_color/compressed
#               /camera_right/image_color/compressed'
#CAMERA_INFO_TOPICS='/camera_front/camera_info
#                    /camera_left/camera_info
#                    /camera_rear/camera_info
#                    /camera_right/camera_info'

# source ROS workspace
source /home/$USER/workspaces/traversability_ws/devel/setup.bash

# save sensor data
./save_sensor_data --bag-paths ${BAG_PATHS} \
                   --cloud-topics ${CLOUD_TOPIC} \
                   --lidar-frame ${LIDAR_FRAME} \
                   --camera-topics ${CAMERA_TOPICS} \
                   --camera-info-topics ${CAMERA_INFO_TOPICS} \
                   --robot-model 'Box()' --discard-model 'Box()' \
                   --input-step ${INPUT_STEP} --visualize $VIS --save-data $SAVE \
                   --fixed-frame map