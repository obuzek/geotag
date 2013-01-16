
import sys, math
from collections import defaultdict
from rtree import index
from LocationChangePredictor.GeoTweetDataset import Coordinates
from LocationChangePredictor.HomeRegions import Cluster

class RefineRegions:

    def __init__(self,tweets,lmbda=15): # td is a GeoTweetDataset
        if type(tweets) is not dict:
            raise TypeError("Tweets must be a dictionary of int(ID) -> TweetInfo objects.")
        #self.tweets = tweets
        
        self._l_means(tweets,lmbda)

    def _nearestCluster(self,tweet_info):
        # the nearest cluster is somewhat of an approximation -- since the rtree
        # is based on a 2-D coordinate space, and technically distances on the
        # surface of the earth are calculated using arclength, the rtree k-nn
        # function won't necessarily return the points nearest by arc length,
        # but instead by lat / long unit space.

        # to correct for this we select the argmin_cluster dist(cluster,tweet)
        # for the top 20 clusters from the rtree (for efficiency)

        locs = list(self._cluster_means.nearest(tweet_info.geo.coordForRTree(),20,objects=True))

        dists = []
        for loc in locs: # 
            cluster_id = loc.id
            cluster = loc.object

            dists.append(tweet_info.geo.distanceOnUnitSphere(cluster.mean))

        argmin = -1
        mindist = sys.maxint
        for i,dist in enumerate(dists):
            if dist < mindist:
                argmin = i
                mindist = dist
                
        return locs[argmin].id,mindist    # of the top 20 by unit dist, returns closest
                                          # by arc length

    def _kmeans_estep(self,tweets):

        for tweet_id in tweets:
            tweet_info = tweets[tweet_id]
            if self._max_cluster_id != -1:
                nearest_cluster_id, dist = self._nearestCluster(tweet_info)
                assigned_cluster_id = nearest_cluster_id
            
            if self._max_cluster_id == -1 or dist*Coordinates.RADIUS_OF_EARTH > self._lmbda:
                # create a new cluster; this is too far away
                self._max_cluster_id += 1
                assigned_cluster_id = self._max_cluster_id
                sys.stdout.write(":creating cluster number %d\n" % assigned_cluster_id)
                
                # initializing the mean of this cluster as the location of this tweet,
                # for the next round (for faster convergence)
                
                c = Cluster(tweet_info.geo,0)
                self._clusters[assigned_cluster_id] = c
                self._cluster_means.insert(assigned_cluster_id,c.mean.coordForRTree(),c)
            
            self._cluster_assmts[tweet_id] = assigned_cluster_id
    
    def _kmeans_mstep(self,tweets):
        clusters_unmentioned = self._clusters.keys()
        
        total_latitude = defaultdict(float) # all totals are indexed by cluster id
        total_longitude = defaultdict(float)
        total_in_cluster = defaultdict(int)

        for tweet_id,cluster_id in self._cluster_assmts.iteritems():
            tweet_info = tweets[tweet_id]

            total_latitude[cluster_id] += tweet_info.geo.latitude
            total_longitude[cluster_id] += tweet_info.geo.longitude
            total_in_cluster[cluster_id] += 1
            
            if cluster_id in clusters_unmentioned:
                clusters_unmentioned.remove(cluster_id)
        
        for cluster_id in total_latitude:
            total_latitude[cluster_id] /= total_in_cluster[cluster_id]
            total_longitude[cluster_id] /= total_in_cluster[cluster_id]
            
            c = Cluster(Coordinates(total_latitude[cluster_id],
                                total_longitude[cluster_id]),
                        0)
            self._cluster_means.delete(cluster_id,
                                       self._clusters[cluster_id].mean.coordForRTree())
            self._cluster_means.insert(cluster_id,
                                       c.mean.coordForRTree(),
                                       c)
            self._clusters[cluster_id] = c

        for cluster_id in clusters_unmentioned:
            self._cluster_means.delete(cluster_id,
                                       self._clusters[cluster_id].mean.coordForRTree(),
                                       self._clusters[cluster_id])
            self._clusters.pop(cluster_id)
    
    def _calc_cluster_variances(self,tweets):
        
        regions = index.Index()
        self._region_list = []
        
        total_sq_dist = defaultdict(float)
        total_in_cluster = defaultdict(int)
        
        for tweet_id, cluster_id in self._cluster_assmts.iteritems():
            tweet_info = tweets[tweet_id]
            
            cluster = self._clusters[cluster_id]

            total_sq_dist[cluster_id] += math.pow(tweet_info.geo.distanceOnUnitSphere(cluster.mean),
                                                  2)
            total_in_cluster[cluster_id] += 1
        
        for cluster_id in total_sq_dist:
            cluster = self._clusters[cluster_id]
            
            c = Cluster(cluster.mean,
                        total_sq_dist[cluster_id] / total_in_cluster[cluster_id])
            
            regions.insert(cluster_id,
                           cluster.mean.coordForRTree(),
                           c)
            self._region_list.append((cluster_id,c))
        
        return regions

    def _l_means(self,tweets,lmbda,iterations=15): # lmbda is the num miles away before beginning new cluster
        self._lmbda = lmbda
        self._cluster_means = index.Index()
        self._clusters = {}       # cluster_id -> Cluster object
        self._cluster_assmts = {} # tweet_id -> cluster

        self._max_cluster_id = -1

        for i in range(iterations):
            self._kmeans_estep(tweets)
            self._kmeans_mstep(tweets)

        self._regions = self._calc_cluster_variances(tweets)
        
    def assignments(self,tweets_to_process):
        region_assmts = {}
        for tweet_id,tweet_info in tweets_to_process.iteritems():
            if tweet_id in self._cluster_assmts:
                region_assmts[tweet_id] = self._cluster_assmts[tweet_id]

            else:
                region_assmts[tweet_id] = self.getRegionNumber(tweet_info)

        return region_assmts
    
    def getRegionInfo(self,region_num):
        return self._clusters[region_num].mean

    def getRegionNumber(self,tweet_info):
        if tweet_info.id in self._cluster_assmts:
            return self._cluster_assmts[tweet_info.id]
        return self._nearestCluster(tweet_info)[0] # just the id, thanks

    def dump_gaussians(self,fname):
        # dumps the RefineRegions information to a flat file
        # organized by region: cluster number, mean lat, mean long, sigma^2

        f = open(fname,"w+")
        
        f.write("CLUSTER\tMU_LAT\tMU_LONG\tVAR\n")

        for cluster_id, cluster in self._region_list:
            f.write("%d\t%0.4f\t%0.4f\t%0.4f\n" % (cluster_id,
                                                   cluster.mean.latitude,
                                                   cluster.mean.longitude,
                                                   cluster.variance))

        f.close()

        sys.stdout.write("Gaussians now available in file: %s\n" % (fname))
    
"""
    def dump_cluster_assmts(self,fname):
        # dumps the RefineRegions information to a flat file
        # organized by tweetloc: cluster number, lat, long
        # don't use this
        
        f = open(fname,"w+")
        f.write("CLUSTER\tLAT\tLONG\n")
        for tweet_id,cluster_id in self._cluster_assmts.iteritems():
            tweet_info = self.tweets[tweet_id]
            f.write("%d\t%0.4f\t%0.4f\n" % (cluster_id,
                                            tweet_info.geo.latitude,
                                            tweet_info.geo.longitude))
"""
