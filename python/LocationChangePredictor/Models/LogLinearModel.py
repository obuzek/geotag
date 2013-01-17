
class LogLinearModel:
    
    def __init__(self,window):
        self.window = window # 1-7 or -1 == "home"
        self.feature_counts = defaultdict(int)
        self.total_counts = 0

    def normalize_counts(self): # turns them all into log-likelihoods
        
        self.prob = defaultdict(float)
        
        if self.total_counts == 0:
            sys.stdout.write(">> No data for model "+str(self.window))
            return
        denom = math.log(self.total_counts)
        
        for ftr in self.feature_counts:
            self.prob[ftr] = math.log(self.feature_counts[ftr]) - denom

    def evaluate_prob(self,ngrams):
        
        total_prob = 0

        for ngram in ngrams:
            total_prob += self.prob[ngram]

        return total_prob

    def add(self,ngrams):
        for ngram in ngrams:
            self.feature_counts[ngram] += 1
            self.total_counts += 1

    def generate_ngrams(self,tweet):

        tkns = tweet.split(" ")

        grams = []

        for n in range(NGRAMS):
            for i,tkn in enumerate(tkns):
                grams.append(" ".join(tkns[i:i+n+1]))
                
        return grams
