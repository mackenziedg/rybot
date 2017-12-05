import gensim
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
        
        Returns
        -------
        proc -- Yields a processed string to list of words
        """
        
        for b in self.bodys:
            b = re.split("<.*?>", b)
            b = re.sub('[0-9A-z]', '', ''.join(b))
            yield b.lower()


q = pd.read_csv('../../stackoverflow-nlp/stacksample/Questions.csv', usecols=['Id', 'Body'], encoding='latin1')
s = Sentences(q.Body)

model = gensim.models.Word2Vec(sentences=s, min_count=12, workers=4)
