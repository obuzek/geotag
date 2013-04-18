from __future__ import division
from collections import defaultdict
import sys, copy, math
from LocationChangePredictor.GeoTweetDataset.Regions.Data import Coordinates
import random

class ScheduleEstimator:

    def __init__(self,gtd):
        # define canonical schedule vectors
        self.work_vec = self._generate_canon_sched_vector([(9,11),(13,18)],["M","Tu","W","Th","F"])
        home_vec = self._generate_canon_sched_vector([(21,23),(0,8)],["M","Tu","W","Th","F","Sa","Su"])
        home_vec_wkd = self._generate_canon_sched_vector([(9,14)],["Sa","Su"])
        self.home_vec = self._or_vectors(home_vec,home_vec_wkd)
        self.travel_vec = self._generate_canon_sched_vector([(0,23)],["F","Sa","Su","M"])
        local_vec_evening = self._generate_canon_sched_vector([(18,23)],["M","Tu","W","Th","F"])
        local_vec_wkd = self._generate_canon_sched_vector([(15,23)],["Sa","Su"])
        self.local_vec = self._or_vectors(local_vec_evening,local_vec_wkd)

        self.work_vec = self._add_lambda(self.work_vec)
        self.home_vec = self._add_lambda(self.home_vec)
        self.local_vec = self._add_lambda(self.local_vec)
        self.travel_vec = self._add_lambda(self.travel_vec)

        priors = { "home" : .3,
                  "work" : .3,
                  "local" : .2,
                  "travel" : .2 }

        timesteps = range(7*24)
        self.renormalize(timesteps,priors)

        print "CANONICAL"
        print "---------"
        print "WORK"
        self._print_vector(self.work_vec)
        print "HOME"
        self._print_vector(self.home_vec)
        print "TRAVEL"
        self._print_vector(self.travel_vec)
        print "LOCAL"
        self._print_vector(self.local_vec)

        random.seed(12)

        self.gtd = gtd # this ScheduleEstimator is going to collect data for a specific dataset

    def _add_lambda(self,vec,lmbda=0.1):
        # res = range(len(vec))
        for pos in range(len(vec)):
            vec[pos] = vec[pos] + lmbda
        return vec

    def renormalize(self,timesteps,priors=defaultdict(lambda:.25),home=None,work=None,local=None,travel=None,lmbda=0.1):
        # timesteps tells you which timesteps to normalize
        if home is None:
            home = self.home_vec
        if work is None:
            work = self.work_vec
        if local is None:
            local = self.local_vec
        if travel is None:
            travel = self.travel_vec

        for i in timesteps:

            home[i] += lmbda
            work[i] += lmbda
            travel[i] += lmbda
            local[i] += lmbda

            total = 0.
            if home[i] > 0:
                home[i] *= priors["home"]
                total += home[i]
            if work[i] > 0:
                work[i] *= priors["work"]
                total += work[i]
            if travel[i] > 0:
                travel[i] *= priors["travel"]
                total += travel[i]
            if local[i] > 0:
                local[i] *= priors["local"]
                total += local[i]

            if total > 0:
                home[i] =   home[i]  / total
                work[i] =   work[i]  / total
                local[i] =  local[i]  / total
                travel[i] = travel[i]  / total

    def _print_vector(self,vec):
        for t in range(0,24):
            for d in range(0,7):
                sys.stdout.write("%0.3f" % (vec[d*24+t])+"\t")
            sys.stdout.write("\n")

    def _add_vecs(self,vecs,timesteps,weights=None):
        if weights is None:
            weights = [1 / len(vecs)]*len(vecs)
        if len(weights) != len(vecs):
            pass # maybe should throw an incorrect length exception, or something

        vec = [0]*len(vecs[0])
        for num in range(len(vecs)):
#             print vecs[num][:10]
            for i in range(len(vecs[0])):
                if i in timesteps:
                    vec[i] += vecs[num][i]*weights[num]
                else:
                    vec[i] += vecs[num][i]

        return vec

    def _or_vectors(self,vec1,vec2):
        vec = [0]*7*24
        for i in range(len(vec1)):
            if vec1[i] == 1 or vec2[i] == 1:
                vec[i] = 1

        return vec

    def _generate_canon_sched_vector(self,times,days):
        # EX:
        #   times: tuples with elapsed hours, 0-23
        #         [(9,11),(13,18)]
        #   days = ['M','Tu','W','Th','F','Sa','Su']
        #   wkday = dict([[i,days[i]] for i in range(7)])
        #   days: list of day labels from the days list above
        poss_days = ['M','Tu','W','Th','F','Sa','Su']
        wkday = dict((poss_days[i],i) for i in range(7))
        
        sched_vector = [0]*7*24 # has something for every hour and day

        for day in days:
            weekday = wkday[day]
            offset = weekday*24
            for start_time,end_time in times:
                if start_time < end_time:
                    for i in range(start_time,end_time+1):
                        sched_vector[offset+i] = 1
        return sched_vector

    def predict_schedules(self,iterations):
        self.initialize_schedules()

        for i in range(iterations):
            self.compute_schedules()
            self.compute_location_types()

        for user_id in self.gtd.getUsers():
            ut = self.gtd.getUserTweetsByUserID(user_id)
            sys.stdout.write("-"*80+"\n")
            sys.stdout.write("USER_ID: "+str(user_id)+"\t"+str(len(ut._tweets))+"\n")
            sys.stdout.write("-------\n")
            sys.stdout.write("HOME\n")
            self._print_vector(self.curr_home_vec[user_id])
            sys.stdout.write("WORK\n")
            self._print_vector(self.curr_work_vec[user_id])
            sys.stdout.write("LOCAL\n")
            self._print_vector(self.curr_local_vec[user_id])
            sys.stdout.write("TRAVEL\n")
            self._print_vector(self.curr_travel_vec[user_id])

    def initialize_schedules(self):
        self.curr_home_vec = {}  
        self.curr_work_vec = {}  
        self.curr_local_vec = {} 
        self.curr_travel_vec = {}
        
        for user_id in self.gtd.getUsers():
            self.curr_home_vec[user_id] = copy.deepcopy(self.home_vec)   
            self.curr_work_vec[user_id] = copy.deepcopy(self.work_vec)
            self.curr_local_vec[user_id] = copy.deepcopy(self.local_vec)
            self.curr_travel_vec[user_id] = copy.deepcopy(self.travel_vec)

    def where_am_I(self,place_prob,user_id,time,key=None):
        if key is None:
            return max(place_prob,key=lambda k:place_prob.get(k)[time])
        else:
            return max(place_prob,key=key)

    def test_probability_dist(self,*args,**kwargs):
#            print kwargs.get("timesteps")
            for i in kwargs.get("timesteps"):
                s = 0
                for vec in args:
#                    print vec
                    s += vec[i]
                if math.fabs(s - 1.0) > 0.0001:
                    print "ZOMG!" , i, s
                    for vec in args:
                        print vec
                    sys.exit(-1)

    def compute_schedules(self):
        # based on current beliefs about where a person will be at a given time,
        # decide where they are and update schedules
        for user_id in self.gtd.getUsers():
            ut = self.gtd.getUserTweetsByUserID(user_id)

            home_vec = [0]*7*24
            work_vec = [0]*7*24
            local_vec = [0]*7*24
            travel_vec = [0]*7*24

            timesteps_for_normalizing = set()

            for tweet_id in ut.tweetIDiter():
                tweet_info = ut.getTweet(tweet_id)

                t = tweet_info.weekday*24+tweet_info.time[3] 
                place_prob = {"h":self.curr_home_vec[user_id],
                                 "w":self.curr_work_vec[user_id],
                                 "l":self.curr_local_vec[user_id],
                                 "t":self.curr_travel_vec[user_id]}

                where_at_t = self.where_am_I(place_prob,user_id,t)

                if where_at_t == "h":
                    home_vec[t] += 1
                if where_at_t == "w":
                    work_vec[t] += 1
                if where_at_t == "l":
                    local_vec[t] += 1
                if where_at_t == "t":
                    travel_vec[t] += 1

                timesteps_for_normalizing.add(t)
                
            self.renormalize(timesteps_for_normalizing,
                           home=home_vec,
                           work=work_vec,
                           local=local_vec,
                           travel=travel_vec)
            # after this point there should be no problems with the prob dist
#             print "after normalizing:"
            self.test_probability_dist(home_vec,work_vec,local_vec,travel_vec,timesteps=timesteps_for_normalizing)

            # update beliefs about where a person will be at a given time        
#             print "Before adding:"
            self.test_probability_dist(self.curr_home_vec[user_id],
                                      self.curr_work_vec[user_id],
                                      self.curr_local_vec[user_id],
                                      self.curr_travel_vec[user_id],
                                      timesteps=range(7*24))
#             print self.curr_home_vec[user_id][:10]
#             print self.curr_work_vec[user_id][:10]
#             print self.curr_local_vec[user_id][:10]
#             print self.curr_travel_vec[user_id][:10]

           
            weights = [0.1,0.9]
            self.curr_home_vec[user_id] = self._add_vecs([home_vec,self.curr_home_vec[user_id]],timesteps_for_normalizing,weights=weights)
            self.curr_work_vec[user_id] = self._add_vecs([work_vec,self.curr_work_vec[user_id]],timesteps_for_normalizing,weights=weights)
            self.curr_local_vec[user_id] = self._add_vecs([local_vec,self.curr_local_vec[user_id]],timesteps_for_normalizing,weights=weights)
            self.curr_travel_vec[user_id] = self._add_vecs([travel_vec,self.curr_travel_vec[user_id]],timesteps_for_normalizing,weights=weights)
             
#             print "after adding:"
#             print timesteps_for_normalizing
            self.test_probability_dist(self.curr_home_vec[user_id],
                                      self.curr_work_vec[user_id],
                                      self.curr_local_vec[user_id],
                                      self.curr_travel_vec[user_id],
                                      timesteps=range(7*24))


    def compute_location_types(self):
        # based on the average across all the times we predict a person is in a place,
        # decide where someone probably is at a given time
        for user_id in self.gtd.getUsers():
            ut = self.gtd.getUserTweetsByUserID(user_id)

            avg_home = Coordinates(0,0)
            avg_work = Coordinates(0,0)
            avg_local = Coordinates(0,0)
            avg_travel = Coordinates(0,0)
            total_home = 0
            total_work = 0
            total_local = 0
            total_travel = 0

            home_vec = [0]*7*24
            work_vec = [0]*7*24
            local_vec = [0]*7*24
            travel_vec = [0]*7*24


            for tweet_id in ut.tweetIDiter():
                tweet_info = ut.getTweet(tweet_id)

                t = tweet_info.weekday*24+tweet_info.time[3] 

                home_geo = Coordinates(tweet_info.geo.latitude*self.curr_home_vec[user_id][t],
                                       tweet_info.geo.longitude*self.curr_home_vec[user_id][t])
                work_geo = Coordinates(tweet_info.geo.latitude*self.curr_work_vec[user_id][t],
                                       tweet_info.geo.longitude*self.curr_work_vec[user_id][t])
                local_geo = Coordinates(tweet_info.geo.latitude*self.curr_local_vec[user_id][t],
                                       tweet_info.geo.longitude*self.curr_local_vec[user_id][t])
                travel_geo = Coordinates(tweet_info.geo.latitude*self.curr_travel_vec[user_id][t],
                                       tweet_info.geo.longitude*self.curr_travel_vec[user_id][t])
                # if where_at_t == "h":
                avg_home += home_geo
                total_home += self.curr_home_vec[user_id][t]
                # if where_at_t == "w":
                avg_work += work_geo 
                total_work += self.curr_work_vec[user_id][t]
                # if where_at_t == "l":
                avg_local += local_geo 
                total_local += self.curr_local_vec[user_id][t]
                # if where_at_t == "t":
                avg_travel += travel_geo 
                total_travel += self.curr_travel_vec[user_id][t]
           
            if total_home > 0:
                avg_home /= total_home 
            if total_work > 0:
                avg_work /= total_work
            if total_local > 0:
                avg_local /= total_local
            if total_travel > 0:
                avg_travel /= total_travel

            timesteps = set()
            
            for tweet_id in ut.tweetIDiter():
                tweet_info = ut.getTweet(tweet_id)
                place_prob = {"h":tweet_info.geo-avg_home,
                     "w":tweet_info.geo-avg_work,
                     "l":tweet_info.geo-avg_local,
                     "t":tweet_info.geo-avg_travel}
                t = tweet_info.weekday*24+tweet_info.time[3] 

                where_at_t = self.where_am_I(place_prob,user_id,t,key=place_prob.get)

                if where_at_t == "h":
                    home_vec[t] += 1
                if where_at_t == "w":
                    work_vec[t] += 1
                if where_at_t == "l":
                    local_vec[t] += 1
                if where_at_t == "t":
                    travel_vec[t] += 1

                timesteps.add(t)
                
            self.renormalize(timesteps,
                           home=home_vec,
                           work=work_vec,
                           local=local_vec,
                           travel=travel_vec)
            # update beliefs about where a person will be at a given time        
            
            weights = [0.1,0.9]
            self.curr_home_vec[user_id] = self._add_vecs([home_vec,self.curr_home_vec[user_id]],timesteps,weights)
            self.curr_work_vec[user_id] = self._add_vecs([work_vec,self.curr_work_vec[user_id]],timesteps,weights)
            self.curr_local_vec[user_id] = self._add_vecs([local_vec,self.curr_local_vec[user_id]],timesteps,weights)
            self.curr_travel_vec[user_id] = self._add_vecs([travel_vec,self.curr_travel_vec[user_id]],timesteps,weights)
             
    def cluster_schedules(self,k,iterations=100):
        # k-means, with schedules! 
        self.cluster_assignments = dict((user_id,random.randint(0,k-1)) for user_id in self.gtd.getUsers()) # by user ID
        self.home_vec_mean = {} # one per cluster
        self.work_vec_mean = {}
        self.local_vec_mean = {} 
        self.travel_vec_mean = {}

        self.num_clusters = k

        for i in range(iterations):
            self.compute_cluster_means()
            self.compute_user_assignments()

        sys.stdout.write("CLUSTER MEANS\n")
        sys.stdout.write("-"*80+"\n")
        for k in range(self.num_clusters):
            sys.stdout.write("="*10+str(k)+"="*10+"\n")
            sys.stdout.write("HOME\n")
            self._print_vector(self.home_vec_mean[k])
            sys.stdout.write("WORK\n")
            self._print_vector(self.work_vec_mean[k])
            sys.stdout.write("LOCAL\n")
            self._print_vector(self.local_vec_mean[k])
            sys.stdout.write("TRAVEL\n")
            self._print_vector(self.travel_vec_mean[k])

    def compute_cluster_means(self):
        #print self.cluster_assignments
        self.num_users_in_cluster=defaultdict(int)
        for user,cluster in self.cluster_assignments.iteritems():
            self.num_users_in_cluster[cluster] += 1
        #print self.num_users_in_cluster
        for k in range(self.num_clusters):
            in_cluster = self.num_users_in_cluster[k]
            if in_cluster == 0:
                continue
            wgt_vec = [1./in_cluster]*in_cluster
            timesteps = range(7*24)
            self.home_vec_mean[k] = self._add_vecs([vec for user,vec in self.curr_home_vec.iteritems() if self.cluster_assignments[user] == k],timesteps=timesteps,weights=wgt_vec)
            self.work_vec_mean[k] = self._add_vecs([vec for user,vec in self.curr_work_vec.iteritems() if self.cluster_assignments[user] == k],timesteps=timesteps,weights=wgt_vec)
            self.local_vec_mean[k] = self._add_vecs([vec for user,vec in self.curr_local_vec.iteritems() if self.cluster_assignments[user] == k],timesteps=timesteps,weights=wgt_vec)
            self.travel_vec_mean[k] = self._add_vecs([vec for user,vec in self.curr_travel_vec.iteritems() if self.cluster_assignments[user] == k],timesteps=timesteps,weights=wgt_vec)

        #print self.home_vec_mean
        #print self.work_vec_mean
        #print self.local_vec_mean
        #print self.travel_vec_mean

    def KL(self,dist1,dist2):
        # when we're computing the divergence, we're computing 
        kl = {}
        for t in range(7*24):
            kl[t] = 0
            for key in dist1:
                kl[t] += math.log(dist1[key][t]/dist2[key][t])*dist1[key][t]

        return sum([v for k,v in kl.iteritems()])
    
    def JS(self,dist1,dist2):
        return 0.5*self.KL(dist1,dist2)+0.5*self.KL(dist2,dist1)
            
    def compute_user_assignments(self):
        for user_id in self.gtd.getUsers():
            cluster_div = {}
            for k in range(self.num_clusters):
                curr_user_dist = {"h":self.curr_home_vec[user_id],
                                  "w":self.curr_work_vec[user_id],
                                  "l":self.curr_local_vec[user_id],
                                  "t":self.curr_travel_vec[user_id]}
                curr_cluster_dist = {"h":self.home_vec_mean[k],
                                  "w":self.work_vec_mean[k],
                                  "l":self.local_vec_mean[k],
                                  "t":self.travel_vec_mean[k]} 
                cluster_div[k] = self.JS(curr_user_dist,curr_cluster_dist)

            self.cluster_assignments[user_id] = min(cluster_div,key=cluster_div.get)

    def compute_avg_ll_of_data(self):

        n = 0
        total_ll = 0.0
        total_user_sched_ll = 0.0
        total_user_cluster_ll = 0.0
        total_canonical_ll = 0.0

        canonical_dist = { "h": self.home_vec,
                           "w": self.work_vec,
                           "l": self.local_vec,
                           "t": self.travel_vec }
        
        for user_id in self.gtd.getUsers():
            n += 1

            # compute log-likelihood according 
            curr_user_dist = {"h":self.curr_home_vec[user_id],
                              "w":self.curr_work_vec[user_id],
                              "l":self.curr_local_vec[user_id],
                              "t":self.curr_travel_vec[user_id]}
            ll = self.compute_ll_of_mle(curr_user_dist,user_id)
            total_user_sched_ll += ll

            # compute log-likelihood according to the cluster mean
            cluster = self.cluster_assignments[user_id]
            cluster_dist = { "h": self.home_vec_mean[cluster],
                           "w": self.work_vec_mean[cluster],
                           "l": self.local_vec_mean[cluster],
                           "t": self.travel_vec_mean[cluster] }
            ll = self.compute_ll_of_mle(cluster_dist,user_id)
            total_user_cluster_ll += ll

            # compute log-likelihood according to the canonical vectors
            ll = self.compute_ll_of_mle(canonical_dist,user_id)
            total_canonical_ll += ll

        total_ll += total_user_sched_ll + total_user_cluster_ll + total_canonical_ll
        total_ll /= n*3

        total_user_sched_ll /= n
        total_user_cluster_ll /= n
        total_canonical_ll /= n

        sys.stdout.write("="*80)
        sys.stdout.write("Avg Log Likelihood, overall: %0.3f\n" % total_ll)
        sys.stdout.write("User Sched Log Likelihood: %0.3f\n" % total_user_sched_ll)
        sys.stdout.write("User Cluster Log Likelihood: %0.3f\n" % total_user_cluster_ll)
        sys.stdout.write("Canonical Log Likelihood: %0.3f\n" % total_canonical_ll)

    def compute_mle(self,dist,user_id):
        ut = self.gtd.getUserTweetsByUserID(user_id)

        mle = defaultdict(list)
        for tweet_id in ut.tweetIDiter():
            tweet_info = ut.getTweet(tweet_id)
           
            t = tweet_info.weekday*24+tweet_info.time[3]  

            where_at_t = self.where_am_I(dist,user_id,t)

            mle[t].append(where_at_t)

        return mle

    def compute_ll_of_mle(self,dist,user_id):
        # determine a user's most likely location type at a given time
        # compute the log-likelihood of a user's tweets based on the most likely location assignment
        
        mle = self.compute_mle(dist,user_id)
        
        ll = 0.0
        for t in mle:
            for loc in mle[t]:
                ll += math.log(dist[loc][t])

        return ll

if __name__ == "__main__":
    ScheduleEstimator()
