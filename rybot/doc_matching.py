import numpy as np
import pandas as pd
from gensim.models import Doc2Vec
import re


class DocumentFinder:

    def __init__(self):
        print("Loading questions")
        self.docs = self.load_questions()
        print("Loading model")
        self.model = self.load_model()

    def load_questions(self):
        """Loads and processes the question text into the proper format.

        Returns
        -------
        questions -- A pandas DataFrame with a `Title` column of arrays of words in
        each question
        """
        questions = pd.read_csv("../data/Questions.csv", encoding='latin1',
                                usecols=["Id", "Title"])
        questions.Title = questions.Title.str.replace('([^0-9A-z ]|<[^>]+>)', '')
        questions.Title = questions.Title.str.lower()
        questions.Title = questions.Title.str.split()

        return questions

    def load_model(self):
        """Loads the Doc2Vec model created from the question text.

        Returns
        -------
        model -- A gensim Doc2Vec model
        """

        model = Doc2Vec.load("../data/doc2vec_model")
        model.delete_temporary_training_data(keep_doctags_vectors=True,
                                             keep_inference=True)
        return model

    def get_closest(self, query):
        """Returns the closest match of questions by word-movers distance.

        Parameters
        ----------
        query -- The query string to compare against

        Returns
        -------
        url -- The url of the matched question
        string -- The title of the closest match
        """

        query = re.sub('([^0-9A-z ]|<[^>]+>)', '', query)
        query = query.lower().split()
        match = [np.inf, '', '']
        for ix in range(self.docs.shape[0]):
            wmd = self.model.wv.wmdistance(query, self.docs.iloc[ix].Title)
            if wmd < match[0]:
                match[0] = wmd
                match[1] = self.docs.iloc[ix].Id
                match[2] = self.docs.iloc[ix].Id
        url = "https://www.stackoverflow.com/questions/{}".format(match[1])
        return url, match[2]


if __name__ == "__main__":
    doc = DocumentFinder()
    print(doc.get_closest("create empty numpy array"))
