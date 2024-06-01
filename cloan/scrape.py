from bs4 import BeautifulSoup
from io import TextIOWrapper
import requests
import re



def _dehyphenate(word: str):
    outlist = [word]
    if "-" in word:
        word = re.sub(r"-(\w)", r"\1", word)
        outlist.append(word)
    return outlist


def dehyphenate(word: str):
    outlist = [word]
    if "-" in word:
        subwords = word.split("-")
        outword = f'{subwords[0]}{"".join([x.lower() for x in subwords[1:]])}'
        # for 
        # word = re.sub(r"-(\w)", r"\1", word)
        outlist.append(outword)
    return outlist

    


def get_pages_wiktionary_de(url: str, file: TextIOWrapper):
    page= requests.get(url)
    # print(page.content)
    soup = BeautifulSoup(page.content, "html.parser")
    # print(soup)
    cont = soup.find("div", class_="mw-content-ltr mw-parser-output").children
    words=[]
    looking_for_start = True
    for child in cont:
        # print(type(child))
        # break
        if looking_for_start:
            if child.name == u"h2":
                looking_for_start = False
            continue
                # if child.findall
        if child.name == u"p":
            # print(child)
            # _ = [file.writelines(ls) for ls in [dehyphenate(el.text) for el in child.find_all_next("a", class_="new")]]
            _ = [[file.write(f'{word}\n') for word in words if len(word) >= 3] for words in [dehyphenate(el.text) for el in child if el.name == u"a"]]
            # EQUIVALENT TO:
            # for word in child.find_all_next("a", class_="new"):
            #     words = dehyphenate(word.text)
            #     for word in words:
            #         file.write(f'{word}\n')

def scrape_wiktionary_german():
    urls = [
            "https://de.wiktionary.org/wiki/Verzeichnis:Deutsch/Anglizismen",
            "https://de.wiktionary.org/wiki/Verzeichnis:Deutsch/Arabismen",
            "https://de.wiktionary.org/wiki/Verzeichnis:Deutsch/Gallizismen",
            "https://de.wiktionary.org/wiki/Verzeichnis:Deutsch/Hispanismen",
            "https://de.wiktionary.org/wiki/Verzeichnis:Deutsch/Chinesische_W%C3%B6rter_in_der_deutschen_Sprache",
            "https://de.wiktionary.org/wiki/Verzeichnis:Deutsch/Japanische_W%C3%B6rter_in_der_deutschen_Sprache",
            "https://de.wiktionary.org/wiki/Verzeichnis:Deutsch/Romanismen",
            "https://de.wiktionary.org/wiki/Verzeichnis:Deutsch/Slawismen"
            ]
            
    FILENAME="data\\loanwords\\german_loanwords.tsv"
    # wipe
    with open(FILENAME, 'w'): pass
    # write
    with open(FILENAME, "a", encoding="utf-8") as lwlist:
        for url in urls:
            output = get_pages_wiktionary_de(url, lwlist)
    # remove duplicates
    with open(FILENAME, "r", encoding="utf-8") as f:
        loanwords = f.readlines()
    with open(FILENAME, "w", encoding="utf-8") as f:
        f.writelines(sorted(list(set(loanwords))))

def get_pages_wiktionary_fr(url: str, file: TextIOWrapper):
    page= requests.get(url)
    # print(page.content)
    soup = BeautifulSoup(page.content, "html.parser")
    # print(soup)
    cont = soup.find("div", class_="mw-category mw-category-columns")
    # print(cont)
    words=[]
    for child in cont.descendants:
        # print(child.get_text())
        # print(child.name)
        if child.name == u"a":
            print(child.string)
            file.write(f'{child.string}\n')

def scrape_wiktionary_french():
    urls = ["https://en.wiktionary.org/wiki/Category:French_terms_borrowed_from_English",
            "https://en.wiktionary.org/w/index.php?title=Category:French_terms_borrowed_from_English&pagefrom=CHAT%0Achat#mw-pages", 
            "https://en.wiktionary.org/w/index.php?title=Category:French_terms_borrowed_from_English&pagefrom=GEEK%0Ageek#mw-pages",
            "https://en.wiktionary.org/w/index.php?title=Category:French_terms_borrowed_from_English&pagefrom=MISTAKE%0Amistake#mw-pages",
            "https://en.wiktionary.org/w/index.php?title=Category:French_terms_borrowed_from_English&pagefrom=SCOTCH%0Ascotch#mw-pages",
            "https://en.wiktionary.org/w/index.php?title=Category:French_terms_borrowed_from_English&pagefrom=VICTORIAVILLE%0AVictoriaville#mw-pages",
            "https://en.wiktionary.org/wiki/Category:French_terms_borrowed_from_German",
            "https://en.wiktionary.org/wiki/Category:French_terms_borrowed_from_Russian",
            "https://en.wiktionary.org/wiki/Category:French_terms_borrowed_from_Persian",
            "https://en.wiktionary.org/wiki/Category:French_terms_borrowed_from_Portuguese",
            "https://en.wiktionary.org/wiki/Category:French_terms_borrowed_from_Breton",
            "https://en.wiktionary.org/wiki/Category:French_terms_borrowed_from_Breton",
            "https://en.wiktionary.org/wiki/Category:French_terms_borrowed_from_Ancient_Greek",
            "https://en.wiktionary.org/w/index.php?title=Category:French_terms_borrowed_from_Ancient_Greek&pagefrom=HAMAMELIS%0Ahamam%C3%A9lis#mw-pages",
            "https://en.wiktionary.org/wiki/Category:French_terms_borrowed_from_Japanese",
            "https://en.wiktionary.org/wiki/Category:French_terms_borrowed_from_Vietnamese",
            "https://en.wiktionary.org/wiki/Category:French_terms_borrowed_from_Spanish",
            "https://en.wiktionary.org/w/index.php?title=Category:French_terms_borrowed_from_Spanish&pagefrom=RENEGAT%0Aren%C3%A9gat#mw-pages",
            # "",
            # "",
            ]

    FILENAME="data\loanwords\_french_loanwords.tsv"
    # wipe
    with open(FILENAME, 'w'): pass
    # write
    with open(FILENAME, "a", encoding="utf-8") as lwlist:
        for url in urls:
            print(f'Scraping {url}')
            output = get_pages_wiktionary_fr(url, lwlist)

if __name__ == "__main__":
    

    # TEST list behaviour
    # outlist=[]
    # a_list =['Video-Editor', 'Video-Film', 'Videogames', 'Video-Guide']
    # midlist=[]
    # print([dehyphenate(word) for word in a_list])
    # temp = [midlist.extend(ls) for ls in [dehyphenate(word) for word in a_list]]
    # outlist.extend(midlist)
    # print(outlist)
    # print(dehyphenate("Gönnungs-Meister"))

    scrape_wiktionary_german()
    # scrape_wiktionary_french()
    pass