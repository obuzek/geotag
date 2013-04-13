from Tweets import TweetInfo, UserTweets
from collections import defaultdict
from Data import Place, User
import json, sys, os, pickle, re

import rebar2

class GeoTweetDataset:

    def __init__(self,md5,
                 exp_out):
        self.md5 = md5
        self.exp_out = exp_out
        
        self.tweets = {}
        self.user_infos = {}
        self.places = {}
        self.coords = []
        
        self.user_tweets_by_user_id = {}
        self.tweet_id_by_user_id = defaultdict(list)
        self.user_id_by_tweet_id = defaultdict(list)
        self.place_id_by_tweet_id = defaultdict(list)
        self.tweet_id_by_place_id = defaultdict(list)

    def apply_regex(self,regex):
        # apply_regex should return a list of tuples, pairing:
        #              (UID, dict of tweet_ids -> recolored tweet)
        
        for uid,ut in self.user_tweets_by_user_id.iteritems():
            recolored = {}
            for tweet_id in ut.tweetIDiter():
                ti = ut.getTweet(tweet_id)
                m = re.search(regex,ti.tweet)
                if m is not None:
                    recolored[tweet_id] = ti.apply_regex(regex)
                                
            if len(recolored) != 0:
                yield uid,recolored

    def importTweetsFromRebar(self,corpus_name,src_stage,version):
        corpus = rebar2.corpus.Corpus.get_corpus(corpus_name)
        #src_ver = corpus.get_stage_versions(src_stage)[-1]

        reader = corpus.make_reader(src_stage)
        communications = reader.load_communications()
        num_communications = corpus.get_num_communications()
        sys.stdout.write('Found %d communications.\n' % (num_communications))
	
        #print '\n'.join(out)
        for communication in communications:
    	    sys.stdout.write('------------------------------------------------------------------\n')
            sys.stdout.write(communication.__str__())
            break

        corpus.close()

    def importTokenizationFromRebar(self,corpus,stage,version):
        pass    

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

    def getUsers(self):
        return self.user_tweets_by_user_id.keys()
                    
    def getUserTweetsByUserID(self,user_id):
        return self.user_tweets_by_user_id[user_id]
    
    def addTokenizations(self,tknizd_tweets_dict):
        for tweet_id,tokenization in tknizd_tweets_dict.iteritems():
            if tweet_id in self.tweets:
                self.tweets[tweet_id].addTokenization(tokenization)

    def setHomePerUser(self,home_regions,lmbda=15):
        user_homes_file = self.exp_out+"/user_homes.%s.out" % self.md5

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
        return self.tweets[tID]
    
