#!/usr/bin/env python
#import sys
#import os
#import json
#import re, math
#import pickle

#from email.utils import parsedate_tz,mktime_tz,formatdate
#from time import struct_time
#import calendar
#import datetime

#import HomeRegions

#from collections import defaultdict,namedtuple,Counter
from collections import namedtuple

__all__ = ["Coordinates",
           "GeoTweetDataset",
           "UserTweets",
           "TweetSegment",
           "TweetInfo"]

Place = namedtuple("Place",["attributes",
                            "bounding_box",
                            "country",
                            "country_code",
                            "full_name",
                            "id",
                            "name",
                            "place_type",
                            "url"])
User = namedtuple("User",["id",
                          "name",
                          "screen_name",
                          "json"])
