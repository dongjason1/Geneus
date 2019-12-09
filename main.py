from keyword_extractor.keyword import get_keyphrases


if __name__ == '__main__':
    words = get_keyphrases('keyword_extractor/test_document.txt', n=100)
    print(words)