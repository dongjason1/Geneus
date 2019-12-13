import sys

from data_processing.process_species_data import filter_has_description, load_all


def average_description_length(raw_data):
    print(f'Filtering {len(raw_data)} data items... ', end='')
    filtered_data = filter_has_description(raw_data)
    lengths = [len(data['text']['Description']) for data in filtered_data]
    from statistics import median, mean
    print(f'Mean: {mean(lengths)}, median: {median(lengths)}')


if __name__ == '__main__':
    raw_data = load_all(sys.argv[1])
    average_description_length(raw_data)
