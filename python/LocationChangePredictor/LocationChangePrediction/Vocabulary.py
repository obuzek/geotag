
class Vocabulary:
    
    def __init__(self):
        self.vocab = {}
        self.max_index = 0

    def get_vocab_num(self,feature):
        if feature in self.vocab:
            return self.vocab[feature]
        else:
            self.vocab[feature] = self.max_index
            self.max_index += 1

        return self.vocab[feature]
