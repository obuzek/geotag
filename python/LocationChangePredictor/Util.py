##!/usr/bin/env python

import Config
import os, sys, subprocess

#wd="/export/projects/tto8/CommunicantAttributes/data/data_ob"
#jerboa=wd+"/geotag/3rd/jerboa"

class TwitterTokenizerWrapper:
    
    def __init__(self):
        pass
    
    def tokenizeFile(self,file,md5):
        JERBOA_ROOT = os.environ["JERBOA_ROOT"]
        #Config.exp_out+"/tweets.%s.tknizd.out" % md5

       tweets_file = Config.exp_out+"/tweets.%s.tknizd.out" % md5
 
        if os.path.isfile(file):
            Popen("java -cp %s/java/src -DTwitterTokenizer.unicode=proj/tokenize/unicode.csv edu.jhu.jerboa.processing.TwitterTokenizer < %s > %s" %
                        (JERBOA_ROOT,
                         file,
                         tweets_file))


# java -cp java/src -DTwitterTokenizer.unicode=proj/tokenize/unicode.csv edu.jhu.jerboa.processing.TwitterTokenizer < file


def md5filehash(self,json_files):
    m = hashlib.md5()
    for f in sorted(json_files):
        m.update(f)
    return m.hexdigest()
    

"""
annotation=lambda fn:sys.stdin.readline().strip()
tweet_info_wdata=lambda ti:sys.stdout.write(str(ti.geo.latitude)+", "+str(ti.geo.longitude)+"\t"+"\t"+str(ti.timeString())+"\t"+ti.tweet+"\n")
tweet_info=lambda ti:sys.stdout.write(str(ti.geo.latitude)+", "+str(ti.geo.longitude)+"\t"+str(ti.timeString())+"\t"+ti.tweet+"\n")
print_user_tweets=lambda num:[[annotation(tweet_info(ti))+"\t"+ti.tweet+"\n")) for ti in ts.tweets] for ts in clcp.gtd.user_tweets_by_user_id[num].time_segmented_tweets]

# list user_away_periods and user_id for things in the trainset
[(u,clcp.gtd.user_tweets_by_user_id[u].user_away_periods) for u in clcp.trainset_users[50:100]]

users_with_location_changes=[u for u in clcp.trainset_users if len(clcp.gtd.user_tweets_by_user_id[u].user_away_periods) > 0]
"""
