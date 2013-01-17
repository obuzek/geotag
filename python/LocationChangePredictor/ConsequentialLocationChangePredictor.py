from __future__ import division

import Config
import GeoTweetDataset
from Util import md5filehash 
from GeoTweetDataset.Regions import HomeRegions
import os, hashlib
from collections import defaultdict, Counter

import argparse, sys, random, math, codecs
import pickle, datetime
from svmutil import *

class ConsequentialLocationChangePredictor:

    def generate_ngrams(self,tweet):

        tkns = tweet.split(" ")

        grams = []

        for n in range(NGRAMS):
            for i,tkn in enumerate(tkns):
                grams.append(" ".join(tkns[i:i+n+1]))
                
        return grams

    def convert_to_svm(self,user_list,make_even_training=False):
        
        y = []
        x = []

        total_before = 0
        total_away = 0
        total_stable_home = 0

        ind_with_away = []

        for user_id in user_list:

            user_tweets = self.gtd.user_tweets_by_user_id[user_id]
            
            for tweet_id,tweet_info in user_tweets._tweets.iteritems():
                ngrams = self.generate_ngrams(tweet_info.tweet)
                featurized = dict([(self.v.get_vocab_num(ftr),val)
                                   for ftr,val 
                                   in Counter(ngrams).iteritems()])
                
                tweet_class = None
                if tweet_info.BEFORE is not None:
                    tweet_class = 1
                    total_before += 1
                elif tweet_info.AWAY is not None:
                    tweet_class = 2
                    ind_with_away.append(total_away)
                    total_away += 1
                else:
                    tweet_class = 3
                    total_stable_home += 1

                y.append(tweet_class)
                x.append(featurized)

        random.seed(238572)        

        inds_to_remove = []

        if make_even_training:
            num_to_remove = total_away - total_before
            sys.stdout.write("Removing enough aways to match before for training...\n")
            
            for i in range(num_to_remove):
                ind_ind = random.randint(0,len(ind_with_away)-1)
                inds_to_remove.append(ind_with_away.pop(ind_ind))

        y = [k for i,k in enumerate(y) if i not in inds_to_remove]
        x = [k for i,k in enumerate(x) if i not in inds_to_remove]
                
        sys.stdout.write("total before: %d\n" % (total_before))
        sys.stdout.write("total away: %d\n" % (total_away))
        sys.stdout.write("total stable home: %d\n" % (total_stable_home))
        return y, x

    def __init__(self,*json_files):
        # setting up: loading data, defining home regions
	
        home_region_out_file = Config.global_out+"/home_regions.%s.pickle"

        md5 = md5filehash(json_files)
        self.md5 = md5
        global_fname = home_region_out_file % md5
        
        gtd_out_file = Config.exp_out+"/geotweets.%s.pickle"
        gtd_fname = gtd_out_file % md5
        
        tweets_tknizd_fname = Config.exp_out+"/tweets.%s.tknizd.out" % md5
        tknizd_tweets = [line.lower().strip().split(" ") for line in open(tweets_tknizd_fname)]
        tknizd_tweets_dict = {}
        prev_tweet_id = None
        for line_arr in tknizd_tweets:
            tweet_id = line_arr[0]
            if tweet_id.isdigit():
                tweet_id_int = int(tweet_id)
                tknizd_tweet = " ".join(line_arr[1:])
                prev_tweet_id = tweet_id_int
                tknizd_tweets_dict[tweet_id_int] = tknizd_tweet
            else:
                tknizd_tweets_dict[prev_tweet_id] += " ".join(line_arr)
        
        self.gtd = None
        oldDataExists = False
	if os.path.isfile(gtd_fname):
            sys.stdout.write("Loading data from %s...\n" % gtd_fname)
	    try:
            	self.gtd = pickle.load(open(gtd_fname))
		oldDataExists=True
	    except ImportError:
                sys.stdout.write("ImportError: This pickle doesn't work with the current GeoTweetDataset version.  Reconstructing...\n")
                sys.stdout.flush()
		pass
        if not oldDataExists:
            sys.stdout.write("Loading data from files.\n")
            self.gtd = GeoTweetDataset.GeoTweetDataset(md5, Config.exp_out)
            for fname in json_files:
                sys.stdout.write("Loading data from %s...\n" % fname)
                self.gtd.importTweetsFromJSONFiles(fname)
            pickle.dump(self.gtd,open(gtd_fname,"w+"))
        
        self.gtd.addTokenizations(tknizd_tweets_dict)
        self.tknizd_tweets_dict = tknizd_tweets_dict

        self.hr = None
        if os.path.exists(global_fname):
            sys.stdout.write("\nLoading home regions from file %s...\n" % global_fname)
            self.hr = pickle.load(open(global_fname))
        else:
            sys.stdout.write("\nPerforming K-means to detect home regions...\n")            
            self.hr = HomeRegions.HomeRegions(self.gtd.tweets,lmbda=HOME_REGION_LMBDA)
            sys.stdout.write("Storing home regions in file %s...\n" % global_fname)
            pickle.dump(self.hr,open(global_fname,"w+"))

        sys.stdout.write("\nAdding ground truth...\n")
        self.autogenGroundTruth()

        sys.stdout.write("\nDivvying up data into train / test / dev splits...\n")
        self.separateData()
        sys.stdout.write(":Training set - %d\n" % len(self.trainset_users))
        sys.stdout.write(":Development set - %d\n" % len(self.devset_users))
        sys.stdout.write(":Test set - %d\n" % len(self.testset_users))

        sys.stdout.write("\nAnnotate some data!\n")
        self.annotate_data()

        sys.stdout.write("\nTraining log-linear discriminative model on annotations...\n")
        self.trainOnAnnotated()

        #sys.stdout.write("\nTraining log-linear discriminative models...\n")
        #self.trainLogLinearBucketModels(STABILITY_THRESHOLD)

        #sys.stdout.write("\nTesting log-linear discriminative models on devset...\n")
        #self.testLogLinearBucketModels(STABILITY_THRESHOLD,self.devset_users)
        
        sys.stdout.write("\nTesting annotated model on devset...\n")
        for k in range(-100,100,5):
            self.testAnnotatedModel(STABILITY_THRESHOLD,self.devset_users,thres=k)

        sys.stdout.write("\nConverting data into SVM format...\n")
        # convert data
        self.v = Vocabulary()
        train_y, train_x = self.convert_to_svm(self.trainset_users,make_even_training=True)
        dev_y, dev_x = self.convert_to_svm(self.devset_users,make_even_training=True)
        test_y, test_x = self.convert_to_svm(self.testset_users,make_even_training=True)

        sys.stdout.write("\nTraining SVM classifier...\n")
        # train
        """
         -t int      -> type of kernel function:
                        0: linear (default)
                        1: polynomial (s a*b+c)^d
                        2: radial basis function exp(-gamma ||a-b||^2)
                        3: sigmoid tanh(s a*b + c)
                        4: user defined kernel from kernel.h
         -c float    -> C: trade-off between training error
                        and margin (default 0.01)
         -b [1..100] -> percentage of training set for which to refresh cache
                        when no epsilon violated constraint can be constructed
                        from current cache (default 100%) (used with -w 4)
        """
        prob  = svm_problem(train_y, train_x)
        param = svm_parameter('-t 0 -c 4 -b 1')
        annotated_svm_model = svm_train(prob, param)
        
        sys.stdout.write("\nTesting SVM classifier on devset...\n")
        # test
        p_label, p_acc, p_val = svm_predict(dev_y, 
                                            dev_x, 
                                            annotated_svm_model,
                                            '-b 1')
        ACC, MSE, SCC = evaluations(dev_y, p_label)
        sys.stdout.write("SVM results:\n")
        sys.stdout.write("Accuracy: %0.3f\n" % ACC)
        sys.stdout.write("MSE: %0.3f\n" % MSE)
        sys.stdout.write("SCC: %0.3f\n" % SCC)


        sys.stdout.write("\nTesting SVM classifier on testset...\n")
        # test
        p_label, p_acc, p_val = svm_predict(test_y, 
                                            test_x, 
                                            annotated_svm_model,
                                            '-b 1')
        ACC, MSE, SCC = evaluations(test_y, p_label)
        sys.stdout.write("SVM results:\n")
        sys.stdout.write("Accuracy: %0.3f\n" % ACC)
        sys.stdout.write("MSE: %0.3f\n" % MSE)
        sys.stdout.write("SCC: %0.3f\n" % SCC)

    def annotate_data(self):
        # getting positive training data that means something
        
        self.data_annotation = defaultdict(dict) # user_id -> tweet_id -> Y / N
        
        data_annotation_out_file = "data_annotation.%s.pickle" % self.md5

        if os.path.isfile(data_annotation_out_file):
            self.data_annotation = pickle.load(open(data_annotation_out_file))

        left_to_annotate = {}
        
        away_users = [u for u in self.trainset_users if len(self.gtd.user_tweets_by_user_id[u].user_away_periods) > 0]
        
        for user_id in away_users:
            ut = self.gtd.user_tweets_by_user_id[user_id]
            if user_id not in self.data_annotation:
                left_to_annotate[user_id] = sorted(ut._tweets.keys(),key=lambda ti:ut._tweets[ti].time)
            if len(self.data_annotation[user_id]) < len(ut._tweets):
                left_to_annotate[user_id] = sorted([tweet_id for tweet_id in ut._tweets.keys() if tweet_id not in self.data_annotation[user_id]],key=lambda ti:ut._tweets[ti].time)

        stdout = codecs.getwriter('utf8')(sys.stdout)
        print_tweet_info=lambda ti:stdout.write(str(ti.geo.latitude)+", "+str(ti.geo.longitude)+"\t"+str(ti.timeString())+"\t"+ti.tweet+"\n")

        for user_id in left_to_annotate:

            ut = self.gtd.user_tweets_by_user_id[user_id]
            finished_annotations = []
            stop_after_user = False

            for tweet_id in left_to_annotate[user_id]:
                res = None
                tweet_info = ut._tweets[tweet_id]
                while res is None:
                    print_tweet_info(tweet_info)
                    res = sys.stdin.readline().strip().upper()
                    if res == "Y" or res == "N":
                        self.data_annotation[user_id][tweet_id] = res
                        finished_annotations.append(tweet_id)
                    elif res == "Q":
                        sys.stdout.write("Q = quit. Ending annotation process.\n")
                        stop_after_user = True
                    else:
                        sys.stdout.write("ERR: Bad input.  Must enter Y / N / Q.\n")
                        res = None
                        
                if stop_after_user:
                    break

            if len(finished_annotations) > 0:
                for tweet_id in finished_annotations:
                    left_to_annotate[user_id].remove(tweet_id)

            if stop_after_user:
                break
        ####################
        
        # save those annotations to a file so we can continue where we left off!
        pickle.dump(self.data_annotation,open(data_annotation_out_file,"w+"))

    def trainOnAnnotated(self):
        self.loglin_annotated = LogLinearModel("annotations")

        total_in_loglin = 0
        total_annotated = 0
        for user_id in self.data_annotation:
            for tweet_id in self.data_annotation[user_id]:
                total_annotated += 1
                if self.data_annotation[user_id][tweet_id] == "Y":
                    # include tweet in the model
                    total_in_loglin += 1
                    ngrams = self.loglin_annotated.generate_ngrams(self.tknizd_tweets_dict[tweet_id])
                    self.loglin_annotated.add(ngrams)

        self.loglin_annotated.normalize_counts()
        self.prob_yes_in_before = total_in_loglin / total_annotated

        
    def trainLogLinearBucketModels(self,stability_thres=7):
        
        self.loglin = {}
        self.loglin_stablehome = LogLinearModel("home")
        
        self.before_prob = defaultdict(float)
        self.stablehome_prob = 0

        self.total_tweets = 0
        
        for i in range(stability_thres+1):
            self.loglin[i] = LogLinearModel(i)

        for user_id in self.trainset_users:

            user_tweets = self.gtd.user_tweets_by_user_id[user_id]

            tweet_dict = user_tweets._tweets
            
            for tweet_id in tweet_dict:
                
                tweet_info = tweet_dict[tweet_id]
            
                ngrams = self.loglin_stablehome.generate_ngrams(self.tknizd_tweets_dict[tweet_id])

                if tweet_info.STABLE_HOME is True:
                    self.stablehome_prob += 1
                    self.loglin_stablehome.add(ngrams)

                if tweet_info.BEFORE is not None:
                    self.before_prob[tweet_info.BEFORE] += 1
                    self.loglin[tweet_info.BEFORE].add(ngrams)
                    
                self.total_tweets += 1
        
        print self.stablehome_prob
        print self.total_tweets
        for i in range(stability_thres+1):
            self.loglin[i].normalize_counts()
            if self.before_prob[i] != 0:
                self.before_prob[i] = math.log(self.before_prob[i] / self.total_tweets)
            else:
                self.before_prob[i] = 0
        self.loglin_stablehome.normalize_counts()
        self.stablehome_prob = math.log(self.stablehome_prob / self.total_tweets)

#        self.testLogLinearBucketModels(STABILITY_THRESHOLD,self.devset_users)

    def testLogLinearBucketModels(self,stability,users):

        total_correct = 0
        total_tested = 0
        total_signal_correct = 0
        total_signal = 0

        for user_id in users:

            user_tweets = self.gtd.user_tweets_by_user_id[user_id]

            tweet_dict = user_tweets._tweets
            
            for tweet_id in tweet_dict:

                tweet_info = tweet_dict[tweet_id]

                ngrams = self.loglin_stablehome.generate_ngrams(self.tknizd_tweets_dict[tweet_id])

                #print tweet_info.BEFORE, tweet_info.STABLE_HOME, tweet_info.AWAY
                #print tweet_info.tweet
                impending_travel_prob = 0
                for i in range(stability+1):
                    p = self.loglin[i].evaluate_prob(ngrams) + self.before_prob[i]
                    impending_travel_prob += p
                stable_prob = self.loglin_stablehome.evaluate_prob(ngrams) + self.stablehome_prob

                if impending_travel_prob > stable_prob:
                    tweet_info.predictTravel()
                else:
                    tweet_info.predictStability()

                if tweet_info.CORRECT:
                    total_correct += 1
                total_tested += 1

                if tweet_info.CORRECT and tweet_info.BEFORE is not None:
                    total_signal_correct += 1
                if tweet_info.BEFORE is not None:
                    total_signal += 1
                #print "STABLE: "+str(p)


        sys.stdout.write("Accuracy overall: %0.1f (%d / %d)\n" % (total_correct / total_tested,
                                                                total_correct,
                                                                total_tested))

        sys.stdout.write("Accuracy for signal: %0.1f (%d / %d)\n" % (total_signal_correct / total_signal,
                                                                total_signal_correct,
                                                                total_signal))

    def testAnnotatedModel(self,stability,users,thres=0):

        total_correct = 0
        total_tested = 0
        total_signal_correct = 0
        total_signal = 0

        for user_id in users:

            user_tweets = self.gtd.user_tweets_by_user_id[user_id]

            tweet_dict = user_tweets._tweets
            
            for tweet_id in tweet_dict:

                tweet_info = tweet_dict[tweet_id]

                ngrams = self.loglin_annotated.generate_ngrams(self.tknizd_tweets_dict[tweet_id])

                impending_travel_prob = 0
                p = self.loglin_annotated.evaluate_prob(ngrams)

                if p > thres:
                    tweet_info.predictTravel()
                else:
                    tweet_info.predictStability()

                if tweet_info.CORRECT:
                    total_correct += 1
                total_tested += 1

                if tweet_info.CORRECT and tweet_info.BEFORE is not None and tweet_info.AWAY is not None:
                    total_signal_correct += 1
                if tweet_info.BEFORE is not None and tweet_info.AWAY is not None:
                    total_signal += 1
                #print "STABLE: "+str(p)

        sys.stdout.write("thres=%d\n" % thres)
        sys.stdout.write("Accuracy overall: %0.1f (%d / %d)\n" % (total_correct / total_tested,
                                                                total_correct,
                                                                total_tested))

        sys.stdout.write("Accuracy for signal: %0.1f (%d / %d)\n" % (total_signal_correct / total_signal,
                                                                total_signal_correct,
                                                                total_signal))
    
    def autogenGroundTruth(self):
        sys.stdout.write(":Setting user homes.\n")
        self.gtd.setHomePerUser(self.hr,lmbda=USER_REGION_LMBDA)
        
        sys.stdout.write(":Generate segmentation for user tweets.\n")
        self.gtd.segmentUserTweets(daytrip_variance_threshold=DAYTRIP_VARIANCE_THRES)

        sys.stdout.write(":Detecting periods of extended away length.\n")
        self.gtd.detectUserAwayPeriods()

        sys.stdout.write(":Annotating BEFORE and STABLE_HOME periods.\n")
        self.gtd.annotateBeforeAway(stability_thres=STABILITY_THRESHOLD)
        
    def separateData(self):

        RANDOM_SEED = 167362
        random.seed(RANDOM_SEED)

        data_split = (.80,.10,.10)
        
        self.trainset_users = []
        self.devset_users = []
        self.testset_users = []
        
        user_ids = self.gtd.user_infos.keys()
        num_users = len(user_ids)
        
        training_total = int(math.ceil(data_split[0] * num_users))

        for i in range(training_total):
            k = random.randint(0,len(user_ids)-1)
            self.trainset_users.append(user_ids.pop(k))
        
        users_left = num_users - training_total

        dev_total = int(math.ceil((data_split[1] / (data_split[1] + data_split[2])) * users_left))

        for i in range(dev_total):
            k = random.randint(0,len(user_ids)-1)
            self.devset_users.append(user_ids.pop(k))

        testset_users = users_left - dev_total

        self.testset_users = user_ids
