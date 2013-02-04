#!/usr/bin/python
"""
Summarize the information in a given corpus.
"""

# We're in a subdirectory of rebar/python -- add our parent directory
# to the path.
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import rebar2
import sys, os, itertools, subprocess, optparse
import google.protobuf.message


USAGE='''\
%prog [options] corpus stage [version] [subset]

  corpus: The name of the corpus to process.
'''
def main():
    parser = optparse.OptionParser(usage=USAGE)
    parser.add_option("-v", action='count', dest='verbose', default=0,
                      help="Generate more verbose output")
    parser.add_option("-q", action='count', dest='quiet', default=0,
                      help="Generate less verbose output")
    parser.add_option("-o", dest='outfile', metavar='FILE',
                      help='Output file (stdout if not specified)')
    parser.add_option("--no-accumulo", dest='use_accumulo', action='store_false',
                      default=True)
    parser.add_option("--num-examples", metavar='N', dest='num_examples',
                      help='Number of full example objects to print',
                      type=int, default=1)
    parser.add_option("-n", metavar='N', dest='num_summary', type=int,
                      help='Number of objects to examine when building the '
                      'summary of fields', default=100)

    (options, args) = parser.parse_args()
    verbosity = 1 + options.verbose - options.quiet
    if len(args) < 2: parser.error('Expected a corpus name')
    if len(args) > 4: parser.error('Expected at most 4 positional args')
    corpus_name = args[0]
    if len(args) >= 2: src_stage = args[1]
    else: src_stage = 'ingest'
    if len(args) >= 3: src_ver = args[2]
    else: src_ver = None
    if len(args) >= 4: subset = args[3]
    else: subset = None
    if options.outfile is None:
        out = sys.stdout
    elif options.outfile.endswith('.gz'):
        import gzip
        out = gzip.GzipFile(options.outfile, 'wb')
    elif options.outfile.endswith('.bz2'):
        import bz2
        out = bz2.BZ2File(options.outfile, 'wb')
    else:
        out = open(options.outfile, 'wb')


    if verbosity >= 0:
        print >>sys.stderr, 'Connecting to corpus %r...' % corpus_name
    corpus = rebar2.corpus.Corpus.get_corpus(corpus_name)
    if src_ver is None:
        src_ver = corpus.get_stage_versions(src_stage)[-1]
    if verbosity > 0:
        print >>sys.stderr, '  Reading from stage: %s (version %s)' % (src_stage, src_ver)

    #out = []
    out.write("Corpus Summary for: %s" % corpus_name)
    
    # Display the output stages for this corpus.
    out.write(' Stages '.center(75, '='))
    stage_to_version = {}
    for stage in corpus.get_stages():
    	stage_to_version.setdefault(stage.name, []).append(stage.version)
    
    for stage_name in stage_to_version.keys():
        out.write('  %s [%s]' % (stage.name, ','.join(
            ver for ver in stage_to_version[stage_name])))

    out.write("\nStage contents for: %s (%s)\n" % (src_stage, src_ver))

    reader = corpus.make_reader(src_stage)
    communications = reader.load_communications()
    num_communications = corpus.get_num_communications()
    out.write('Found %d communications.\n' % (num_communications))
    if out != sys.stdout:
        print 'Found %d communications.\n' % (num_communications)
	
    #print '\n'.join(out)
    for communication in communications:
    	out.write('------------------------------------------------------------------\n')
        out.write(communication.__str__())

    out.close()
    corpus.close()

def show_fields(pbobj, indent='', count=None):
    """
    Show a summary of what fields are defined in a protobuf object
    (without actually showing the values -- to see the values as well,
    just print the pbobj)
    """
    s = '%s' % type(pbobj).__name__
    if count is not None: s += ' (%d)' % count
    for (fd, fv) in pbobj.ListFields():
        name = fd.name.ljust(40-len(indent), '.')
        if isinstance(fv, rebar2.UUID):
            s += '\n%s  %s UUID' % (indent, name)
        elif isinstance(fv, google.protobuf.message.Message):
            s += '\n%s  %s %s' % (indent, name, show_fields(fv, indent+'  '))
        elif hasattr(fv, 'MergeFrom'):
            if len(fv) == 0:
                s += '\n%s  %s repeated %s' % (indent, name, fd.message_type.name)
            else:
                mergedval = type(fv[0])()
                for v in fv: mergedval.MergeFrom(v)
                s += '\n%s  %s repeated %s' % (indent, name,
                                               show_fields(mergedval, indent+'  ', len(fv)))
        else:
            s += '\n%s  %s %s' % (indent, name, type(fv).__name__)
    return s

if __name__ == '__main__':
    main()
