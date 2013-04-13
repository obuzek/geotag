from Data import User, Place
from Regions.Data import Coordinates
from Regions import HomeRegions

from email.utils import parsedate_tz,mktime_tz,formatdate
from time import struct_time
import calendar
import datetime
from ..Util import bcolors

import re
import math
from collections import namedtuple, defaultdict, Counter

class TweetInfo:

    # u'coordinates': {u'coordinates': [-99.155480800000007, 19.403500319999999],
    #                 u'type': u'Point'}
    # u'geo': {u'coordinates': [19.403500319999999, -99.155480800000007],
    #                 u'type': u'Point'},
    # u'id': 156246300290060288,
    # u'id_str': u'156246300290060288',
    # u'place': {u'attributes': {},
    #            u'bounding_box': {u'coordinates': [[[-99.191678999999993,
    #                                                 19.357102000000001],
    #                                                [-99.131066000000004,
    #                                                 19.357102000000001],
    #                                                [-99.131066000000004,
    #                                                 19.404087000000001],
    #                                                [-99.191678999999993,
    #                                                 19.404087000000001]]],
    #                              u'type': u'Polygon'},
    #            u'country': u'Mexico',
    #            u'country_code': u'MX',
    #            u'full_name': u'Benito Ju\xe1rez, Distrito Federal',
    #            u'id': u'7d93122509633720',
    #            u'name': u'Benito Ju\xe1rez',
    #            u'place_type': u'city',
    #            u'url': u'http://api.twitter.com/1/geo/id/7d93122509633720.json'},

    days = ['M','Tu','W','Th','F','Sa','Su']
    wkday = dict([[i,days[i]] for i in range(7)])

    def __init__(self,d):
        self._data = d
        self.id = int(d[u'id'])
        self.place = None
        if d[u'place'] is not None:
            self.place = Place(d[u'place'][u'attributes'],
                           d[u'place'][u'bounding_box'],
                           d[u'place'][u'country'],
                           d[u'place'][u'country_code'],
                           d[u'place'][u'full_name'],
                           d[u'place'][u'id'],
                           d[u'place'][u'name'],
                           d[u'place'][u'place_type'],
                           d[u'place'][u'url'])
        self.geo = Coordinates(float(d[u'geo'][u'coordinates'][0]),
                               float(d[u'geo'][u'coordinates'][1]))
        self.tweet = d[u'text']
        self.user = User(d[u'user'][u'id'],
                         d[u'user'][u'name'],
                         d[u'user'][u'screen_name'],
                         d[u'user'])
        self.time = parsedate_tz(d[u'created_at'])
        self._wktime = mktime_tz(self.time)
        self.weekday = calendar.weekday(*(self.time[:3]))

        self.BEFORE = None
        self.STABLE_HOME = None
        self.AWAY = None
        self.AFTER = None
    
    def apply_regex(self,regex):
        return re.sub(regex,bcolors.OKBLUE+r"\1"+bcolors.ENDC,self.tweet)

    def compareTimewise(self,ut):
        # did self or ut come first?
        return mktime_tz(self.time) < mktime_tz(ut.time)

    def dateString(self):
        return datetime.date(*(parsedate_tz(formatdate(self._wktime))[:3]))

    def addTokenization(self,tokenization):
        self.tokenization = tokenization

    def addBeforeLabel(self,num_days):
        self.BEFORE = num_days
        self.STABLE_HOME = False
        self.AWAY = False

    def addAfterLabel(self,num_days):
        self.AFTER = num_days
        self.STABLE_HOME = False
        self.AWAY = False
        
    def addStableHomeLabel(self):
        self.BEFORE = None
        self.STABLE_HOME = True
        self.AWAY = False

    def addAwayLabel(self):
        self.BEFORE = None
        self.STABLE_HOME = False
        self.AWAY = True

    def predictTravel(self):
        self.PREDICT_TRAVEL = True
        self.PREDICT_STABLE = False

        if self.BEFORE is not None or self.AWAY is True:
            self.CORRECT = True
        else:
            self.CORRECT = False

    def predictStability(self):
        self.PREDICT_TRAVEL = False
        self.PREDICT_STABLE = True

        if self.BEFORE is None and self.AWAY is False:
            self.CORRECT = True
        else:
            self.CORRECT = False

class UserTweets:
    
    def __init__(self,user_id):
        self.user_id = user_id
        self._tweets = {}
    
    def getTweet(self,tweet_id):
        return self._tweets[tweet_id]

    def addTweet(self,tweet_info):
        self._tweets[tweet_info.id] = tweet_info

    def refineRegions(self,lmbda=15,user_regions=None):
        self._user_regions = user_regions
        if user_regions is None:
            self._user_regions = HomeRegions.RefineRegions(self._tweets,lmbda=lmbda)
        self.region_assmts = self._user_regions.assignments(self._tweets)

    def tweetIDiter(self):
        for tweet_id in sorted(self._tweets,key=lambda ti:self._tweets[ti].time):
            yield tweet_id 

    def defineUserHome(self,global_regions):
        region_composition = defaultdict(list)

        # populate the region_composition structure -
        # for each region that the user spends time, figure out what home
        # region they spend most of their time in
        for tweet_id,local_region in self.region_assmts.iteritems():
            tweet_info = self._tweets[tweet_id]
            globreg = global_regions.getRegionNumber(tweet_info)
            region_composition[local_region].append(globreg)
        
        time_spent_in_global_region = defaultdict(int)
        # each user region is said to belong to the home region that they most
        # commonly tweet from in that region.  the size of each user region
        # is then summed per each corresponding home region, and "home" is the
        # region where the user mostly spends their time.
        for local_region,composition in region_composition.iteritems():
            c = Counter(composition)
            corresponding_gr = c.most_common(1)[0][0]
            time_spent_in_global_region[corresponding_gr] += len(composition)
        
        self.user_home_region = max(time_spent_in_global_region,
                                    key=time_spent_in_global_region.get)

        self.user_regions_meaning_home = set([])
        for local_region,composition in region_composition.iteritems():
            c = Counter(composition)
            corresponding_gr = c.most_common(1)[0][0]
            if corresponding_gr == self.user_home_region:
                self.user_regions_meaning_home.add(local_region)

        self.home_region_info = global_regions.getRegionInfo(self.user_home_region)

        return self.user_home_region

    def segmentTweets(self):
        # separates tweets into segments, based on what region the tweet was from
        # and when the tweet happened.  the dividing lines between segments are
        # calendar days, unless a region change happens over the course of a day
        # in which a user that was previously tweeting from a home region suddenly
        # starts tweeting from an away region, or vice versa
        tweets = self._tweets.values()
        tweets.sort(key=lambda ti:mktime_tz(ti.time))

        segments = []
        today = None
        region = None
        curr_segment = []
        for tweet_info in tweets:
            new_day = tweet_info.time[:3]
            new_region = self.region_assmts[tweet_info.id] in self.user_regions_meaning_home
            if new_day != today and len(curr_segment) != 0:
                segment = TweetSegment(today,region,curr_segment)
                segment.annotateSegment(self.user_home_region)
                segments.append(segment)
                curr_segment = []
            if new_region != region and len(curr_segment) != 0:
                segment = TweetSegment(today,region,curr_segment)
                segment.annotateSegment(self.user_home_region)
                segments.append(segment)
                curr_segment = []
            curr_segment.append(tweet_info)
            today = new_day
            region = new_region
        if len(curr_segment) != 0:
            segment = TweetSegment(today,region,curr_segment)
            segment.annotateSegment(self.user_home_region)
            segments.append(segment)

        segments.sort(key=lambda ts:ts.day)

        self.time_segmented_tweets = segments

    def detectAwayPeriods(self,away_length=2,belief_strength=1):        
        # figures out the corresponding indices of time_segmented_tweets
        # where a set of tweets represents a period of time away longer
        # than away_length

        self.user_away_periods = []
        
        if len(self.time_segmented_tweets) == 0:
            return

        LENGTH_OF_DAY = 60*60*24 # seconds

        first_tweet_seg = self.time_segmented_tweets[0]
        old_date = first_tweet_seg.day
        away_periods = []
        curr_away_period = []
        away_for = 0
        if first_tweet_seg.location is False:
            away_for += 1
            curr_away_period.append(0)
        last_tweet = first_tweet_seg.tweets[-1]

        for i,tweet_seg in enumerate(self.time_segmented_tweets):
            if i == 0:
                continue
            new_date = tweet_seg.day
            time_diff_days = math.floor(mktime_tz(tweet_seg.tweets[0].time) / LENGTH_OF_DAY) - math.floor(mktime_tz(last_tweet.time) / LENGTH_OF_DAY)

            # not really using belief_strength right now; could be used to deal with
            # long time periods between tweeting
            # TODO fix treatment of belief_strength
            belief = belief_strength
            if time_diff_days > 1:
                belief = belief_strength / time_diff_days  # could get even more precise w tdiff

            if tweet_seg.location is False: # location is True at home
                curr_away_period.append(i)
                away_for += time_diff_days
            else:
                if away_for >= away_length and len(curr_away_period) > 0:
                    away_periods.append(tuple(curr_away_period))
                curr_away_period = []
                away_for = 0

            old_date = new_date
            last_tweet = tweet_seg.tweets[-1]

        if  len(curr_away_period) is not 0 and away_for >= away_length:
            away_periods.append(tuple(curr_away_period))

        self.user_away_periods = away_periods

    def annotateSegments(self,stability_thres=7):
        
        if len(self.user_away_periods) == 0:
            for tweet_seg in self.time_segmented_tweets:
                tweet_seg.addStableHomeToAll()                
            return

        # addBeforeToTweets(away_segment,stability_thres=7)

        all_segment_indices = range(len(self.time_segmented_tweets))

        ind = range(len(self.user_away_periods))
        ind.reverse()
        for i in ind:
            away_period = self.user_away_periods[i]
            for tweet_seg_ind in away_period:
                tweet_seg = self.time_segmented_tweets[tweet_seg_ind]
                tweet_seg.addAwayToAll()
                if tweet_seg_ind in all_segment_indices:
                    all_segment_indices.remove(tweet_seg_ind)
            away_index = away_period[0]
            away_index_last = away_period[-1]
            away_segment = self.time_segmented_tweets[away_index]
            away_segment_last = self.time_segmented_tweets[away_index_last]
  
            for k in reversed(range(away_index)):
                seg = self.time_segmented_tweets[k]
                time_diff = away_segment.time_in_days - seg.time_in_days
                if time_diff <= stability_thres:
                    seg.addBeforeToTweets(away_segment,stability_thres=stability_thres)
                    if k in all_segment_indices:
                        all_segment_indices.remove(k)
  

            for k in range(away_index,len(self.time_segmented_tweets)):
                seg = self.time_segmented_tweets[k]
                time_diff = away_segment_last.time_in_days - seg.time_in_days
                if time_diff <= stability_thres:
                    seg.addAfterToTweets(away_segment_last,stability_thres=stability_thres)
                    if k in all_segment_indices:
                        all_segment_indices.remove(k)
            
        # anything left is stable home; mark it as such
        for index in all_segment_indices:
            seg = self.time_segmented_tweets[index]
            seg.addStableHomeToAll()

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
