import math
from Regions.Data import Coordinates 
from collections import namedtuple

class TweetSegment(namedtuple("TweetSegment",["day",
                                              "location",  # True for Home, False for Away
                                              "tweets"])): # list of TweetInfo objects, chrono-sort
    def annotateSegment(self,home_region_info):
        self.home = home_region_info
        self.computeCentroid()
        self.computeDayInSeconds()
        self.calculateVariance()
    
    def calculateVariance(self):
        
        variance = 0

        for tweet_info in self.tweets:
            variance += math.pow(self.centroid.distanceOnUnitSphere(tweet_info.geo,
                                                                unit_multiplier=Coordinates.RADIUS_OF_EARTH),2)

        self.variance = math.sqrt(variance)
            
    def computeDayInSeconds(self):
        self.time_in_days = int(math.floor(mktime_tz(self.tweets[0].time) / (60*60*24)))
    
    def computeCentroid(self):
        total_latitude = 0
        total_longitude = 0
        
        for tweet_info in self.tweets:
            total_latitude += tweet_info.geo.latitude
            total_longitude += tweet_info.geo.longitude
        
        self.centroid = Coordinates(total_latitude / len(self.tweets),
                                    total_longitude / len(self.tweets))

    def addStableHomeToAll(self):
        for tweet_info in self.tweets:
            tweet_info.addStableHomeLabel()

    def addAwayToAll(self):
        for tweet_info in self.tweets:
            tweet_info.addAwayLabel()
    
    def addBeforeToTweets(self,away_segment,stability_thres=7):
        # stability_threshold is the max number of days away something can be before it's
        # considered to be part of a STABLE_HOME
        
        time_diff = away_segment.time_in_days - self.time_in_days
        
        for tweet_info in self.tweets:
            if time_diff < stability_thres and self.location is True:
                tweet_info.addBeforeLabel(time_diff)
            elif self.location is True:
                tweet_info.addStableHomeLabel()
            else:
                tweet_info.addAwayLabel()


    def addAfterToTweets(self,away_segment,stability_thres=7):
        # stability_threshold is the max number of days away something can be before it's
        # considered to be part of a STABLE_HOME
        
        time_diff = away_segment.time_in_days - self.time_in_days
        
        for tweet_info in self.tweets:
            if time_diff <= stability_thres and self.location is True:
                tweet_info.addAfterLabel(time_diff)
            elif self.location is True:
                tweet_info.addStableHomeLabel()
            else:
                tweet_info.addAwayLabel()
