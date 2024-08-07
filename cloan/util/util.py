import re
import os
import yaml
from utoken import utokenize
from utoken import detokenize

import sqlite3
import wn

import pyarabic.araby as araby # this will remove diacritics which are optional in writing in Abjad scripts

from rich.console import Console
from rich.rule import Rule
import questionary
import json
import time
from util.styles import default_select_style, interrupt_style, SENT_STYLE, MARK_LW, yellowbold, yellow_light, orange_light
from util.interrupts import *
from util.language_mappings import NAME_TO_ISO3CODE, ARABIC_SCRIPT, WORDNET_NAMES
console = Console()

tok = utokenize.Tokenizer()  # Initialize tokenizer, load resources later
detok = detokenize.Detokenizer()  # Initialize tokenizer, load resources later

ROOT = os.path.abspath(os.path.join( os.path.dirname(__file__), "../.."))
ROOT = os.path.join(os.getcwd(), "..")
console.log(ROOT)
DATA_PATH = os.path.abspath(os.path.join(ROOT, "data/"))
console.log("Data path =",DATA_PATH)
PERSIST = os.path.abspath(os.path.join(DATA_PATH, "internal/PERSISTENCE.json"))



##### TOKENIZING / DETOKENIZING ###############
def load_tok_detok(lang: str) -> tuple[utokenize.Tokenizer,detokenize.Detokenizer]:
    code = NAME_TO_ISO3CODE[lang]
    global tok, detok
    tok = utokenize.Tokenizer(lang_code=code)  # Initialize tokenizer, load resources
    detok = detokenize.Detokenizer(lang_code=code)
    return tok, detok
###############################################


######## LOAD WORDNET ##############################
def load_wordnet(lang: str):
    if lang not in WORDNET_NAMES.keys():
        return None
    wn_name = WORDNET_NAMES[lang]
    try:
        wordnet = wn.Wordnet(wn_name)
    except sqlite3.OperationalError:
        wn.download(wn_name)
        wordnet = wn.Wordnet(wn_name)
    return wordnet

def use_wordnet(lang: str):
    answer = ""
    if answer.startswith("YES"): return True
    else: return False
###############################################


##### ANNOTATION MEMORY #######################
def update_annmem(annotation_memory: dict[str, dict[str, set[str]]],
                       replacements: dict[str, str])  -> dict[str, dict[str, set[str]]]:
    """Update the bidirectional annotation memory.

    Parameters
    -
    annotation_memory : the annotation memory.
    replacements : a dictionary containing mappings in the following format:
        {loanword : native}
    """
    for loan,native in replacements.items():
        try:
            annotation_memory["loan-native"][loan].add(native)
        except KeyError:
            annotation_memory["loan-native"][loan] = {native}
        
        try:
            annotation_memory["native-loan"][native].add(loan)
        except KeyError:
            annotation_memory["native-loan"][native] = {loan}
    # console.log(annotation_memory)
    return annotation_memory

def save_annmem(annmem, path):
    # initialize output dictionary (avoiding in-place modification)
    out_annmem = {"loan-native" : {}, "native-loan" : {}}
    
    # Convert all sets to lists
    for lw,alt_set in annmem["loan-native"].items():
        out_annmem["loan-native"][lw] = list(alt_set)
    for lw,alt_set in annmem["native-loan"].items():
        out_annmem["native-loan"][lw] = list(alt_set)

    # console.log(out_annmem)
    
    with open(path, 'w', encoding="utf-8") as am:
        json.dump(out_annmem, am)
###############################################


##### MANUAL EDITING ##########################
def detect_changes(old_sent: str, new_sent: str):
    start = 0
    if old_sent == new_sent:
        pass

    for i,(a,b) in enumerate(zip(old_sent, new_sent)):
        if a != b:
            start = i
            break
    for i, (a,b) in enumerate(zip(old_sent[::-1], new_sent[::-1]), ):
        if a != b:
            stop = -i
            break
    # print(start,stop)
    if len(old_sent) > len(new_sent):
        stop = - len(new_sent)
        return old_sent[start:stop], stop
    else:
        stop = - len(old_sent)
        return new_sent[start:stop], stop
###############################################

######## OUTPUT ##########
def load_prev_output(path):
    try:
        with open(path, 'r', encoding="utf-8") as f:
            # console.log("found existing output file")
            results = json.load(f)
    except FileNotFoundError:
        results = {}
    except json.decoder.JSONDecodeError:
        results = {}

    return results
###############################################


###############################################
################# PERSISTENCE #################
def start_annotating_from_sent_x(num_sents) -> int:

    # which line
    userinput = input(f'From which sentence onward would you like to start working?\n(Valid range: 0 - {num_sents-1})')
    try:
        number = int(userinput)
        if number > num_sents:
            print(f'Your input ({userinput}) exceeds the number of available sentences.\nPlease pass in a value lower than {num_sents}.')
            number = start_annotating_from_sent_x(num_sents)
    except ValueError:
        print(f'{userinput} cannot be converted to an Integer.\nPlease only enter digits')
        number = start_annotating_from_sent_x(num_sents)
    return number


def persistence_load(language, corpus_name, num_sentences) -> int:
    try:
        # open the memory file, load the saved position for the current language
        with open(PERSIST, "r", encoding="utf-8") as f:
            persistence = json.load(f)
            # console.log("opened persistence file")
        
        position = persistence[corpus_name][language]["position"]
        # console.log(position)
        # if a file has already been passed through completely:
        if position >= num_sentences:
            # Ask the user whether they want to reannotate the whole process again
            choice = questionary.select(
                "You've already fully annotated this corpus\nDo you really want to go through it again?",
                choices=("yes","no", "yes, but only from a certain line onwards")).ask()
            if choice == "no":
                print("Exiting...")
                time.sleep(1.0)
            elif choice == "yes, but only from a certain line onwards":                    
                position = start_annotating_from_sent_x(num_sentences)        
            else:
                position=0
        return position
    except FileNotFoundError:
        print("Memory-file could not be found.\nInitialising memory, and starting annotation from the start of the selected file.")
        persistence = {}
        position = 0
        persistence[corpus_name] = {language : {"position": position, "time": 0.} }
    except json.decoder.JSONDecodeError:
        print("Memory-file was found, but didn't contain a valid store.\nInitialising memory, and starting annotation from the start of the selected file.")
        persistence = {}
        position = 0
        persistence[corpus_name] = {language : {"position": position, "time": 0.} }
    # File exists, but "language" has no entry yet 
    except KeyError:
        position = 0
        try:
            persistence[corpus_name][language] = {"position": position, "time": 0.}
        except KeyError:
            persistence[corpus_name] = {language : {"position": position, "time": 0.} }
    return position


def persistence_save(language, corpus_name, position, time: float=0.):
    # save file position
    try:
        with open(PERSIST, "r", encoding="utf-8") as f:
            memory = json.load(f)
    except json.decoder.JSONDecodeError:
        memory = {corpus_name : { language : {"position": position, "time": time}}}
    try:
        memory[corpus_name][language]["position"] = position
        memory[corpus_name][language]["time"] += time
    except KeyError:
        try:
            memory[corpus_name][language] = {"position": position, "time": time}
        except KeyError:
            memory[corpus_name] = { language : {"position": position, "time": time}}
    # console.log(memory)
    with open(PERSIST, 'w', encoding="utf-8") as f:
        json.dump(memory, f)
    # console.log("Saved current position")
###############################################



###############################################
################# CONFIG ######################
def load_config():
    config_path = os.path.abspath(os.path.join(DATA_PATH, ".config/config.yml"))
    # console.log(config_path)
    console.log(config_path)
    with open(config_path, 'r', encoding='utf-8') as f:
        config_dict = yaml.safe_load(f)
    return config_dict
        

def save_config(config_dict):
    config_path = os.path.abspath(os.path.join(DATA_PATH, ".config/config.yml"))
    with open(config_path, "w", encoding="utf-8") as config_stream:
        yaml.dump(config_dict, config_stream)
###############################################



###############################################
############# LOADING LOANWORDS ###############
def load_lwlist(language=str) -> set:
    try:
        filename = load_config()["wordlists"][language]
        if filename == None:
            return set()
    except KeyError:
        raise FileNotFoundError
    lwlist_path = os.path.abspath(os.path.join(DATA_PATH, "loanwords", filename))
    with open(lwlist_path, "r", encoding="utf-8") as lwfile:
        # ASSUMES FORMAT: 
        #   {   LOANWORD1 : {other_info},
        #       LOANWORD2 : {...},
        #       ... }
        if lwlist_path.endswith(".json"):
            lwdict = json.load(lwfile)
            # we only really need the
            lwlist = set([kvpair[0] for kvpair in lwdict.items()])
        elif lwlist_path.endswith(".tsv"):
            lwlist = set(lwfile.read().split("\n"))
            # Remove empty string
            try:
                lwlist.remove("")
            except ValueError:
                pass
    return lwlist

def load_bidict(language=str) -> dict:
    lw_dict_path = os.path.abspath(os.path.join(f'{DATA_PATH}/loanwords/',load_config()["wordlists"][language]))
    with open(lw_dict_path, "r", encoding="utf-8") as f:
        lwdict = json.load(f)
    # possible keynames: 
    # - "equiv"
    # - "alt"
    # - "alternative"
    # in the first loanword's values, get all the key-names
    possible_keynames = tuple(lwdict.items())[0][1].keys()
    # set the keyname
    if "equiv" in possible_keynames: keyname = "equiv"
    if "alt" in possible_keynames: keyname = "alt"
    if "alternative" in possible_keynames: keyname = "alternative"

    # create the bi-lingual dictionary in the following format:
    #   {LOANWORD1  : [ALT1, ALT2],
    #    LOANWORD2  : [ALT1, ALT2],
    #   ... }
    bi_dict = {lw:val[keyname] for lw,val in lwdict.items()}
    return bi_dict

def locate_lwlist():
    LWLISTS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/loanwords"))
    try:
        console.print(Rule())
        console.print(f"Locating loanword-list\nMake sure your file is located in the following directory: ")
        console.print(f"\n    {orange_light(LWLISTS_PATH)}\n")

        # ask the user to enter the directory-path
        filename = console.input(yellow_light("Please enter the name of your file:\n"))
        file_fullpath = os.path.join(LWLISTS_PATH, filename)

        # Check 1: file exists and is a file (not a directory)
        assert os.path.isfile(file_fullpath)
        
        # PREVIEW
        with open(file_fullpath, "r", encoding="utf-8") as f:
            for i in range(5):
                console.print(yellow_light(f'{str(i)}\t'),f.readline().strip("\n"))
        # USER: confirm file
        user_feedback = questionary.select(
            "These are the first few lines of the file you entered. Is this the right file?",
            choices=["YES, continue to annotation.", "NO, choose another."],
            style=default_select_style,
        ).ask()
        
        # Check 2: user actually wants this file
        assert user_feedback == "YES, continue to annotation."
        
        return filename
    # If the checks fail, let the user know he failed tragically. 
    # then try again.
    except AssertionError:
        console.print(Rule(style="red"))
        console.print("Hmm, something didn't quite go right. Let's try again:")
        return locate_lwlist()
###############################################



###############################################
############# MATCHING LOANWORDS ###############
def diacriticagnostic_matching(sentence: str, lw_list: set|list) -> set:
    matches = []
    # precompute the "stripped sentence" instead of stripping the sentence with each lw we're checking
    # console.log("type(sentence) ", type(sentence))
    sentence_stripped = araby.strip_diacritics(sentence)
    for lw in lw_list:
        if (lw in sentence) or (lw in sentence_stripped):
            matches.append(lw)
        elif araby.strip_diacritics(lw) in sentence or araby.strip_diacritics(lw) in sentence_stripped:
            matches.append(araby.strip_diacritics(lw))
    return matches


def find_loanwords_in_sentence(sentence: str, lw_list: list[str] | set[str], full_match_only: bool=True, abjad_match: bool=False):
    found_words = []
    if abjad_match:
        found_words = diacriticagnostic_matching(sentence, lw_list)
    else:
        for lw in lw_list:
            lw = lw.strip("\n")
            # only match full
            if full_match_only:
                lw = f' {lw} '
            # ^ not necessary, i think?
            if lw in sentence:
                lw = lw.strip()
                found_words.append(lw)
            elif lw.lower() in sentence:
                found_words.append(lw.lower())
    return found_words


def highlight_all_loanwords(sentence, lw_candidates: list|set, abjad: bool=False):

    # console.log(tok.lang_code)
    full_sentence = sentence.split()
    # console.log(all_words)
    sent_so_far = ""
    if abjad:
        for word in full_sentence:
            # is NOT a lw-candidate
            if (word not in lw_candidates) and (araby.strip_diacritics(word) not in lw_candidates):
                sent_so_far = f'{sent_so_far}{word} '
            # IS a lw-candidate
            else:
                console.print(sent_so_far,end="")
                console.print(word, style=MARK_LW, end="")
                sent_so_far = " "
    else:
        for word in full_sentence:
            # is NOT a lw-candidate
            if word not in lw_candidates and word.lower() not in lw_candidates:
                sent_so_far = f'{sent_so_far}{word} '
            # IS a lw-candidate
            else:
                console.print(sent_so_far,end="")
                console.print(word, style=MARK_LW, end="")
                sent_so_far = " "
    console.print(sent_so_far)
##################################################



########################################
########### INTERRUPT MENUS ############
def interrupt_menu_main():
    options = ["RESTART annotation of the current sentence (already made annotations for this sentence will be lost)", "DISCARD the current Sentence, continue with the next one", "GO BACK to the previous sentence", "QUIT the annotation process."]
    try:
        console.clear()
        console.print("\n", Rule(style="red", characters="#"))
        choice = questionary.select(
            "What do you want to do?",
            instruction="",
            style=interrupt_style,
            choices=options,
            use_shortcuts=True,
            default=None,
            pointer=f'>>',
            ).unsafe_ask()
    # In case of an additional press of CTRL+C, assume the annotator wants to quit the annotation process
    except KeyboardInterrupt:
        raise ExitAnnotation
    
    # 1: RESTART sentence
    if choice == options[0]:
        raise ResetSentence
    # 2: DISCARD sentence
    elif choice == options[1]:
        raise DiscardSentence
    # 3: Go back 1 sentence
    elif choice == options[2]:
        raise PreviousSentence
    # 4: EXIT annotation
    elif choice == options[3]:
        raise ExitAnnotation


def interrupt_startup():
    options = ["TRY startup AGAIN.", "EXIT annotation (already?!)"]
    try:
        # console.print(Rule(title="Keyboard Interrupt", style="red", characters="#"))
        console.clear()
        console.print("\n", Rule(style="red", characters="#"))
        choice = questionary.select(
            "What do you want to do?",
            instruction="",
            style=interrupt_style,
            choices=options,
            use_shortcuts=True,
            default=None,
            # show_selected=True,
            pointer=f'>>',
            ).unsafe_ask()
    # In case of an additional press of CTRL+C, assume the annotator wants to quit the annotation process
    except KeyboardInterrupt:
        raise ExitAnnotation
    
    # 1: RESTART sentence
    if choice == options[0]:
        raise ResetSentence
    # 3: EXIT annotation
    elif choice == options[1]:
        raise ExitAnnotation


def interrupt_manual_replacement():
    try:
        console.clear()
        console.print("\n", Rule(style="red", characters="#"))
        options = ["TRY AGAIN: Reset the sentence to how it was just before, do another replacement operation.","MOVE ON: continue with the next sentence, but save all previous annotations for the current sentence.","DISCARD: continue with the next sentence, but don't save any annotations for the current sentence."]
        choice = questionary.select(
            "What do you want to do?",
            instruction="",
            style=interrupt_style,
            choices=options,
            use_shortcuts=True,
            default=None,
            pointer=f'>>',
        ).unsafe_ask()
        if choice == options[0]:
            raise ResetSentence
        if choice == options[1]:
            raise SaveAndMoveOn
        if choice == options[2]:
            raise DiscardSentence
    except KeyboardInterrupt:
        raise ExitAnnotation
####################################################

if __name__ == "__main__":
    pass