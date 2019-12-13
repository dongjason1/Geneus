import pke
from nltk.corpus import stopwords

import numpy as np
from scipy import spatial
from sklearn.manifold import TSNE
from sklearn.preprocessing import normalize

"""
Extracts the keywords from a document. The lower the score, the more relevant it is

Params:
    doc (str): path to the document or raw text to analyze
Returns:
    words: list of keywords
    weights: list of weights associated with their keywords
"""
def get_keywords(doc, num=10):
    # Create a YAKE extractor and load the document
    extractor = pke.unsupervised.YAKE()
    extractor.load_document(input=doc,
                            language='en',
                            normalization=None)

    # Select candidates and weight them
    extractor.candidate_selection(n=1)
    extractor.candidate_weighting()

    # Get n highest candidates and remove redundant results using levenshtein distance threshold
    keywords = extractor.get_n_best(n=num, threshold=0.8)
    
    words = [key[0] for key in keywords]
    weights = normalize([[1/key[1] for key in keywords]], norm='l1')[0]
    return words, weights

"""
Loads the embeddings dictionary from file

Params:
    path (str): path to the previously trained embeddings dictionary
"""
def load_embeddings_dict(path='./glove_model/glove.6B.200d.txt'):
    embeddings_dict = {}
    with open(path, 'r') as f:
        for line in f:
            values = line.split()
            word = values[0]
            vector = np.asarray(values[1:], "float32")
            embeddings_dict[word] = vector
    return embeddings_dict

"""
Sorts the embeddings by closeness to the input embedding

Params:
    embedding (vector): the vector representation of the text
    embeddings_dictionary (str to vector): the embeddings dictionary
"""
def find_closest(embedding, embeddings_dictionary):
    return sorted(embeddings_dictionary.keys(), key=lambda word: spatial.distance.euclidean(embeddings_dictionary[word], embedding))

"""
Sums the embedded vectors of a list of keywords

Params:
    keywords (list of str): list of keywords
    embeddings_dictionary (str to vector): the embeddings dictionary
"""
def embed_keywords(keywords, embeddings_dictionary, weights=None):
    vec = np.zeros(300)
    if weights is None:
        for word in keywords:
            try:
                vec += embeddings_dictionary[word]
            except KeyError:
                continue
    else:
        for word,weight in zip(keywords,weights):
            try:
                vec += embeddings_dictionary[word]*weight
            except KeyError:
                continue
    return vec

if __name__ == '__main__':
    print('ooops')