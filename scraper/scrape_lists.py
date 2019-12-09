import sys

import requests
from bs4 import BeautifulSoup


def scrape(wikipedia_url):
    page = requests.get(wikipedia_url)
    soup = BeautifulSoup(page.text, 'html.parser')
    contents = soup.find("div", {"id": "mw-content-text"})
    lists = set()
    for a in contents.findChildren("a", href=lambda href: href and 'wiki' in href):
        lists.add('https://en.wikipedia.org/' + a.text)

    for list in sorted(lists):
        print(list)


if __name__ == '__main__':
    scrape(sys.argv[1])