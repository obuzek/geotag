from LocationChangePredictor import HomeRegions

class UserTweets:
    
    def __init__(self,user_id):
        self.user_id = user_id
        self._tweets = {}
    
    def addTweet(self,tweet_info):
        self._tweets[tweet_info.id] = tweet_info

    def refineRegions(self,lmbda=15,user_regions=None):
        self._user_regions = user_regions
        if user_regions is None:
            self._user_regions = HomeRegions.RefineRegions(self._tweets,lmbda=lmbda)
        self.region_assmts = self._user_regions.assignments(self._tweets)

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
