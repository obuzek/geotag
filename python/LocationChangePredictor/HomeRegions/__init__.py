#!/usr/bin/env python

from collections import namedtuple

__all__ = ["RefineRegions",
           "HomeRegions"]

Cluster = namedtuple("Cluster",["mean", # a Coordinates object
                                "variance"]) # sigma^2, in lat / long units
    
    
