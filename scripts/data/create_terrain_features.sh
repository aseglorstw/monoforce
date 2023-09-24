#! /bin/bash

DATA_PATH=/home/$USER/data/robingas/data
#ROBOT_NAME='marv'
#EXPERIMENT_NAME='22-08-12-cimicky_haj'
#SEQUENCE_NAME='ugv_2022-08-12-15-18-34'
#SEQUENCE_NAME='ugv_2022-08-12-16-37-03'

ROBOT_NAME='husky'
EXPERIMENT_NAME='22-09-27-unhost'/${ROBOT_NAME}
#EXPERIMENT_NAME='22-10-27-unhost-final-demo'
#SEQUENCE_NAME='husky_2022-09-27-15-01-44'
SEQUENCE_NAME='husky_2022-09-27-10-33-15'
#SEQUENCE_NAME='husky_2022-10-27-15-33-57'

source /home/$USER/workspaces/traversability_ws/devel/setup.bash
./create_terrain_features --dataset-path $DATA_PATH/$EXPERIMENT_NAME/${SEQUENCE_NAME}_trav/ \
                          --control-model diffdrive \
                          --visualize False --save-data True
