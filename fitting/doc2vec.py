import gensim
import logging
import numpy as np
import pandas as pd
import pickle
import re


class Sentences:
    def __init__(self, body):
        self.bodys = body
        self.lab_sents = []
        for ix, b in enumerate(self.bodys):
            b = re.sub('([^0-9A-z ]|<.*?>)', '', b)
            b = b.lower()
            b = b.split(' ')
            self.lab_sents.append(gensim.models.doc2vec.LabeledSentence(b, "SENT_{}".format(ix)))

    def __iter__(self):
        """Strips HTML tags, converts to lowercase, and splits into a list of words.

        Parameters
        ----------
        body -- A pandas Series of text strings

        Yields
        -------
        proc -- A list of word/id pairs
        """
        for i in self.lab_sents:
            yield i


def main():
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s',
                        level=logging.INFO)

    # Have to flush the print statement if running with `tee`
    print("Reading in questions", flush=True)
    q = pd.read_csv('../data/Questions.csv', usecols=['Id', 'Title'], encoding='latin1')
    print("Converting to the proper format")
    s = Sentences(q.Title)
    with open("./sentences", "wb+") as f:
        # s = pickle.load(s)
        pickle.dump(s, f)

    print("Beginning model fitting", flush=True)
    model = gensim.models.Doc2Vec(size=300, min_count=5, window=10, workers=10,
                                  alpha=0.025, min_alpha=0.025)
    model.build_vocab(s)
    for epoch in range(10):
        model.train(s, total_words=model.corpus_count, epochs=model.iter)
        model.alpha -= 0.002
        model.min_alpha = model.alpha
    print("Finished fitting", flush=True)

    print("Saving model object", flush=True)
    model.save("./doc2vec_model")
    # print("Saving raw vectors", flush=True)
    # model.wv.save_doc2vec_format("./word2vec_wv.txt")
    print("Finished.", flush=True)


if __name__ == '__main__':
    main()
