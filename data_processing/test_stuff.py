import sys

import matplotlib as matplotlib
import numpy as np
import matplotlib.pyplot as plt

from data_processing.process_species_data import filter_has_description, load_all


def average_description_length(raw_data):
    print(f'Filtering {len(raw_data)} data items... ', end='')
    filtered_data = filter_has_description(raw_data);
    print(f'Number with description: {len(filtered_data)}')
    lengths = [len(data['text']['Description']) for data in filtered_data]
    from statistics import median, mean
    print(f'Mean: {mean(lengths)}, median: {median(lengths)}')
    # frequency, bins = np.histogram(lengths, bins=20)

    lengths_summary = [len(data['text']['__SUMMARY__']) for data in raw_data]

    fig, axs = plt.subplots(2, 1)

    n_bins = 150

    axs[0].hist(lengths_summary, bins=n_bins)
    axs[0].set_title("Article summary lengths")
    axs[0].set_xlabel("Number of words")
    axs[0].set_ylabel("Number of articles")

    axs[1].hist(lengths, bins=n_bins)
    axs[1].set_title("Article description lengths")
    axs[1].set_xlabel("Number of words")
    axs[1].set_ylabel("Number of articles")

    fig.tight_layout()
    # plt.show()
    plt.savefig('lengths.png', dpi=300)


if __name__ == '__main__':
    raw_data = load_all(sys.argv[1])
    average_description_length(raw_data)
