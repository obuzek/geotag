import TweetInfo, UserTweets
from collections import defaultdict
import Place, User

class GeoTweetDataset:

    def __init__(self,md5):
        self.md5 = md5
        
        self.tweets = {}
        self.user_infos = {}
        self.places = {}
        self.coords = []
        
        self.user_tweets_by_user_id = {}
        self.tweet_id_by_user_id = defaultdict(list)
        self.user_id_by_tweet_id = defaultdict(list)
        self.place_id_by_tweet_id = defaultdict(list)
        self.tweet_id_by_place_id = defaultdict(list)

    def importTweetsFromJSONFiles(self,*files):
        for f in files:
            for line in open(f):
                line = line.strip()
                j = json.loads(line)

                # if has a location:
                if j["geo"] == None:
                    # we only include located data in this dataset
                    continue
                
                ti = TweetInfo(j)
                
                self.tweets[ti.id] = ti
                self.user_infos[ti.user.id] = ti.user
                ut = None

                if ti.user.id in self.user_tweets_by_user_id:
                    ut = self.user_tweets_by_user_id[ti.user.id]
                else:
                    ut = UserTweets(ti.user.id)

                ut.addTweet(ti)

                self.user_tweets_by_user_id[ti.user.id] = ut

                if ti.place is not None:
                    self.places[ti.place.id] = ti.place
                self.coords.append(ti.geo)
                
                self.tweet_id_by_user_id[ti.user.id].append(ti.id)
                self.user_id_by_tweet_id[ti.id].append(ti.user.id)
                if ti.place is not None:
                    self.place_id_by_tweet_id[ti.id].append(ti.place.id)
                    self.tweet_id_by_place_id[ti.place.id].append(ti.id)
                    
    def addTokenizations(self,tknizd_tweets_dict):
        for tweet_id,tokenization in tknizd_tweets_dict.iteritems():
            self.tweets[tweet_id].addTokenization(tokenization)

    def setHomePerUser(self,home_regions,lmbda=15):
        user_homes_file = "user_homes.%s.out" % self.md5

        user_regions = {}

        loaded_from_file = False
        
        if os.path.isfile(user_homes_file):
            sys.stdout.write("Loading data from %s...\n" % user_homes_file)
            loaded_from_file = True
            user_regions = pickle.load(open(user_homes_file))

        for user_id,utweets in self.user_tweets_by_user_id.iteritems():
            if loaded_from_file:
                utweets.refineRegions(lmbda=lmbda,user_regions=user_regions[user_id])
            else:
                utweets.refineRegions(lmbda=lmbda)
                user_regions[user_id] = utweets._user_regions
            utweets.defineUserHome(home_regions)

        if loaded_from_file is False:
            pickle.dump(user_regions,open(user_homes_file,"w+"))
        

    def segmentUserTweets(self,daytrip_variance_threshold=15):
        # TODO daytrip_variance_threshold isn't being used yet; need to implement this
        
        for user_id,utweets in self.user_tweets_by_user_id.iteritems():
            utweets.segmentTweets()
            
    def detectUserAwayPeriods(self):
        for user_id,utweets in self.user_tweets_by_user_id.iteritems():
            utweets.detectAwayPeriods()

    def annotateBeforeAway(self,stability_thres=7):
        for user_id,utweets in self.user_tweets_by_user_id.iteritems():
            utweets.annotateSegments(stability_thres=stability_thres)
    
    def getTweet(self,tID):
        return tweets[tID]
