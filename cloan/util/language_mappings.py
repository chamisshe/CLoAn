import os
DATA_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/")


FLORES_NAMES = {
    "english" : "eng_Latn",
    "en" : "eng_Latn",
    "german" : "deu_Latn",
    "deutsch" : "deu_Latn",
    "de" : "deu_Latn",
    "test" : "test_Latn",
}

#            1:LANGUAGE
# 0:MODEL   | english      | german       |
# ----------| ----------------------------|
#   NLLB    | dev.eng_Latn | dev.deu_Latn |
#           |

# with open(f'{DATA_PATH}config.yml', "r", encoding="utf-8") as f:

ARABIC_SCRIPT = {
    "farsi",
    "kurdish-central"
}

WORDNET_NAMES = {
    "german" : "odenet",
    "french" : "omw-fr",
    "test" : "odenet",
}

NAME_TO_ISO3CODE = {
    "english":"eng",
    "german":"deu",
    "test":"deu",
    "kurdish-central":"ckb",
    "french":"fra",
    "greek" : "ell",
    "russian" : "rus",
    "farsi" : "fas",
}


DEFAULT_NAMES = {
    # ENGLISH
    "english" : "english",
    "en" : "english",
    "eng" : "english",
    "stan1293" : "english",
    # GERMAN
    "german" : "german",
    "deutsch" : "german",
    "ger" : "german",
    "deu" : "german",
    "de" : "german",
    "stan1295" : "german",
    # KURDISH
    "kurdish" : "kurdish",
    "ku" : "kurdish",
    "kur" : "kurdish",
    "kurd1259" : "kurdish",
    "ckb" : "kurdish",
    # GREEK
    "greek" : "greek",
    "el" : "greek",
    "ell" : "greek",
    "gre" : "greek",
    "ellinika": "greek",
    "elliniká": "greek",
    "ελληνικά": "greek",
    "gree1276" : "greek",
    # FRENCH
    "french" : "french",
    "francais" : "french",
    "français" : "french",
    "french" : "french",
    "fr" : "french",
    "fra" : "french",
    "fre" : "french",
    "stan1290" : "french",
    # FARSI
    "farsi": "farsi",
    "persian": "farsi",
    "fa": "farsi",
    "fas": "farsi",
    "per": "farsi",
    "fars1254": "farsi",
    # RUSSIAN
    "russian" : "russian",
    "ru" : "russian",
    "rus" : "russian",
    "русский" : "russian",
    "russ1263" : "russian",
    # TEST
    "test" : "test",
}