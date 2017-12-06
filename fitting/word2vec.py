import gensim
import logging
import numpy as np
import pandas as pd
import re


class Sentences:
    def __init__(self, body):
        self.bodys = body

    def __iter__(self):
        """Strips HTML tags, converts to lowercase, and splits into a list of words.
        
        Parameters
        ----------
        body -- A pandas Series of text strings
        
        Yields
        -------
        proc -- A list of words
        """

        for b in self.bodys:
            b = re.sub('([^0-9A-z ]|<.*?>)', '', b)
            b = b.lower()
            b = b.split(' ')
            yield b


def main():
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s',
                        level=logging.INFO)

    # Have to flush the print statement if running with `tee`
    print("Reading in questions", flush=True)
    q = pd.read_csv('../data/Questions.csv', usecols=['Id', 'Body'], encoding='latin1')
    s = Sentences(q.Body)

    print("Beginning model fitting", flush=True)
    model = gensim.models.Word2Vec(sentences=s, min_count=5, window=4, workers=4)
    print("Finished fitting", flush=True)

    print("Saving model object", flush=True)
    model.save("./word2vec_model")
    print("Saving raw vectors", flush=True)
    model.wv.save_word2vec_format("./word2vec_wv.txt")
    print("Finished.", flush=True)


if __name__ == '__main__':
    main()
