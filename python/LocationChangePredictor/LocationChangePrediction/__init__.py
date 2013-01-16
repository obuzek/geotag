#!/usr/bin/env python

"""
parser = argparse.ArgumentParser(description="Run consequential location change predictor system.")
parser.add_argument("-G","--global-out",
                    metavar="global_out",
                    type=str,
                    nargs=1,
                    required=False,
                    help="where to output the global regions file")
parser.add_argument("-g","--globalregions",
                    metavar="global",
                    type=str,
                    nargs=1,
                    required=False,
                    help="global regions file from a previous run")
"""

HOME_REGION_LMBDA = 15 # in miles
USER_REGION_LMBDA = 2.5 # in miles
DAYTRIP_VARIANCE_THRES = 15 # miles -- actually stddev
STABILITY_THRESHOLD = 7 # max days to count in a "before" period
NGRAMS = 3

__all__ = ["ConsequentialLocationChangePredictor",
           "LogLinearModel",
           "SupportVectorMachine",
           "ProbabilisticGraphicalModel",
           "Vocabulary"]

#args = parser.parse_args()
"""
def main(files):
    clcp = ConsequentialLocationChangePredictor(*files)
    f = open("clcp.%s.pickle" % datetime.datetime.strftime(datetime.datetime.now(),"%y%m%d.%H%M"),
             "w+")
    f.write(pickle.dumps(clcp))
    f.close()
    return clcp

if __name__ == "__main__":
    main(sys.argv[1:])
"""
