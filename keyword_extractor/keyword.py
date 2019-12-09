import pke
from nltk.corpus import stopwords

"""
Extracts the keywords from a document. The lower the score, the more relevant it is

Params:
    doc (str): path to the document or raw text to analyze
"""
def get_keyphrases(doc, n=10):
    # Create a YAKE extractor and load the document
    extractor = pke.unsupervised.YAKE()
    extractor.load_document(input=doc,
                            language='en',
                            normalization=None)

    # Select candidates and weight them
    extractor.candidate_selection(n=1)
    extractor.candidate_weighting()

    # Get n highest candidates and remove redundant results using levenshtein distance threshold
    keyphrases = extractor.get_n_best(n=n, threshold=0.8)
    return keyphrases

if __name__ == '__main__':
    get_keyphrases('this is my document')
