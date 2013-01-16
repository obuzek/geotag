import sys

f = sys.argv[1]

# USERNAME
# TWEET_ID
# PLACE_ID
# TIME
# SOURCE
# LAT
# LONG
# TWEET  

MIN_TWEETS = 5

for line in open(f):
    line_arr = line.strip().split("\t")
    
    
    
