 to see corpus information via python in rebar:
/home/hltcoe/obuzek/working/rebar/python/examples/rebar2/show_corpus.py

importing into python for processing (theresa's code):
??? wait for input from theresa
==========================processRebarTweet.py============================
def getCommunicationIds(file):
   commids = {}
   fileobj = open(file, 'r')
   for line in fileobj:
      id = (line.strip().split('\t'))[0]
      commids[id] = False
   fileobj.close

   return commids
## End getCommunicationIds ##


def loadData(id_file,datatype,corpus_name):
   if os.path.exists(id_file):
      comm_ids = getCommunicationIds(id_file)
   else:
      print "Unable to find %s" % id_file
      sys.exit()

   #print comm_ids.keys()

   if datatype == "rebar_tweet":
      return loadRebarTweets(corpus_name,comm_ids)
   elif datatype == "conll_tweet":
      return loadCoNLLTweets(corpus_name,comm_ids)
## End loadData ##


def loadRebarTweets(corpus_name,comm_ids):
   corpus = rebar2.corpus.Corpus.get_corpus(corpus_name)
   input_stages = ["tweet_info","jerboa_tokens"]
   input_version = "v1"

   reader = corpus.make_reader(input_stages)
   communications = reader.load_communications(comm_ids.keys())

   data = {}
   for message in communications:
      data[message.tweet_info.id] = processRebarTweet(message)

   reader.close()
   return data
## End loadRebarTweets ##

def processRebarTweet(message):
   tweet = Communication(message.tweet_info.id)
   try:
      tokenization = message.section_segmentation[0].section[0].sentence[0].tokenization[0]
      for token in tokenization.get_best_token_sequence():
         tweet.words.append(Word(token.text))
         if remention.match(token.text):
            tweet.words[-1].kind = "USERMENTION"
         elif rehttp.match(token.text):
            tweet.words[-1].kind = "URL"
   except IndexError:
      print "Trouble with tokenization for tweet:", message.tweet_info.id
================================================
