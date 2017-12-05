from itertools import count

import numpy as np
import pandas as pd

from keras.callbacks import ModelCheckpoint
from keras.models import Sequential
from keras.layers import Dense, Dropout, LSTM, Flatten
from keras.layers.embeddings import Embedding

import pickle

from sklearn.preprocessing import LabelBinarizer
from sklearn.model_selection import train_test_split
from sklearn.utils import class_weight

import tensorflow as tf


def create_embedding_map(q):
    """Creates a map of words to integers

    Parameters
    ----------
    q -- Pandas DataFrame of questions with at least a `Title` field
    
    Returns
    -------
    q_embeddings -- dict() mapping words to integers
    """

    titles = q.Title.str.split()
    # Convert the words to a naive embedding
    print("Embedding words")
    q_embeddings = set()

    for title in titles:
        for word in title:
            q_embeddings.add(word.lower())

    q_embeddings = dict(zip(q_embeddings, count()))

    return q_embeddings


def generate_embeddings(q, t):
    """Converts questions and associated tags into integer vectors
    
    Parameters
    ----------
    q -- Pandas DataFrame of questions with at least `Id` and `Title` fields 
    t -- Pandas DataFrame of tags with at least `Id` and `Title` fields
    
    Returns
    -------
    q -- Pandas Dataframe of questions embedded into vectors and their first associated tag with fields `Id`, `Title`, and `Tag`
    l -- Length of each vector
    m -- Total number of distinct integers
    """ 

    titles = q.Title.str.split()
    # Convert the words to a naive embedding
    print("Embedding words")
    q_embeddings = set()

    for title in titles:
        for word in title:
            q_embeddings.add(word.lower())

    q_embeddings = dict(zip(q_embeddings, count()))
    q.Title = q.Title.map(lambda x: [q_embeddings[word.lower()] for word in x.split()])

    print("Padding titles")
    # Pad the titles to the same length
    max_title_len = q.Title.apply(len).max()

    q.Title = [np.concatenate([np.zeros(max_title_len - len(title)), title]) for title in q.Title]

    # There's definitely a better way to do this but whatever
    # This is really bad though

    print("Combining questions and tags")
    t = t.groupby('Id').first()

    q = q.join(t, on='Id', rsuffix='t_')
    q = q[~q.Tag.isna()]

    q = q[['Id', 'Title', 'Tag']]

    return q, max_title_len, max(q_embeddings.values())


def baseline_model(input_length, n_words, embedding_vector_length=32):
    n_tags = 9388
    print("Adding layers")
    model = Sequential()
    print("Adding Embedding layer")
    model.add(Embedding(n_words, embedding_vector_length, input_length=input_length))
    print("Adding LSTM layer")
    model.add(LSTM(int(input_length/2), activation='tanh'))
    model.add(Dense(n_tags, input_dim=embedding_vector_length, activation='relu'))
    model.add(Dropout(0.5))
    # print("Adding Flatten layer")
    # model.add(Flatten())
    model.add(Dense(n_tags, activation='softmax'))
    print("Compiling model")
    model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

    return model


def main():
    # fix random seed for reproducibility
    np.random.seed(1)
    print("Reading in Questions.csv")
    q = pd.read_csv("../data/Questions.csv", encoding='latin1')
    print("Reading in Tags.csv")
    t = pd.read_csv("../data/Tags.csv", encoding='latin1')
    print("Done reading in files.")

    q, l, m = generate_embeddings(q, t)
 
    print("Splitting data")
    # Split into training and testing data
    train, test = train_test_split(q, train_size=0.7)

    X_train = np.array(train.Title.tolist())
    X_test = np.array(test.Title.tolist())

    y_train = train.Tag
    y_test = test.Tag

    # Now we actually create the model
    print("Fitting Tag binarizer")
    lb = LabelBinarizer()
    lb.fit(q.Tag.unique())
    with open("./lb.pickle", 'wb') as f:
        pickle.dump(lb, f)

    class_weight_dict = class_weight.compute_class_weight('balanced',
                                                          np.unique(y_train),
                                                          y_train)
    y_train = lb.transform(y_train)
    y_test = lb.transform(y_test)

    with tf.device('/gpu:0'):
        print("Building model")
        model = baseline_model(input_length=l, n_words=m)
        checkpointer = ModelCheckpoint(filepath='model4.hdf5', verbose=1, save_best_only=True)

        model.fit(X_train, y_train, validation_data=(X_test, y_test),
                epochs=5, batch_size=25, callbacks=[checkpointer],
                  class_weight=class_weight_dict)
        print("Saving model")
        model.save("./model4.hdf5")
    print("Finshed!")

if __name__ == '__main__':
    main()
