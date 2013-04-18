#!/usr/bin/env python

import argparse, datetime, pickle, os
from LocationChangePredictor.ConsequentialLocationChangePredictor import ConsequentialLocationChangePredictor
from LocationChangePredictor import Config

def main():

    parser = argparse.ArgumentParser(description="Run consequential location change predictor system.")
    parser.add_argument("files",
                        type=str,
                        nargs="*",
                        help="corpus files, must be a flat file of json tweets or corpus, version")
    parser.add_argument("-r","--regex_testing",
                        metavar="regex_file",
                        type=str,
                        nargs=1,
                        required=False,
                        help="annotate the corpus in accordance with a set of regexes")
    parser.add_argument("-f","--foursquare",
                        action="store_true",
                        help="annotate the corpus with a foursquare labeling (and output obtained info to file; not yet used)")                      
    parser.add_argument("-R","--rebar",
                        action="store_true",
                        required=False,
                        help="interpret files argument as corpus, version")
    parser.add_argument("-d","--project-loc",
                        metavar="proj_loc",
                        type=str,
                        nargs=1,
                        required=False,
                        help="where the base directory for the project is")
    parser.add_argument("-G","--global-out",
                        metavar="global_out",
                        type=str,
                        nargs=1,
                        required=False,
                        help="where to output the global regions file")
    parser.add_argument("-E","--exp-out",
                        metavar="exp_out",
                        type=str,
                        nargs=1,
                        required=False,
                        help="where to put any experiment-related results")
    parser.add_argument("-g","--globalregions",
                        metavar="global",
                        type=str,
                        nargs=1,
                        required=False,
                        help="global regions file from a previous run")

    args = parser.parse_args()

    # print args
    
    #for i,f in enumerate(args.files):
    #    args.files[i] = os.path.abspath(f)

    if not args.project_loc:
        Config.proj_loc = os.path.abspath(os.environ["GEO_PROJ_LOC"])
    else:
        Config.proj_loc = os.path.abspath(args.project_loc)

    if not args.global_out:
        Config.global_out = os.path.abspath(Config.proj_loc + "/cache")
    else:
        Config.global_out = os.path.abspath(args.global_out)

    if not args.exp_out:
        Config.exp_out = os.path.abspath(Config.proj_loc + "/cache")
    else:
        Config.exp_out = os.path.abspath(args.exp_out)

    if not os.path.isdir(Config.proj_loc):
        raise ValueError("bad path - %s (project location must be a path to a valid directory on the system, check $GEO_PROJ_LOC or -d)" % proj_loc)

    if not os.path.isdir(Config.global_out):
        raise ValueError("bad path - %s (global region location must be a path to a valid directory on the system, check $GEO_PROJ_LOC or -G)" % global_out)

    if not os.path.isdir(Config.exp_out):
        raise ValueError("bad path - %s (experimental output location must be a path to a valid directory on the system, check $GEO_PROJ_LOC or -E)" % exp_out)

    if args.rebar:
        for f in args.files:
            print f
        corpus = args.files[0]
        version = args.files[1]
        print corpus
        print version
        clcp = ConsequentialLocationChangePredictor(corpus=corpus,version=version)
        f = open(Config.global_out+"/clcp.%s.pickle" % datetime.datetime.strftime(datetime.datetime.now(),"%y%m%d.%H%M"),
                 "w+")
        f.write(pickle.dumps(clcp))
        f.close()
        return clcp

    clcp = ConsequentialLocationChangePredictor(*(args.files))
    clcp.estimate_schedules()
    # clcp.do_home_regions()
    if args.regex_testing is not None:
        for regex in args.regex_testing:
            clcp.regex_testing(regex)
    if args.foursquare:
        clcp.foursquare_labeling()
    f = open(Config.global_out+"/clcp.%s.pickle" % datetime.datetime.strftime(datetime.datetime.now(),"%y%m%d.%H%M"),
             "w+")
    f.write(pickle.dumps(clcp))
    f.close()
    return clcp

if __name__ == "__main__":
    main()
