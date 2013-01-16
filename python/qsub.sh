#!/bin/bash

#$ -l mem_free=55G

DATA_DIR=/export/projects/tto8/TwitterData/twitter-multilingual.v1
CODE=/export/projects/tto8/CommunicantAttributes/data/data_ob

cd $DATA_DIR

cd $CODE/geotag/code/sys

python ConsequentialLocationChangePredictor.py $DATA_DIR/*.json