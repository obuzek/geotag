#!/usr/bin/env python

import json, sys, os, subprocess, hashlib, re, codecs
from LocationChangePredictor.Util import md5filehash

stdout = codecs.getwriter('utf8')(sys.stdout)

def strip_tweet_of_line_breaks(tweet):
    tweet = ' '.join(tweet.splitlines())
    return re.sub(r"(?<=[a-z])\r?\n"," ", tweet)

files = sys.argv[1:]

md5 = md5filehash(files)

out_loc = os.environ["GEO_PROJ_LOC"]+"/cache"
out_fname = "tweets.%s.out" % md5
tknizd_out_fname = "tweets.%s.tknizd.out" % md5

out_fname = out_loc+"/"+out_fname
tknizd_out_fname = out_loc+"/"+tknizd_out_fname

if not os.path.isfile(out_fname):
    out_f = open(out_fname,"w+")
    out_f = codecs.getwriter('utf8')(out_f)

    for f in files:
        for line in open(f):
           j = json.loads(line.strip())
           out_f.write("%d\t%s\n" % ( j[u'id'],
                                    strip_tweet_of_line_breaks(j[u'text'])))
        out_f.flush()

    out_f.close()

sys.stdout.write("Dumping columns to separate files\n")
cmd = "cut -f1 %s > /tmp/tmp.tweetIDs.1" % out_fname 
sys.stdout.write(cmd)
os.system(cmd)
cmd = "cut -f2 %s > /tmp/tmp.tweets.2" % out_fname
sys.stdout.write(cmd)
os.system(cmd)
sys.stdout.write("Tokenizing...\n")
cmd = """java -cp $JERBOA_ROOT/dist/jerboa.jar -DTwitterTokenizer.unicode=$JERBOA_ROOT/proj/tokenize/unicode.csv \
          edu.jhu.jerboa.processing.TwitterTokenizer < /tmp/tmp.tweets.2 > /tmp/tmp.tweets.3"""
sys.stdout.write(cmd)
os.system(cmd)
sys.stdout.write("Pasting back together...\n")
subprocess.call(["paste","/tmp/tmp.tweetIDs.1","/tmp/tmp.tweets.3"], stdout=open(tknizd_out_fname,"w+"))
sys.stdout.write("Done.\n")

