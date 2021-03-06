import argparse
import glob
import itertools
import json
import os
import sys

import numpy
import numpy as np
from json import JSONDecodeError
from pathlib import Path

from tqdm import tqdm

# from keyword_extractor.keyword import get_keywords, load_embeddings_dict, embed_keywords
# from bert_extractor.bert_extractor import BertModel

BERT_PATH='/home/yxh597/projects/dl-final-project/bert_en_uncased_L-24_H-1024_A-16'

"""
For keywords: 
python3 data_processing/process_species_data.py species_data no_filter create_keyword_representation one_hot_encode_kingdom input_datas/keyword
"""

def load_all(data_directory):
    json_files = list(Path(data_directory).rglob('*.json'))
    data = []
    for json_file in tqdm(json_files, desc='Loading JSON files into memory...'):
        with json_file.open() as json_f:
            try:
                data.append(json.load(fp=json_f))
            except JSONDecodeError as e:
                print(f'Could not JSON decode {json_file}')

    return data


def transform_data(data, data_func, label_func):
    data_item_transformed = []
    for data_item_raw in tqdm(data, desc='Creating data...'):
        data_item_transformed.append(data_func(data_item_raw))
    data_label_transformed = []
    for data_item_raw in tqdm(data, desc='Creating labels...'):
        data_label_transformed.append(label_func(data_item_raw))
    return data_item_transformed, data_label_transformed


def save_data(all_data, all_labels, filename_prefix):
    data_filename = filename_prefix + '_data.json'
    labels_filename = filename_prefix + '_labels.json'
    if not os.path.exists(data_filename):
        Path(data_filename).touch()
    if not os.path.exists(labels_filename):
        Path(labels_filename).touch()
    with open(data_filename, 'w+') as f:
        json.dump(all_data, fp=f)
    with open(labels_filename, 'w+') as f:
        json.dump(all_labels, fp=f)


def filter_data(raw_data, filter_func):
    return filter_func(raw_data)


def filter_has_description(all_data):
    return list(filter(lambda data: 'Description' in data['text'], all_data))


# Dummy thingy for testing
def data_article_length(all_data):
    def article_length(data):
        return [sum([len(section_text) for section_text in data['text'].values()])]
    return list(map(article_length, tqdm(all_data)))


def no_filter(all_data):
    return all_data


def one_hot_encode_kingdom(all_data):
    kingdoms = ['Animalia', 'Plantae', 'Fungi']

def find_all_for_key(all_data, target_key):
    if target_key == 'Kingdom':
        return ['Animalia', 'Plantae', 'Fungi']
    key_set = set()
    for single_data in all_data:
        for entry in single_data['classification']:
            key, value = list(entry.items())[0]
            if key == target_key:
                key_set.add(value)
    return key_set


def one_hot_encode(all_data, keys):
    labels_values = [list(sorted(find_all_for_key(all_data, target_key))) for target_key in keys]
    labels_keys = [[target_key]*len(label) for label, target_key in zip(labels_values, keys)]

    labels_values_flattened = list(itertools.chain(*labels_values))
    labels_keys_flattened = list(itertools.chain(*labels_keys))

    shape = len(labels_keys_flattened)

    def one_hot_encode_item(single_data):
        vector = np.zeros(shape, dtype=numpy.int8)
        for entry in single_data['classification']:
            key, value = list(entry.items())[0]
            if key in keys:
                if value[0] == '?':
                    value = value[1:]
                vector[labels_values_flattened.index(value)] = 1

        return vector.tolist()

    return labels_keys_flattened, labels_values_flattened, list(map(one_hot_encode_item, tqdm(all_data)))

def one_hot_encode_phyla(all_data):
    return one_hot_encode(all_data, keys=['Kingdom', 'Phylum'])


# """
# Creates the keyword word embedding representation of the text data. Cleans the data for mentions of the taxonomy
#
# Params:
#     documents (lis of dict): JSON documents to convert
#     n (int): number of keywords to generate
#     weighted (bool): whether or not to use a weighted sum
# """
# def create_keyword_representation(documents, n=20, weighted=True):
#     print('loading embeddings...')
#     embed = load_embeddings_dict(path='data_processing/glove_model/glove.6B.300d.txt')
#
#     # wikipedia sections not to read
#     banned_sections = ['references', 'see also', 'external links']
#     output = []
#
#     for doc in tqdm(documents, desc='Converting documents to keyword vectors'):
#         # taxonomy words to remove from training data
#         taxonomy_words = []
#         for dic in doc['classification']:
#             key = list(dic.keys())[0]
#             val = dic[key]
#             taxonomy_words.append(key.lower())
#             taxonomy_words.append(val.lower())
#
#         #concatenate the paragraphs
#         concat = ""
#         for key, val in doc['text'].items():
#             if key.lower() not in banned_sections:
#                 concat += " " + val
#
#         # get keywords from concatenated sections and remove taxonomy words
#         keys, weights = get_keywords(concat, num=n)
#         i = 0
#         while i < len(keys):
#             if keys[i].lower() in taxonomy_words:
#                 del keys[i]
#                 np.delete(weights, i)
#                 i-=1
#             i += 1
#
#         # Get the word embedding representation
#         representation = embed_keywords(keys, embed, weights) if weighted else embed_keywords(keys, embed)
#         output.append(representation.tolist())
#     return output


def extract_text_from_doc(doc):
    banned_sections = ['references', 'see also', 'external links']
    concat = ""
    for key, val in doc['text'].items():
        if key.lower() not in banned_sections:
            concat += " " + val         
    return concat


def create_bert_representation(documents, max_len=128):
    bert_model = BertModel(BERT_PATH, max_len)
    print('Working on BERT representations...')
    
    # Extract sections
    doc_texts = [extract_text_from_doc(doc) for doc in documents]
       
    reprs = bert_model.get_reprs(doc_texts)
    return reprs.tolist()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Format")
    parser.add_argument('data_directory', type=str, help='directory that has json files')
    parser.add_argument('filename_prefix', type=str, help='output filename prefix')
    args = parser.parse_args()

    raw_data = load_all(args.data_directory)
    labels_keys_flattened, labels_values_flattened, labels = one_hot_encode(raw_data, keys=['Kingdom', 'Phylum', 'Class'])

    labels_keys_filename = args.filename_prefix + '_labels_keys.json'
    labels_values_filename = args.filename_prefix + '_labels_values.json'
    labels_filename = args.filename_prefix + '_labels.json'

    if not os.path.exists(labels_keys_filename):
        Path(labels_keys_filename).touch()
    if not os.path.exists(labels_values_filename):
        Path(labels_values_filename).touch()
    if not os.path.exists(labels_filename):
        Path(labels_filename).touch()

    with open(labels_keys_filename, 'w+') as f:
        json.dump(labels_keys_flattened, fp=f)
    with open(labels_values_filename, 'w+') as f:
        json.dump(labels_values_flattened, fp=f)
    with open(labels_filename, 'w+') as f:
        json.dump(labels, fp=f)



# if __name__ == '__main__':
#     parser = argparse.ArgumentParser(description="Format")
#     parser.add_argument('data_directory', type=str, help='directory that has json files')
#     parser.add_argument('filter_func', type=str, default='no_filter', help='function in this module to filter data points')
#     parser.add_argument('data_func', type=str, help='function in this module to transform into data')
#     parser.add_argument('label_func', type=str, help='function in this module to transform into labels')
#     parser.add_argument('filename_prefix', type=str, help='output filename prefix')
#     args = parser.parse_args()
#
#     raw_data = load_all(args.data_directory)
#     print(f'Filtering {len(raw_data)} data items... ', end='')
#     filtered_data = locals()[args.filter_func](raw_data)
#     print(f'{len(filtered_data)} remaining.')
#     print('Creating data items...')
#     # data = locals()[args.data_func](raw_data)
#     print('Creating label items...')
#     labels = locals()[args.label_func](raw_data)
#
#     # if len(data) != len(labels):
#     #     print(f'Length of data ({len(data)}) and labels ({len(labels)}) were unequal... aborting.')
#     #     sys.exit(1)
#
#     print('Saving data and labels... ', end='')
#     # save_data(data, labels, filename_prefix=args.filename_prefix)
#     print('DONE!')
