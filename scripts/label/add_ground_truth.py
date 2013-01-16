#!/usr/bin/env python

from collections import defaultdict,namedtuple
from email.utils import parsedate_tz,mktime_tz,formatdate
from time import struct_time
import calendar
import datetime
import sys

import math

THRESHOLD = 200 # THIS IS SOMETHING THAT SHOULD BE VARY-ABLE

gt_file = open("ground_truth_tweets.txt","w+")

def distance_on_unit_sphere(lat1, long1, lat2, long2):
    # code yoinked from elsewhere                                                                                                                                                                                                                                        
    # http://www.johndcook.com/python_longitude_latitude.html                                                                                                                                                                                                                   
    # Convert latitude and longitude to                                                                                                                                                                                                                             
    # spherical coordinates in radians.                                                                                                                                                                                                                                       
    degrees_to_radians = math.pi/180.0

    # phi = 90 - latitude                                                                                                                                                                                                                                                     
    phi1 = (90.0 - lat1)*degrees_to_radians
    phi2 = (90.0 - lat2)*degrees_to_radians

    # theta = longitude                                                                                                                                                                                                                                                 
    theta1 = long1*degrees_to_radians
    theta2 = long2*degrees_to_radians

    # Compute spherical distance from spherical coordinates.                                                                                                                                                                                                                        

    # For two locations in spherical coordinates                                                                                                                                                                                                                                    
    # (1, theta, phi) and (1, theta, phi)                                                                                                                                                                                                                                           
    # cosine( arc length ) =                                                                                                                                                                                                                                                        
    #    sin phi sin phi' cos(theta-theta') + cos phi cos phi'                                                                                                                                                                                                                      
    # distance = rho * arc length                                                                                                                                                                                                             
    cos = (math.sin(phi1)*math.sin(phi2)*math.cos(theta1 - theta2) +
           math.cos(phi1)*math.cos(phi2))
#    print cos                                                                                                                                                                                                                                                                      
    arc = math.acos( round(cos,12) )

    # Remember to multiply arc by the radius of the earth                                                                                                                                                                                                                           
    # in your favorite set of units to get length.                                                                                                                                                                                                                                  

    # radius of Earth = 3 963.1676 miles                                                                                                                                                                                                                                            

    return arc*3963.1676

#>>> Point = namedtuple('Point', ['x', 'y'], verbose=True)
#USERNAME        TWEET_ID        PLACE_ID        TIME    SOURCE  LAT     LONG    TWEET
LineData = namedtuple('LineData', ['username',
                                   'tweet_id',
                                   'place_id',
                                   'time',
                                   'source',
                                   'long', # CHANGE ONCE THE PROCESSOR IS CHANGED, for now lat and long are in the wrong order!
                                   'lat',
                                   'tweet'])
days = ['M','Tu','W','Th','F','Sa','Su']
wkday = dict([[i,days[i]] for i in range(7)])

class GroundTruth:
    NONE = 0
    BEFORE = 1
    DURING = 2
    AFTER = 3
    STABLE = 4
    
    _vars = ["NONE","BEFORE","DURING","AFTER","STABLE"]
    
    @staticmethod
    def to_str(x):
        return GroundTruth._vars[x]
    

# assuming that any arguments are filenames to process
for f in sys.argv[1:]:
    
    data = [LineData(*(line.strip().split("\t"))) for line in open(f)]

    by_username = defaultdict(list)

    for line in data:
        by_username[line.username].append(line)

    for uname, line_list in by_username.iteritems():
        # now we need to split data into weeks

        by_date = defaultdict(list)
        
        for line in line_list:
            t = parsedate_tz(line.time)
            weekday = calendar.weekday(*(t[:3]))
        
            # Tu-Th, put in one pile
            # F-M, put in another
            #  (Tu = 1; F = 4)
            tuth = None

            if weekday >= 1 and weekday < 4:
                diff = (weekday-1)*3600*24 # set it as part of the past Tuesday
                tuth = "Tu"
            if weekday == 0:
                diff = 3*3600*24 # go back three days to be part of the past Friday
                tuth = "F"
            if weekday >= 4:
                diff = (weekday-4)*3600*24 # set it as part of the past Friday
                tuth = "F"
    
            wktime = mktime_tz(t) - diff
            wkdate = datetime.date(*(parsedate_tz(formatdate(wktime))[:3]))

            by_date[wkdate].append(line)

        sys.stdout.write(uname+"\n")

        avg_by_date = defaultdict(lambda:[0,0])

        last = None
        last_date = None

        prev_during_after = False
        prev_wkdate = None

        ground_truth = defaultdict(int)
        elapsed = defaultdict(tuple)

        wkdates = by_date.keys()
        wkdates.sort()
        for wkdate in wkdates:
            line_list = by_date[wkdate]
            for line in line_list:
                avg_by_date[wkdate][0] += float(line.lat) / len(by_date[wkdate])
                avg_by_date[wkdate][1] += float(line.long) / len(by_date[wkdate])

            curr = tuple(avg_by_date[wkdate])
            curr_date = wkdate
            
            if last is not None:
                dist_traveled = distance_on_unit_sphere(last[0],last[1],curr[0],curr[1])
                time_traveled = curr_date-last_date
            else:
                dist_traveled = 0
                time_traveled = datetime.timedelta(0)

            elapsed[wkdate] = (dist_traveled,time_traveled.days)
                
            last = curr
            last_date = curr_date

            sys.stdout.write("%s\t%s:\t%f, %f\t%0.3f mi\t%d days\n" % (wkday[wkdate.weekday()],
                                                              wkdate,
                                                              avg_by_date[wkdate][0],  # avg lat
                                                              avg_by_date[wkdate][1],  # avg long
                                                              dist_traveled,
                                                              time_traveled.days))

            # LABELING WITH GROUND TRUTH           

            if time_traveled.days < 14:
                if dist_traveled > THRESHOLD:
                    if prev_during_after:
                        ground_truth[prev_wkdate] = GroundTruth.DURING
                        prev_during_after = False
                    else:
                        ground_truth[prev_wkdate] = GroundTruth.BEFORE
                    
                    prev_during_after = True
                
                else:
                    if prev_during_after:
                        ground_truth[prev_wkdate] = GroundTruth.AFTER
                        prev_during_after = False
                    
                    ground_truth[wkdate] = GroundTruth.STABLE
            else:
                if prev_during_after:
                    ground_truth[prev_wkdate] = GroundTruth.AFTER
                    prev_during_after = False
                    
                ground_truth[wkdate] = GroundTruth.STABLE
            
            prev_wkdate = wkdate

        if ground_truth[prev_wkdate] == GroundTruth.NONE:
            ground_truth[prev_wkdate] = GroundTruth.AFTER
        
        sys.stdout.write("\n")
        sys.stdout.flush()

        ctr = 0
        for wkdate in wkdates:
            line_list = by_date[wkdate]
            truth_val = ground_truth[wkdate]
            
            for line in line_list:
                l = (line.username,
                     line.tweet_id,
                     line.place_id,
                     "WKID_%d" % ctr,
                     "%0.3f mi" % elapsed[wkdate][0],
                     "%d days" % elapsed[wkdate][1],
                     GroundTruth.to_str(truth_val),
                     line.time,
                     line.lat,
                     line.long,
                     line.tweet)
                gt_file.write(("\t".join(["%s" for i in range(len(l))])+"\n") % l)
            
            ctr += 1
            gt_file.flush()
        
        
        
        
        
        
        
