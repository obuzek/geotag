#!/usr/bin/env python

import sys, re
import datetime
import calendar
import math
from collections import defaultdict
import email
from email.utils import parsedate_tz,mktime_tz #,formatdate

# assumes that the only argument is going to be the file we're processing
f = sys.argv[1]

def histogram(d):
    # assumes label : int

    maxval = max(d.values())
    interval = maxval*1.0 / 100

    hist_d = {}

    for label in d:
        hist_d[label] = "".join(["=" for i in range(int(math.ceil(d[label]/interval)))])

    return hist_d

#calendar.weekday(2010,9,11)
days = {0:"M",1:"Tu",2:"W",3:"Th",4:"F",5:"Sa",6:"Su"}

def minmax():
    return [sys.maxint,0]

tweets_on_day = defaultdict(int)
calendar_days = defaultdict(int)
hours = defaultdict(int)
user_tweet_num = defaultdict(int)
user_timespan = defaultdict(minmax)


for day in days:
    tweets_on_day[day] = 0

# we're going to assume that this takes the form of one of the outputs of the process_json script

# USERNAME
# TWEET_ID
# PLACE_ID
# TIME
# SOURCE
# LAT
# LONG
# TWEET

firstline = None

for line in open(f):
    if firstline is None:
        firstline = line
#        continue
    line_arr = line.strip().split("\t")

    timestr = line_arr[3]

    # processing time according to rfc822

    #>>> import email
    #>>> from email.utils import parsedate_tz,mktime_tz,formatdate
    #>>> formatdate(mktime_tz(parsedate_tz("Sat Jan 07 00:15:12 +0000 2012")))
    #'Sat, 07 Jan 2012 00:15:12 -0000'
    #...the parsedate_tz gets the struct_time (really just a tuple with the same ord\
    #ering as the struct_time from the time module); mktime_tz turns it into seconds\
    #relative to a timezone; and formatdate turns it back into a string!

    # ordering of time.struct_time:
    # tm_year,tm_mon,tm_mday, tm_hour,tm_min,tm_sec, tm_wday,tm_yday,tm_isdst
    date_tup = parsedate_tz(timestr)
    username = line_arr[0]
    
    weekday = calendar.weekday(date_tup[0],date_tup[1],date_tup[2])
    
    tweets_on_day[weekday] += 1
    calendar_days[tuple(date_tup[:3])] += 1
    hours[date_tup[3]] += 1
    user_tweet_num[username] += 1
    
    t = mktime_tz(date_tup)
    if t < user_timespan[username][0]:
        user_timespan[username][0] = t
    if t > user_timespan[username][1]:
        user_timespan[username][1] = t

tweet_num_buckets = defaultdict(int)

for user,num in user_tweet_num.iteritems():
    tweet_num_buckets[num / 5] += 1

print "WKDAY\tNUMTWTS"
for day,eqstr in histogram(tweets_on_day).iteritems():
    print "%s\t%d\t%s" % (days[day],tweets_on_day[day],eqstr)


tspan_buckets = defaultdict(int)
which_users = defaultdict(list)

f = open("users_longer_than_two_weeks.txt","w")

for username in user_timespan:
    elapsed = user_timespan[username][1]-user_timespan[username][0]
    tspan_buckets[(int)(elapsed / 3600 / 12)] += 1
    which_users[(int)(elapsed / 3600 / 12)].append(username)
    f.write(username+"\n")

print "\nHOURS\tNUMUSERS"
print "0",tspan_buckets[0]
tspan_buckets.pop(0)
h = histogram(tspan_buckets).items()
h.sort()
for hour,eqstr in h:
    print "%d\t%d\t%s" % (hour*12,tspan_buckets[hour],eqstr)

print "sum > 2 weeks: ", sum([tspan_buckets[h] for h in tspan_buckets if h >= 2*7*2])

print "\nDATE\tNUMTWTS"
h = histogram(calendar_days).items()
h.sort(key=lambda i:i[0][2])
for day,eqstr in h:
    print "%4d-%02d-%02d\t%d\t%s" % (day[0],day[1],day[2],calendar_days[day],eqstr)

print "\nHOUR\tNUMTWTS"
for hour,eqstr in histogram(hours).iteritems():
    print "%02d\t%d\t%s" % (hour,hours[hour],eqstr)

print "\nVOLTWTS\tNUMUSERS"
for vol,eqstr in histogram(tweet_num_buckets).iteritems():
    print "%3d\t%d\t%s" % (vol,tweet_num_buckets[vol],eqstr)
