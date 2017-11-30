from itertools import count

import numpy as np
import pandas as pd

from keras.models import Sequential
from keras.layers import Dense, LSTM, Flatten
from keras.layers.embeddings import Embedding
from keras.preprocessing import sequence
from keras.utils import np_utils
from keras.wrappers.scikit_learn import KerasClassifier

from sklearn.preprocessing import LabelEncoder, LabelBinarizer
from sklearn.model_selection import train_test_split, KFold, cross_val_score

import tensorflow as tf

# fix random seed for reproducibility
np.random.seed(1)
# q = pd.read_csv("./data/Questions.csv", encoding='latin1')
# t = pd.read_csv("./data/Tags.csv", encoding='latin1')
print("Reading in Questions.csv")
q = pd.read_csv("../../stackoverflow-nlp/stacksample/Questions.csv", encoding='latin1')
print("Reading in Tags.csv")
t = pd.read_csv("../../stackoverflow-nlp/stacksample/Tags.csv", encoding='latin1')
print("Done reading in files.")

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

print("Splitting data")
# Split into training and testing data
train, test = train_test_split(q, train_size=0.7)

X_train = train.Title
X_test = test.Title

y_train = train.Tag
y_test = test.Tag

# Now we actually create the model

print("Fitting Tag binarizer")
lb = LabelBinarizer()
lb.fit(q.Tag.unique())

def baseline_model(input_length=max_title_len, n_words=max(q_embeddings.values()),
                   embedding_vector_length=32, n_tags=9388):
    model = Sequential()
    model.add(Embedding(n_words, embedding_vector_length, input_length=input_length))
    model.add(Dense(10, input_dim=embedding_vector_length, activation='relu'))
    model.add(Flatten())
    model.add(Dense(n_tags, activation='softmax'))
    model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
    
    return model

with tf.device('/gpu:0'):
    print("Building model")
    model = baseline_model()
    model.fit(np.array(X_train.tolist()), lb.transform(y_train), epochs=10, batch_size=10)
    print("Saving model")
    model.save("./model1")
