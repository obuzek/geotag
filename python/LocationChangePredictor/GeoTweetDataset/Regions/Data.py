from collections import namedtuple
import math

Cluster = namedtuple("Cluster",["mean", # a Coordinates object
                                "variance"]) # sigma^2, in lat / long units

class Coordinates(namedtuple("Coord",["latitude",
                                        "longitude"])):
    RADIUS_OF_EARTH = 3963.1676 #miles
    
    def coordForRTree(self):
        # (minx, miny, maxx, maxy)
        # (left, bottom, right, top)
        # (long, lat, long, lat)
        return (self.longitude,
                self.latitude,
                self.longitude,
                self.latitude)

    def __iadd__(self,coord):
        return Coordinates(self.latitude+coord.latitude,
                           self.longitude+coord.longitude)

    def __idiv__(self,num):
        return Coordinates(self.latitude / num,
                           self.longitude / num)

    def __mult__(self,num):
        c = Coordinates(self.latitude * num,self.longitude * num)
        return c

    def __sub__(self,coord):
        return self.distanceOnUnitSphere(coord)

    def distanceOnUnitSphere(self, coord, unit_multiplier=1.0):
        # code yoinked from elsewhere
        # http://www.johndcook.com/python_longitude_latitude.html

        # Convert latitude and longitude to
        # spherical coordinates in radians.
        degrees_to_radians = math.pi/180.0

        lat1 = self.latitude
        long1 = self.longitude
        lat2 = coord.latitude
        long2 = coord.longitude
        
        # phi = 90 - latitude                                              
        phi1 = (90.0 - lat1)*degrees_to_radians
        phi2 = (90.0 - lat2)*degrees_to_radians
        
        # theta = longitude
        theta1 = long1*degrees_to_radians
        theta2 = long2*degrees_to_radians

        # Compute spherical distance from spherical coordinates.
        # For two locations in spherical coordinates
        # (1, theta, phi) and (1, theta, phi)
        # cosine( arc length ) =
        #    sin phi sin phi' cos(theta-theta') + cos phi cos phi'
        # distance = rho * arc length
        
        cos = (math.sin(phi1)*math.sin(phi2)*math.cos(theta1 - theta2) +
               math.cos(phi1)*math.cos(phi2))
        
        arc = math.acos( round(cos,12) )

        # Remember to multiply arc by the radius of the earth
        # in your favorite set of units to get length.
        
        return arc*unit_multiplier


