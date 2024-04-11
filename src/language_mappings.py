import os
DATA_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/")


NLLB_NAMES = {
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

# GET_FILENAMES = {
#     "NLLB" : {
#         # "english": "eng_Latn",
#         "german": "dev.deu_Latn",
#         "french": "dev.fra_Latn",
#         "kurdish": "",
#         "russian": "dev.rus_Cyrl",
#         "greek": "dev.ell_Grek",
#         "farsi": "dev.pes_Arab",
#         "test": "dev.test_Latn",
#         },
# }

# filenames:
#   NLLB:
#     german: dev.deu_Latn
#     french: dev.fra_Latn
#     kurdish: 
#     russian: dev.rus_Cyrl
#     greek: dev.ell_Grek
#     farsi: dev.pes_Arab
#     test: dev.test_Latn


# AVAILABLE_LANGUAGES = {
#     # "english",
#     "german",
#     "french",
#     "kurdish",
#     "russian",
#     "greek",
#     "farsi",
# }


WORDNET_NAMES = {
    "german" : "odenet",
    
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