import argparse
import functools
import glob
import json
import os
import re
import sys
from multiprocessing.pool import Pool
from pathlib import Path

import requests
import wikipediaapi
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3 import Retry


def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def get_classication(wikipedia_url):
    page = requests_retry_session().get(wikipedia_url)
    soup = BeautifulSoup(page.text, 'html.parser')
    infoboxes = soup.find_all("table", class_="infobox")
    if len(infoboxes) < 1:
        print("No info box found.")
        return None

    infobox = infoboxes[0]
    infobox_tbody = infobox.findChildren("tbody", recursive=False)
    if len(infobox_tbody) < 1:
        print("No info box body found.")
        return None

    all_rows = infobox_tbody[0].findChildren(recursive=False)

    past_scientific_classification_row = False
    mappings = list()
    for tr in all_rows:
        if not past_scientific_classification_row:
            past_scientific_classification_row = len(
                tr.findChildren("a", string=re.compile("^scientific classification$", re.I))) > 0
        else:
            if len(tr.findChildren("th",
                                   style=lambda style_string: style_string and 'text-align: center' in style_string)) > 0:
                break
            else:
                tds = tr.findChildren("td", recursive=False)
                if len(tds) != 2:
                    print("Yikes!")
                    return None

                mappings.append({tds[0].text.strip().replace(":", ""): tds[1].text.strip()})

    return mappings


def collect_sections(sections, parents=None):
    if len(sections) == 0:
        return dict()

    sections_mapping = dict()
    for section in sections:
        title = section.title if parents is None else parents + '-' + section.title
        sections_mapping[title] = section.text
        inner_sections_mappings = collect_sections(section.sections, section.title if parents is None else parents + '-' + section.title)
        sections_mapping = {**sections_mapping, **inner_sections_mappings}
    return sections_mapping


def get_text_contents(wikipedia_article):
    wiki_wiki = wikipediaapi.Wikipedia(
        language='en',
        extract_format=wikipediaapi.ExtractFormat.WIKI
    )
    page = wiki_wiki.page(wikipedia_article)

    sections_mapping = collect_sections(page.sections)

    sections_mapping = {'__SUMMARY__': page.summary, **sections_mapping}

    return sections_mapping


def scrape(wikipedia_url):
    try:
        classification_mappings = get_classication(wikipedia_url)
        if classification_mappings is None:
            return None

        text_contents = get_text_contents(wikipedia_url.split('en.wikipedia.org/wiki/', 1)[1].strip())
    except Exception as e:
        return None

    return {
        "url": wikipedia_url,
        "classification": classification_mappings,
        "text": text_contents
    }


def scrape_n_store(wikipedia_url, output_folder, already_processed_filepath):
    output_filename = wikipedia_url.split('en.wikipedia.org/wiki/', 1)[1].strip() + '.json'
    output_filepath = os.path.join(output_folder, output_filename)
    print(f'Opening {output_filepath}.')
    with open(output_filepath, mode='w+') as output_file:
        print(f'Scraping {wikipedia_url}...')
        mappings = scrape(wikipedia_url)
        if mappings is None:
            print('Failed to get data...')
            return
        json.dump(mappings, output_file, ensure_ascii=False, indent=2)
        print(f'Saved to {output_filepath}!\n')
        with open(already_processed_filepath, 'a') as f:
            f.write(wikipedia_url)
            f.write('\n')



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Scrape species pages from page lists.")
    parser.add_argument('data_input_directory', type=str, help='directory that has folders '
                                                              'with files containing lists of species pages')
    parser.add_argument('data_output_directory', type=str, help='directory that will contain output json files')
    parser.add_argument('already_processed_file', type=str, help='file with a list of urls processed already')
    parser.add_argument('--threads', default=8, type=int, help='number of threads to use')
    # parser.add_argument('data_category', help='folders inside input e.g. animal')
    args = parser.parse_args()

    species_pages_lists = glob.glob(os.path.join(args.data_input_directory, '*.txt'))
    species_pages_lists = list(filter(lambda file: not file.endswith('searchedBadUrls.txt') and not file.endswith('lists.txt'), species_pages_lists))
    print(f'Found {len(species_pages_lists)} lists to search.')

    if not os.path.exists(args.already_processed_file):
        Path(args.already_processed_file).touch()

    with open(args.already_processed_file, 'r') as f:
        already_processeed = set(f.read().split('\n'))

    # pool = Pool(processes=args.threads)
    for species_pages_list in species_pages_lists:
        print(f'Opening {species_pages_list}... ', end='')
        output_folder = os.path.join(args.data_output_directory, os.path.splitext(os.path.basename(species_pages_list))[0])
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        scraper_f = functools.partial(scrape_n_store, output_folder=output_folder, already_processed_filepath=args.already_processed_file)

        with open(species_pages_list, mode='r') as list_f:
            species_pages = list_f.read().split('\n')
            species_pages = [item for item in species_pages if item != '']
            species_pages_uncrawled = [item for item in species_pages if item not in already_processeed]
            print(f'{len(species_pages_uncrawled)} pages to crawl ({len(species_pages) - len(species_pages_uncrawled)} already crawled).')
            print('================')
            for species_page in species_pages_uncrawled:
                scraper_f(species_page)
