#!/usr/bin/env python

#USERNAME    TWEET_ID                   PLACE_ID                WKID      DIST           TIME    LABEL   DATE                             LAT             LONG          TWEET
#111045208       169183324248604672      8f9664a8ccd89e5c        WKID_2  1171.581 mi     3 days  DURING  Mon Feb 13 22:17:02 +0000 2012  43.65697078     -79.36439971    I'm in a new York state of mind.

from collections import namedtuple, defaultdict
import sys
import math

LineData = namedtuple("LineData",['username',
                                  'tweet_id',
                                  'place_id',
                                  'wkid',
                                  'dist',
                                  'time',
                                  'label',
                                  'date',
                                  'lat',
                                  'long',
                                  'tweet'])

TOP_FEATURES = 50
NGRAMS = 3

data = [LineData(*(line.strip().split("\t"))) for line in sys.stdin]


def normalize_counts(cd): # turns them all into log-likelihoods!  YAY
    s = math.log(sum(cd.values()))
    
    n = defaultdict(float)

    for key in cd:
        n[key] = math.log(cd[key]) - s

    return n

def top_X(X,res):

    ftrs = res.keys()
    ftrs.sort(key=lambda ftr:res[ftr])

    top = [(ftr,res[ftr]) for ftr in ftrs[-X:]]
    top.reverse()

    return top

def bottom_X(X,res):
    ftrs = res.keys()
    ftrs.sort(key=lambda ftr:res[ftr])

    return [(ftr,res[ftr]) for ftr in ftrs[:X]]

def top_X_w_log_likelihood_ratios(X,null,alt):
    
    res = defaultdict(float)

    for key in alt:
        if key in null:
            res[key] = -2*null[key] + 2*alt[key]

    return top_X(X,res)

def print_top_ftrs(ftr_res):
    sys.stdout.write("FTR\tD\n")
    
    for ftr,res in ftr_res:
        sys.stdout.write("%s\t%0.3f\n" % (ftr,res))

    sys.stdout.write("\n")
    sys.stdout.flush()

def generate_ngrams(tkns):

    grams = []

    for n in range(NGRAMS):
        for i,tkn in enumerate(tkns):
            grams.append(" ".join(tkns[i:i+n+1]))

    return grams

def preprocess_tweet(tweet):
    
    tkns = tweet.split(" ")

    for i,tkn in enumerate(tkns):
        if tkn[0] == '@':
            tkns[i] = "@USERNAME"
        
        if tkn[:5] == "http:":
            tkns[i] = "http://URL/"

    return tkns

def combine_counts(cl):
    
    totals = defaultdict(int)
    
    for cd in cl:
        for key in cd:
            totals[key] += cd[key]

    return totals

def predictions(before,after,during,stable):

    max_ctr = 30
    ctr = 0

    correct = defaultdict(int)
    missed = defaultdict(int)
    actual = defaultdict(int)

    errors = {}
    
    s = ["BEFORE","AFTER","DURING","STABLE"]

    for st in s:
        correct[st] = 0
        missed[st] = 0
        actual[st] = 0
        errors[st] = {}
        for st2 in s:
            errors[st][st2] = 0
    
    for d in data:

        tkns = preprocess_tweet(d.tweet)

        ngram_list = generate_ngrams(tkns)

        total_prob = defaultdict(float)

        for tkn in ngram_list:
            
            probs = {"BEFORE" : before[tkn],
                     "AFTER" : after[tkn],
                     "DURING" : during[tkn],
                     "STABLE" : stable[tkn]}

            for key in probs:
                total_prob[key] += probs[key]
        
#        print total_prob

        pred_lbl = max(total_prob,key=total_prob.get)

        actual[d.label] += 1
#        print "actual: %s predicted: %s" % (d.label,pred_lbl)
        if d.label == pred_lbl:
            correct[d.label] += 1
        else:
            missed[d.label] += 1
            errors[d.label][pred_lbl] += 1
            if True:# ctr < max_ctr:
                print "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (d.label,pred_lbl,d.time,
                                                  d.username,
                                                  d.date,
                                                  d.lat,
                                                  d.long,
                                                  d.tweet)
            ctr += 1
            
    print actual
    print correct
    print missed
    print errors

    print "Across: predicted label"
    print "Down: actual label"
    print "\t".join([' ']+s)
    for st in s:
        sys.stdout.write(st+"\t")
        for st2 in s:
            sys.stdout.write(str(errors[st2][st])+"\t")
        sys.stdout.write("\n")

    for key in correct:
        p = correct[key] / (actual[key]*1.0)
        sys.stdout.write("%s: P - %0.2f\n" % (key,p))
            
    

before_counts = defaultdict(int)
after_counts = defaultdict(int)
during_counts = defaultdict(int)

stable_counts = defaultdict(int) # null / stable model

for d in data:
    
    tkns = preprocess_tweet(d.tweet)

    ngram_list = generate_ngrams(tkns)
    
    for tkn in ngram_list:

        if d.label == "BEFORE":
            before_counts[tkn] += 1
        if d.label == "AFTER":
            after_counts[tkn] += 1
        if d.label == "DURING":
            during_counts[tkn] += 1
        if d.label == "STABLE":
            stable_counts[tkn] += 1

before = normalize_counts(before_counts)
after = normalize_counts(after_counts)
during = normalize_counts(during_counts)
stable = normalize_counts(stable_counts)

unstable = normalize_counts(combine_counts([before_counts,
                                            after_counts,
                                            during_counts]))

lvl = TOP_FEATURES

print "====BEFORE===="
print_top_ftrs(top_X_w_log_likelihood_ratios(lvl,stable,before))
print "====DURING===="
print_top_ftrs(top_X_w_log_likelihood_ratios(lvl,stable,during))
print "====AFTER===="
print_top_ftrs(top_X_w_log_likelihood_ratios(lvl,stable,after))


print ""
print "==========================="
print "====STABLE===="
print_top_ftrs(top_X_w_log_likelihood_ratios(lvl,unstable,stable))
print "====UNSTABLE===="
print_top_ftrs(top_X_w_log_likelihood_ratios(lvl,stable,unstable))

predictions(before,after,during,stable)
