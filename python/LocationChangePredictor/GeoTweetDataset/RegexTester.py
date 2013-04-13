# depends on GeoTweetDataset and Tweets.*
import hashlib, copy, random, pickle, sys, os, codecs, re
from collections import defaultdict
from .. import Config

class Log:

    def __init__(self,log_file):
        self.f = codecs.getwriter('utf8')(open(log_file,"a"))
        self.stdout = codecs.getwriter('utf8')(sys.stdout) 

    def log(self,string,printout=True):
        if printout:
            self.stdout.write(string)
            self.stdout.flush()
        self.f.write(string)
        self.f.flush()

    def log_prompt(self,prompt):
        self.log(prompt)
        res = sys.stdin.readline().strip().upper()
        self.log(res+"\n")
        return res
    
    def close_log(self):
        self.f.close()


class RegexTester:
        
    def __init__(self,gtd,regex_file):

        # MAGIC NUMBERS
        PREC_AT_NUM = 50

        regexes = {}
        for line in open(regex_file):
            print line
            line_arr = line.strip().split("\t")
            id,phrase,regex = line_arr
            regexes[id] = regex
        
        self.md5 = self.md5filehash(regexes.values())

        folder = os.path.realpath(Config.exp_out+"/annotations")
    
        if not os.path.isdir(folder):
            os.mkdir(folder)

        # CREATE A COPY OF THE INPUT FILE
        input_file_copy = folder+("/regex_input.%s.txt" % self.md5)
        if not os.path.isfile(folder+("/regex_input.%s.txt" % self.md5)):
            # create a copy of the actual input file
            in_copy = open(input_file_copy,"w+")
            
            for regex_id in sorted(regexes.keys()):
                in_copy.write("%s\t%s\n" % (regex_id,regexes[regex_id]))
            
            in_copy.close()
        
        # RESTORE FROM SAVE
        
        # data structure for saving:
        # { regex_id ->
        #        { all_users : [UIDs],
        #          test_users : [UIDs],
        #          annot : { UID -> Y/N } }
        
        regex_struct = lambda: {"all_users": [],"test_users":[],"annot":{},"total":0}

        self.annotations = {}
        
        save_file = folder + "/regex_annot_save.%s.pickle" % self.md5

        if os.path.isfile(save_file):
            self.annotations = pickle.load(open(save_file))

        # ANNOTATE

        print_tweet_info=lambda ti,rtweet:u"\t".join([unicode(x) for x in [ti.geo.latitude,
                                                                            ti.geo.longitude,
                                                                            ti.dateString(),
                                                                            rtweet]])+u"\n"
        stop_after_user = False
        
        regex_log_folder = folder + ("/user_session_logs.%s.out" % self.md5)
        if not os.path.isdir(regex_log_folder):
            os.mkdir(regex_log_folder)

        for regex_id in sorted(regexes.keys()):
            l = Log(regex_log_folder + ("/regex_%s.txt" % regex_id))
            regex = regexes[regex_id]

            if regex_id not in self.annotations:
                self.annotations[regex_id] = regex_struct()
                # LOAD POSSIBLE USERS

                # apply_regex should return a list of tuples, pairing:
                #              (UID, dict of tweet_ids -> recolored tweet)
                for user_id,tweet_idx in gtd.apply_regex(regex): 
                    self.annotations[regex_id]["all_users"].append(user_id)
                
                all = copy.copy(self.annotations[regex_id]["all_users"])
                self.annotations[regex_id]["total"] = len(all)

                for i in range(PREC_AT_NUM):
                    if len(all) is 0:
                        break
                    
                    idx = random.randint(0,len(all)-1)
                    self.annotations[regex_id]["test_users"].append(all.pop(idx))
            
            # APPLY ANNOTATIONS TO USERS

            annot = self.annotations[regex_id]["annot"]

            if len(annot) == len(self.annotations[regex_id]["test_users"]):
               continue # this means that it's just been loaded and determined to be done

            for uid in self.annotations[regex_id]["test_users"]:
                if uid not in annot:
                    # annotate it
                    res = None
                    while res is None:
                        ut = gtd.getUserTweetsByUserID(uid)
                        l.log("="*80+"\n")
                        for tweet_id in ut.tweetIDiter():
                                tweet_info = gtd.getTweet(tweet_id)
                                l.log(print_tweet_info(tweet_info,tweet_info.apply_regex(regex)))
                        res = l.log_prompt("")
                        if res == "Y" or res == "N":
                            annot[uid] = res
                        elif res == "Q":
                            l.log("Q = quit. Ending annotation process.\n")
                            stop_after_user = True
                        else:
                            l.log("ERR: Bad input.  Must enter Y / N / Q.\n")
                            res = None
                        
                if stop_after_user:
                    break # out of the "annotate this UID's tweet" loop

            l.close_log()

            if stop_after_user:
                break # out of the "finish this regex" loop

        # out of both the UID and regex loops; now it's necessary to:
        #   - pickle the annotations
        #   - output all the current prec@50's to a file
        
        pickle.dump(self.annotations,open(save_file,"w+"))
        
        l = Log(folder + ("/regex_out.%s" % self.md5))
        for regex_id in sorted(self.annotations.keys()):
            if "total" in self.annotations[regex_id]:
                l.log("%s\t%d / %d (%d found in corpus)\n" % (regex_id,
                                     sum([1 for x,y in self.annotations[regex_id]["annot"].iteritems() if y == "Y"]),
                                     len(self.annotations[regex_id]["test_users"]),
                                     self.annotations[regex_id]["total"]))
            else:
                l.log("%s\t%d / %d (?? found in corpus)\n" % (regex_id,
                                     sum([1 for x,y in self.annotations[regex_id]["annot"].iteritems() if y == "Y"]),
                                     len(self.annotations[regex_id]["test_users"])))
        l.close_log()
   
    def md5filehash(self,regexes):
        m = hashlib.md5()
        for f in sorted(regexes):
            m.update(f)
        return m.hexdigest()

    def regex_test(self,regex_file):
        pass

        # ALGORITHM
        # have some way of saving this process; it's going to take a long time and will be seriously frustrating
        # if we have to redo it 
        
        # open file, extract regular expressions and their corresponding regex_id

        # for every regular expression:
            # apply to every user's tweets
            # retain all users that fired on that regex
            # choose 50 random users for which the regex fired
            # retain answers while:
                # for every one of the 50 chosen users, display their tweets,
                # including the regex'd tweet (retain coloration in data structure)
            # at the end of the 50, report the precision

        # make sure you can save at ANY POINT in this process!

def test_regex(gtd,regex):
    pass


