import json
import re
import sys
import requests
import urllib.parse
import os
from bs4 import BeautifulSoup

def scrapeUrls(url, maxTries=5):
    if maxTries == 0:
        return set()

    try:
        page = requests.get(url)
    except:
        return scrapeUrls(url, maxTries - 1)

    soup = BeautifulSoup(page.text, 'html.parser')
    bodyContent = soup.find("div", {"id":"mw-content-text"})
    urls = bodyContent.findChildren("a", href=lambda href: href and ('wiki' in href))

    urlSet = set()
    for url in urls:
        urlSet.add("https://en.wikipedia.org" + url['href'])

    return urlSet

def isSpeciesPage(url, maxTries=5):
    if maxTries == 0 or (url.startswith("https://en.wikipedia.org/wiki/File:")):
        return False

    try:
        page = requests.get(url)
    except:
        return isSpeciesPage(url, maxTries - 1)

    soup = BeautifulSoup(page.text, 'html.parser')
    infoboxes = soup.find_all("table", class_="infobox")
    if len(infoboxes) < 1:
        #print("No info box found. (" + url + ")")
        return False

    infobox = infoboxes[0]
    infobox_tbody = infobox.findChildren("tbody" , recursive=False)
    if len(infobox_tbody) < 1:
        #print("No info box body found. (" + url + ")")
        return False

    all_rows = infobox_tbody[0].findChildren(recursive=False)

    past_scientific_classification_row = False
    for tr in all_rows:
        if not past_scientific_classification_row:
            past_scientific_classification_row = len(tr.findChildren("a", string=re.compile("^scientific classification$", re.I))) > 0
        else:
            if len(tr.findChildren("th", style=lambda style_string: style_string and 'text-align: center' in style_string)) > 0:
                break
            else:
                tds = tr.findChildren("td", recursive=False)
                if len(tds) != 2:
                    print("Yikes! (" + url + ")", file=sys.stderr, flush=True)
                    return False

                if tds[0].text.strip().replace(":", "") == "Species":
                    print("Yay! (" + url + ")", file=sys.stdout, flush=True)
                    return True
    return False

if __name__ == '__main__':
    print("Starting the Run", file=sys.stdout, flush=True)
    print("Starting the Run", file=sys.stderr, flush=True)
    animalPath = "../data/fungi"
    with open(animalPath + "/lists.txt","r") as file:
        listOfLists = file.read().split('\n')

    for listUrl in listOfLists:
        inputUrl = listUrl
        speciesUrlSet = scrapeUrls(inputUrl)
        parsedUrl = urllib.parse.unquote(inputUrl)

        outputFileName = animalPath + "/" + parsedUrl[len("https://en.wikipedia.org/wiki/"):] + ".txt"
        badURLFileName = animalPath + "/" + "searchedBadUrls.txt"

        #Make the file if it doesnt exist
        if not os.path.exists(outputFileName):
            os.mknod(outputFileName)

        if not os.path.exists(badURLFileName):
            os.mknod(badURLFileName)

        with open(outputFileName,"r") as file:
            searched = set(file.read().split('\n'))

        with open(badURLFileName,"r") as file:
            searchedBad = set(file.read().split('\n'))

        file = open(outputFileName,"a")
        fileBad = open(badURLFileName, "a")
        for url in speciesUrlSet:
            urlParse = urllib.parse.unquote(url)
            if (not urlParse in searched) and (not urlParse in searchedBad):
                if isSpeciesPage(url):
                    file.write(urlParse + '\n')
                    file.flush()
                else:
                    fileBad.write(urlParse + '\n')
                    fileBad.flush()
        file.close()
