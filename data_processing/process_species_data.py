import argparse
import glob
import json
import os
import sys
from json import JSONDecodeError
from pathlib import Path

from tqdm import tqdm


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

    def one_hot_encode(single_data):
        for entry in single_data['classification']:
            key, value = list(entry.items())[0]
            if key == 'Kingdom':
                item = [0, 0, 0]
                for i in range(len(kingdoms)):
                    if kingdoms[i] in value:
                        item[i] = 1
                        return item
                print(f'Kingdom {value} is unknown for {single_data["url"]}')
                sys.exit(1)

        print(f'{single_data["url"]} has no Kingdom...')
        sys.exit(1)

    return list(map(one_hot_encode, tqdm(all_data)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Format")
    parser.add_argument('data_directory', type=str, help='directory that has json files')
    parser.add_argument('filter_func', type=str, default='no_filter', help='function in this module to filter data points')
    parser.add_argument('data_func', type=str, help='function in this module to transform into data')
    parser.add_argument('label_func', type=str, help='function in this module to transform into labels')
    parser.add_argument('filename_prefix', type=str, help='output filename prefix')
    args = parser.parse_args()

    raw_data = load_all(args.data_directory)
    print(f'Filtering {len(raw_data)} data items... ', end='')
    filtered_data = locals()[args.filter_func](raw_data)
    print(f'{len(filtered_data)} remaining.')
    print('Creating data items...')
    data = locals()[args.data_func](raw_data)
    print('Creating label items...')
    labels = locals()[args.label_func](raw_data)

    if len(data) != len(labels):
        print(f'Length of data ({len(data)}) and labels ({len(labels)}) were unequal... aborting.')
        sys.exit(1)

    print('Saving data and labels... ', end='')
    save_data(data, labels, filename_prefix=args.filename_prefix)
    print('DONE!')
