#!/usr/bin/env python

HOME_REGION_LMBDA = 15 # in miles
USER_REGION_LMBDA = 2.5 # in miles
DAYTRIP_VARIANCE_THRES = 15 # miles -- actually stddev
STABILITY_THRESHOLD = 7 # max days to count in a "before" period
NGRAMS = 3

from LogLinearModel import LogLinearModel
from ProbabilisticGraphicalModel import ProbabilisticGraphicalModel
from Vocabulary import Vocabulary
from SupportVectorMachine import SupportVectorMachine

__all__ = ["LogLinearModel",
           "SupportVectorMachine",
           "ProbabilisticGraphicalModel",
           "Vocabulary"]

