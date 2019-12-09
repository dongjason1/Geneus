import json
import re
import sys
import requests
import wikipediaapi
from bs4 import BeautifulSoup


def get_classication(wikipedia_url):
    page = requests.get(wikipedia_url)
    soup = BeautifulSoup(page.text, 'html.parser')
    infoboxes = soup.find_all("table", class_="infobox")
    if len(infoboxes) < 1:
        print("No info box found.")
        sys.exit(1)

    infobox = infoboxes[0]
    infobox_tbody = infobox.findChildren("tbody", recursive=False)
    if len(infobox_tbody) < 1:
        print("No info box body found.")
        sys.exit(1)

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
                    sys.exit(1)

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
    classification_mappings = get_classication(wikipedia_url)

    text_contents = get_text_contents(wikipedia_url.split('en.wikipedia.org/wiki/', 1)[1])

    return {
        "url": wikipedia_url,
        "classification": classification_mappings,
        "text": text_contents
    }


if __name__ == '__main__':
    mappings = scrape(sys.argv[1])
    with open(sys.argv[2], mode='w') as output_file:
        json.dump(mappings, output_file, ensure_ascii=False, indent=2)
