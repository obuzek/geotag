#!/usr/bin/env python

import os

d = "/export/projects/tto8/TwitterData/twitter-multilingual.v1/english/"

files = [d+f for f in os.listdir(d) if f.find(".json") != -1]
files.sort()
