#!/usr/bin/env python

import sys
import json
import pprint

# View a json file in prettyprint mode, one data item at a time.

# usage: ./data_viewer.py filename
#
# ex:    ./data_viewer.py /export/projects/tto8/TwitterData/twitter-multilingual.v1/tweets-multilingual.v1.000.json

# Press enter to view the next data item.

# setting this flag to true means that it will skip over any tweets for users that don't have geo-enabled
geo_enabled = True

filename = sys.argv[1]

print filename

for line in open(filename):
    d = json.loads(line.strip())
    if geo_enabled and (d[u'user'][u'geo_enabled'] == False or d[u'coordinates'] == None):
        continue
    pprint.pprint(d)
    x = sys.stdin.readline()
    if x.strip() == "q":
        break
