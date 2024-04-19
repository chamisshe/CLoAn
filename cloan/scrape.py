from bs4 import BeautifulSoup
from io import TextIOWrapper
import requests
import re


def dehyphenate(word: str):
    outlist = [word]
    if "-" in word:
        word = re.sub(r"-(\w)", r"\1",word)
        outlist.append(word)
    return outlist



def get_pages_wiktionary(url: str, file: TextIOWrapper):
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
                # if child.findall
        if child.name == u"p":
            # _ = [file.writelines(ls) for ls in [dehyphenate(el.text) for el in child.find_all_next("a", class_="new")]]
            _ = [[file.write(f'{word}\n') for word in words if len(word) >= 3] for words in [dehyphenate(el.text) for el in child.find_all_next("a", class_="new")]]
            # EQUIVALENT TO:
            # for word in child.find_all_next("a", class_="new"):
            #     words = dehyphenate(word.text)
            #     for word in words:
            #         file.write(f'{word}\n')

if __name__ == "__main__":
    urls = ["https://de.wiktionary.org/wiki/Verzeichnis:Deutsch/Anglizismen","https://de.wiktionary.org/wiki/Verzeichnis:Deutsch/Arabismen", "https://de.wiktionary.org/wiki/Verzeichnis:Deutsch/Gallizismen", "https://de.wiktionary.org/wiki/Verzeichnis:Deutsch/Hispanismen","https://de.wiktionary.org/wiki/Verzeichnis:Deutsch/Japanische_W%C3%B6rter_in_der_deutschen_Sprache", "https://de.wiktionary.org/wiki/Verzeichnis:Deutsch/Romanismen", "https://de.wiktionary.org/wiki/Verzeichnis:Deutsch/Slawismen"]
    
    FILENAME="4 - CDA - Contrastive Dataset Annotator/lw-de.tsv"

    # TEST list behaviour
    # outlist=[]
    # a_list =['Video-Editor', 'Video-Film', 'Videogames', 'Video-Guide']
    # midlist=[]
    # print([dehyphenate(word) for word in a_list])
    # temp = [midlist.extend(ls) for ls in [dehyphenate(word) for word in a_list]]
    # outlist.extend(midlist)
    # print(outlist)

    with open(FILENAME, 'w'): pass
    with open(FILENAME, "a", encoding="utf-8") as lwlist:
        for url in urls:
            output = get_pages_wiktionary(url, lwlist)
            # print(output)
        # break
    pass