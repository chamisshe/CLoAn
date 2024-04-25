##################  IMPORTS  ######################
# Generic
import re
import os
import time
import json


# Visuals
from rich.style import Style
from rich.console import Console
from rich.rule import Rule
from rich.highlighter import Highlighter
from rich.prompt import Prompt
# Alternative Lookup
from rich.text import Text
import wn
import pyarabic.araby as araby

# Interactivity
import click
from typing import Optional
import questionary
import pyperclip
import pyautogui


from util.language_mappings import FLORES_NAMES, WORDNET_NAMES, ARABIC_SCRIPT #, GET_FILENAMES, AVAILABLE_LANGUAGES
from util.util import locate_lwlist,\
                        load_lwlist,\
                        load_config,\
                        load_bidict,\
                        save_config,\
                        load_position,\
                        save_position_and_pass,\
                        which_pass,\
                        find_loanwords_in_sentence,\
                        highlight_all_loanwords, \
                        detect_changes, \
                        interrupt_menu_main, \
                        interrupt_manual_replacement, \
                        load_tok_detok, \
                        interrupt_startup


# demo
from startup import launch
###################################################



# Global Variables
console = Console()
use_annotation_memory = True
remember_position = True
wipe_previous = False
find_alternatives_mode = ""

from utoken import utokenize, detokenize
tokenizer = utokenize.Tokenizer()
detokenizer = detokenize.Detokenizer()

############# STYLES ##############
from util.styles import default_select_style, interrupt_style, SENT_STYLE, MARK_LW, yellowbold, yellow_light, orange_light, magentabold
print(wn.lexicons())
wordnet = wn.Wordnet("odenet")

############# INTERRUPTS #################
from util.interrupts import *


##### DATA PATHS: ADJUST IF NECESSARY #####
SRC_FOLDER = f"{os.path.dirname(os.path.realpath(__file__))}"
DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/"))
PERSIST = os.path.abspath(os.path.join(DATA_PATH, "internal/PERSISTENCE.json"))

annotation_vars = {}

# initialise annotation memory
annotation_memory = {}





def manual_replacement(sentence: str) -> tuple[str, dict[str:str]]:
    
    # Save original sentence:
    original_sentence = sentence
    replacements = {}

    console.print(f"Sentence:", style="bold")
    console.print(sentence)
    # ASK user whether to do any manual replacement-operations at all
    try:
        choice = questionary.select(
            "\nDo you want to manually replace any other words in the current sentence?",
            choices=("YES, please.", "NO, take me to the next sentence"),
            style=default_select_style,
            use_shortcuts=True,
            default=None,
            qmark="",
        ).unsafe_ask()
    except KeyboardInterrupt:
        interrupt_menu_main()
    if choice.startswith("YES"):
        pass
    # If user does not want to do any manual replacement stuff: return the current sentence and an empty dict
    else:    
        return sentence, replacements

    ######### MANUAL REPLACEMENT #########
    # instruction = "The manual replacement of loanwords works in three ste"
    # console.print(instruction, style="yellow")
    while True:
        try:
            old_sentence = sentence
            # 1. delete
            instruction = "DELETE the word you want to replace: (you will insert its replacement in the next step)"
            console.print(instruction, style="yellow")
            intermediate_sent = edit_manual(old_sentence)
            if intermediate_sent == old_sentence:
                console.log("The sentence wasn't modified. Please try again or continue with the next sentence")
                raise ResetSentence

            deleted, position = detect_changes(old_sentence, intermediate_sent)

            # 2. insert
            instruction = yellow_light("Replacing: ") + magentabold(deleted) + "\n" + yellow_light("Now INSERT the word at the appropriate place:")
            console.print(instruction, style="yellow")
            new_sentence = edit_manual(intermediate_sent, position)
            if intermediate_sent == new_sentence:
                console.log("No alternative word was inserted. Please try again or continue with the next sentence")
                raise ResetSentence
            
            inserted, position = detect_changes(old_sent=intermediate_sent, new_sent=new_sentence)

            # 3. edit
            instruction = yellow_light("If needed, you can now edit the sentence.")
            console.print(instruction, style="yellow")
            new_sentence = edit_manual(intermediate_sent, position)
            
            # --> store difference in both operations
            replacements[deleted] = inserted
            choice = questionary.select(
                "Do you want to make any further changes to the sentence?",
                choices=("YES, let me make more replacements.", "NO, take me to the next sentence"),
                style=default_select_style,
                use_shortcuts=True,
                default=None,
                qmark="",
            ).unsafe_ask()
            sentence = new_sentence
            if choice.startswith("YES"):
                continue
            else:    
                break
        except ResetSentence:
        # continue the while loop when the user just wants to retry the current edit
            continue
        except SaveAndMoveOn:
        # break the whileloop, and continue save results
            break
            

    print(replacements)
    annotation_memory.update(replacements)

    return sentence, replacements


def edit_manual(sentence: str, position=False)-> str:
    """
    Generate alternatives for a given loanword using WordNet.
    Let the user choose any number of suitable alternatives.

    Parameters
    ----------
    loanword : str
        A loanword

    Returns
    -------
    """
    pyperclip.copy(sentence)
    pyautogui.hotkey("ctrl", "v")
    if position:
        position = len(sentence[position:].split())
        with pyautogui.hold('ctrl'):
            pyautogui.press(["left"]*(position))
        pyautogui.press(["left"])
    
    try:
        corrected_sentence = input()
    except KeyboardInterrupt:
        interrupt_manual_replacement()
    return corrected_sentence


def edit(pre: str, selected: str, post: list[str])-> str:
    """
    Generate alternatives for a given loanword using WordNet.
    Let the user choose any number of suitable alternatives.

    Parameters
    ----------
    loanword : str
        A loanword

    Returns
    -------
    """
    # starttime = time.time()
    instruction = "The target word has been replaced. You can now edit the sentence if it's necessary.\nHit ENTER when you're done:"
    try:
        # console.log(time.time() - starttime)
        console.print(instruction, style="yellow")
        poststring = " ".join(post)
        
        sentence = pre + " " + selected + " " + " ".join(post)
        
        pyperclip.copy(sentence)
        pyautogui.hotkey("ctrl", "v")

        # for i in range(len(post)):
            # pyautogui.hotkey("ctrl", "left")
        # pyautogui.press(['left']*(len(poststring)))
        with pyautogui.hold('ctrl'):
            pyautogui.press(["left"]*(len(post)))
        pyautogui.press(["left"])
        # pyautogui.press(["left"]*(len(post)))
        # console.log(time.time() - starttime)
        corrected_sentence = input()
        return corrected_sentence
    except KeyboardInterrupt:
        raise SkipLoanword


def select_and_edit_mono(loanword: str, pre: list[str], post: list[str]) -> tuple[str, str, str] | None:
    """
    
    Returns:
    -------
    new_sentence
        the new, edited sentence
    loanword
        the original loanword
    selected_alternative
        the selected alternative for the loanword
    """
    post_string = " ".join(post)
    pre_string = " ".join(pre)
    skip_message="-SKIP LOANWORD-"
    choices = [skip_message, "-CUSTOM INPUT-", "-DISCARD SENTENCE ALTOGETHER-"]
    
    if find_alternatives_mode == "wordnet":
        choices.extend([wordform.__str__() 
                for synset in wordnet.synsets(loanword) 
                for word in synset.words() 
                for wordform in word.forms()])
    elif find_alternatives_mode == "bi-dict":
        # under the loanword's entry in the bi_dict, get the list of alternatives 
        choices.extend(bi_dict[loanword])

    try:
        choices.extend(annotation_memory[loanword])
    except KeyError:
        pass
    if loanword in choices:
        choices.remove(loanword)
    
    instruction = "Choose the most suitable alternative for the highlighted word or replace it with a custom word - if possible:"
    try:
        console.print("Sentence:", style="bold")
        console.print(pre_string, end=" ", style=SENT_STYLE)
        console.print(loanword, style=MARK_LW, end="")
        console.print(" "+post_string, style=SENT_STYLE, end="\n\n")

        selected_alternative = questionary.select(
                message=instruction,
                style=default_select_style,
                instruction=False,
                choices=choices,
                use_shortcuts=True,
                default=None,
                qmark="",
                ).unsafe_ask()
            # flow-control:
        if selected_alternative == skip_message:
            sentence = pre_string+ " " +loanword+ " " +post_string
            console.print(Rule(style="green3"))

            return sentence, None, None
        elif selected_alternative == "-DISCARD SENTENCE ALTOGETHER-":
            raise DiscardSentence
        # custom input
        elif selected_alternative == "-CUSTOM INPUT-":
            try:
                console.print("\n")
                selected_alternative = console.input(yellowbold("Enter your proposed alternative in its lemma form. \
You can edit this in the next step.\n"))
            # Add the custom word to the annotation memory
                annotation_memory[loanword].add(selected_alternative)

            except KeyError:
                annotation_memory[loanword] = {selected_alternative}
            except KeyboardInterrupt:
                sentence = pre_string + " " + loanword + " " + post_string
                console.print(Rule(style="green3"))

                return sentence, None, None
            
        # TODO : allow user to select additional (secondary) alternatives that won't be implemented (but stored for potential later use)

        ###### EDIT SENTENCE #######
        console.print(Rule())
        try:
            # EDIT NEW SENT
            new_sentence = edit(pre_string, selected_alternative, post)
        # Catch KeyboardInterrupt during Sentence-Editing
        except SkipLoanword:
            # Just try again, basically
            return None
        
        # if all's well
        console.print(Rule(style="green3"))

        return new_sentence, loanword, selected_alternative

    except KeyboardInterrupt:
        interrupt_menu_main()
            
    
def second_pass_cli(lw_list: list[str], sentence: str, language: str) -> dict[str:str, str:dict] | None:
    """Do this and that
    
    Parameters
    ----------
    loanwords : list[str]
        A list of loanword candidates found in the current sentence.
    sentence : str
        The current sentence.
    changes_file : TextIOWrapper
        The stream of the file where the replacement operations are stored.
    loan_file : TextIOWrapper
        The stream of the file where the original sentence (containing all the loanwords) is written to.
    native_file : TextIOWrapper
        The stream of the file where the 'nativized' sentence is written to.

    
    Returns
    -------
    None
    """

    changes = {}
    return_dict = {"new_sentence":"", "changes":changes}
    try:
        sentence = tokenizer.utokenize_string(sentence)
        if lw_list:
            lw_candidates = find_loanwords_in_sentence(sentence, lw_list, abjad_match=(language in ARABIC_SCRIPT))
        else:
            lw_candidates = []
        sentlist = sentence.split()
        sentlen = len(sentlist)

        for i in range(-sentlen, 0):
            word = sentlist[i]

            # IF arabic script...
            if language in ARABIC_SCRIPT:
                # ...also match the stripped word
                stripped_word_in_sent = araby.strip_diacritics(word) in lw_candidates
            else:
                # ...set condition to false otherwise
                stripped_word_in_sent = False
            # regular condition         special case for abjads
            if word in lw_candidates or stripped_word_in_sent:
                rest = sentlist[i+1:]
                full_sent, loanword, alternative = select_and_edit_mono(loanword=word, pre=sentlist[:i], post=rest[i+1:])
                if loanword is not None:
                    changes[loanword] = alternative
                sentlist = full_sent.split()
                
        sentence = " ".join(sentlist)
        sentence, replacements = manual_replacement(sentence)
        sentence = detokenizer.detokenize_string(sentence)
        changes.update(replacements)

        return_dict["new_sentence"] = sentence
        console.log(return_dict)
        
        return return_dict
            
    except ResetSentence:
        return second_pass_cli(lw_list, sentence, language)
    except KeyboardInterrupt:
        raise ExitAnnotation


def first_pass_sentence_annotation(sentence: str, lw_list, position, marking_dict, language: str, mode="wordlist") -> dict:

    sentence = sentence.strip("\n")
    
    console.print(f'{yellowbold("Sentence")} ({(str(position))}):\n', end="")
    if mode == "wordlist" and (lw_list):
        # tokenize sentence for matching
        sentence = tokenizer.utokenize_string(sentence)
        lw_candidates = find_loanwords_in_sentence(sentence, lw_list, abjad_match=(language in ARABIC_SCRIPT))
        highlight_all_loanwords(sentence, lw_candidates, abjad=(language in ARABIC_SCRIPT))
    # UNIMPLEMENTED
    elif mode.lower() in {"ce", "competing_entropies", "compents", "competingentropies"}:
        sentence = tokenizer.utokenize_string(sentence)
        console.print(sentence)
        lw_candidates = None
        # TODO: find loanword candidates by using a competing entropies model

    else:
        console.print(sentence)
        lw_candidates = None
    # console.log("marking_dict : ",marking_dict)
    marking_dict[str(position)] = {"sentence": sentence,"candidates":lw_candidates}
    
    choices = {"Obvious loanwords":"contains-LW",
                "Named Entities" : "contains-NE",
                "Code-switching": "contains-CS"}
    try:
        user_choices = questionary.checkbox(
        message="(multiselect) Does the following sentence contain one or multiple instances of: ",
        style=default_select_style,
        choices=choices.keys(),
        default=None,
        qmark="",
    ).unsafe_ask()
    except KeyboardInterrupt:
        interrupt_menu_main()
    # console.log(user_choices)
    for choice, abbr in choices.items():
        if choice in user_choices:
            marking_dict[str(position)][abbr] = True
        else:
            marking_dict[str(position)][abbr] = False
    # finally:
    return marking_dict

def first_pass(language: str,
                corpus_name: str,
                corpus_path: str,
                file_path: str,
                lw_list: list[str]) -> dict:
    ######### LOAD SENTENCES
    sents_path = os.path.join(corpus_path,file_path)
    if not os.path.exists(os.path.abspath(f'{DATA_PATH}/marking')):
        os.makedirs(f'{DATA_PATH}/marking')
    marking_file = os.path.abspath(os.path.join(DATA_PATH,f'marking/_marking{corpus_name}_{language}.json'))

    # Read sentences from file to list
    with open(sents_path, "r", encoding="utf-8") as sentfile:
        sentences = sentfile.readlines()
    num_sentences = len(sentences)

    # Get first-pass data
    try:
        with open(marking_file, 'r', encoding="utf-8") as f:
            marking_dict = json.load(f)
    except FileNotFoundError: 
        marking_dict = {} 
    except json.decoder.JSONDecodeError:
        marking_dict = {}
    if type(marking_dict) is not dict:
        marking_dict = {}
        
    # PERSISTENCE
    if remember_position:
        position = load_position(language, num_sentences)
        # console.log(position)
        n_pass = 1


    ##############################################
    ############ FIRST PASS MAIN #################
    console.log("1st pass:")
    idx = position
    try:
        console.log("Starting iteration")
        for sentence in sentences[position:]:
            # console.log("first iteration")
            try:
                marking_dict = first_pass_sentence_annotation(sentence, lw_list, position, marking_dict, language)
            except ResetSentence:
                console.log("ResetSentence")
                pass
            except DiscardSentence:
                console.log("DiscardSentence")
                pass
            
            position += 1

        # if run all the way through the end of the file, set pass-var to 2nd pass, reset position to start of file (0)
        n_pass = 2
        position = 0

    # EXITING:
    except ExitAnnotation:
        # progress saving that has to be done inside the current function (access to variables)
        if remember_position:
            console.print("saving position")
            save_position_and_pass(language=language, position=position, n_pass=n_pass)
        with open(marking_file, 'w', encoding="utf-8") as f:
            console.log("Saving marking dict")
            # console.log(marking_dict)
            json.dump(marking_dict, f, indent=4, separators=(',', ': '))
        # propagate the error upwards
        raise ExitAnnotation

    # regular exiting: save everything
    if remember_position:
        console.print("saving position")
        save_position_and_pass(language=language, position=position, n_pass=n_pass)
    with open(marking_file, 'w', encoding="utf-8") as f:
        console.log("Saving marking dict")
        console.log(marking_dict)
        json.dump(marking_dict, f, indent=4, separators=(',', ': '))
    return marking_dict

def second_pass_extracting(language: str,
                           corpus_name: str,
                        corpus_path: str,
                        file_path: str,
                        lw_list: list[str],
                        first_pass_markings: dict):

    ##### FILENAMES #####
    annmem_path = f'{DATA_PATH}internal/annotation_memory-{language}.json'
    marking_file = os.path.abspath(f'{DATA_PATH}/marking/_marking{corpus_name}_{language}.json')
    output_file = os.path.abspath(f"{DATA_PATH}/output/OUT_{corpus_name}_{language}.json")
    # console.log("fpm: ", first_pass_markings)
    if first_pass_markings == {}:
        with open(marking_file, 'r', encoding="utf-8") as f:
            first_pass_markings = json.load(f)
        if first_pass_markings == {}:
            console.log("Marking file empty; redirecting you to mark the corpus again (first pass)")
            first_pass_markings = first_pass(language=language, lw_list=lw_list,corpus_name=corpus_name, corpus_path=corpus_path,file_path=file_path)
        elif type(first_pass_markings) is not dict:
            console.log("The marking file does not contain a valid dictionary; redirecting you to mark the corpus again (first pass)")
            first_pass_markings = first_pass(language=language, lw_list=lw_list, corpus_name=corpus_name, corpus_path=corpus_path,file_path=file_path)
    results = {}
    
    num_sentences = len(first_pass_markings)

    ########### PERSISTENCE ########### 
    # If you want your annotation to continue from where you last left off:
    if remember_position:
        position = load_position(language, num_sentences)
    

    ########### SET ALTERNATIVE-FINDING-MODE ############
    config = load_config()
    
    global find_alternatives_mode
    find_alternatives_mode = config["find_alternatives"][language]
    # use WORDNET to find alternatives
    if find_alternatives_mode == "wordnet":
        if language in WORDNET_NAMES.keys():
            global wordnet
            wordnet = wn.Wordnet(WORDNET_NAMES[language])
            console.log("Using the following WordNets: ", wordnet.lexicons())
        else:
            console.log(f"Found no Wordnet-lexicon for {language}.")
            find_alternatives_mode = "wordnet"
        # MAYBE TODO : wordnet download menu
        # console.print(f"The following are available wordnet lexica that can be downloaded")
    # use BILINGUAL-DICT to find alternatives
    elif find_alternatives_mode == "bi-dict":
        global bi_dict
        bi_dict = load_bidict(language)


    ############ FILE HYGIENE ############
    # if wipe_previous:
    #     pass

    ######## LOAD ANNOTATION MEMORY ########
    if use_annotation_memory:
        console.log("Using annotation memory")

        try:
            global annotation_memory
            with open(annmem_path, "r", encoding="utf-8") as am:
                _annotation_memory = json.load(am)
            for lw, alt_list in _annotation_memory.items():
                annotation_memory[lw] = set(alt_list)

            # console.log(annotation_memory)
        except FileNotFoundError:
            console.log("No file containing an Annotation-Memory could not be found.\nCreating file and starting annotation with an empty Annotation-Memory.")
            
        except json.decoder.JSONDecodeError:
            console.log("A file for the Annotation-Memory was found, but didn't contain a valid store.\nStarting annotation with an empty Annotation-Memory.")

    ########################################
    ########## SECOND-PASS MAIN ############
    console.print(Rule(title=f"SECOND PASS", characters="#", style="orange1"))
    console.print(Rule(style="orange1"))

    idx = position
    # iterate through markings-dict (by accessing it via keys)
    while idx < len(first_pass_markings)-1:
    # for idx in range(position, len(first_pass_markings)-1):
        try:
        # for idx,marking in first_pass_markings.items():
            console.log(f"Skipping Sentence {idx}")
            marking = first_pass_markings[str(idx)]
            if marking["contains-LW"]:
                lw_candidates = marking["candidates"]
                # console.print(yellowbold("Sentence"),f'({(str(idx))}):')
                console.print(Rule(title=f"Sentence {idx}",characters="#", style="spring_green3"))
                sentence = marking["sentence"]
                single_result = second_pass_cli(lw_candidates, sentence, language)
                
                single_result["original_sentence"] = detokenizer.detokenize_string(sentence)
                console.log(single_result)
                # only save if the new sentence differs from the original one
                if single_result["original_sentence"] != single_result["new_sentence"]:
                    results[str(idx)] = single_result
                pass
                idx += 1
                console.log(idx)
            else:
                idx += 1
                continue
        except ResetSentence:
            continue
        except DiscardSentence:
            console.log("Raised DiscardSentence")

            idx += 1
            continue
        except ExitAnnotation:
            console.print("Exiting Annotation", end="\n", style="red bold")
            with console.status("",spinner="simpleDots"):
                time.sleep(.5)
            break

    # EXITING:
    if remember_position:
        console.log("saving position")
        # console.log(position)
        save_position_and_pass(language=language, position=idx, n_pass=2)
    with open(output_file, 'w', encoding="utf-8") as f:
        console.log("Saving results in:\n",yellow_light(output_file))
        # console.log(results)
        json.dump(results, f, indent=4, separators=(',', ': '))
    return results



def annotate_wrapper(language: str,
             corpus_name: str,
             corpus_path: str,
             file_path: str,
             remember_position: bool=True,
             wipe_previous: bool=False,
             load_and_save_annotation_memory: bool=True,
             full_match_only: bool=True):
    """"""
    ############### PATHS ###############
    # lw_path = f'{DATA_PATH}loanwords/{language}_loanwords.tsv'
    if not os.path.exists(f'{DATA_PATH}/output'):
        os.makedirs(f'{DATA_PATH}/output')
    
    output = f'{DATA_PATH}output/RESULTS_{language}.json'


    #######################################
    ######## LOADING LOANWORD-LIST ########
    try:
        lwlist = load_lwlist(language)
        console.log("loaded Loanword-list")
    except FileNotFoundError:
        console.log(f"Couldn't find a list of loanwords for {language}")
        options = ["YES, continue without loanword-list", "NO, locate loanword-list"]
        choice = questionary.select(
            f"Do you want to annotate the sentences {language.capitalize()} without a list of loanwords?\nYou'll have to identify and replace the loanwords yourself.",
            choices=options,
            style=default_select_style,
        ).ask()
        if choice == options[0]:
            lwlist = set()
            # use_lwlist = False
        else:
            filename = locate_lwlist()
            # save filename to config
            config = load_config()
            config["wordlists"][language] = filename
            save_config(config)
            lwlist = load_lwlist(lwlist_path=f'{DATA_PATH}loanwords/{filename}')
            # use_lwlist = True
    # console.log(lwlist)
    # Get from persistence-store: do first or second pass
    n_pass = which_pass(language)
    console.log(f'n-pass: {n_pass}')
    # would also catch a value outside of (1, 2) --> defaults to doing a Firstpass
    first_pass_markings = {}
    try:
        if n_pass != 2:
            first_pass_markings = first_pass(language,corpus_name, corpus_path,file_path,lw_list=lwlist)
        second_pass_extracting(language=language,
                           corpus_name=corpus_name,
                           corpus_path=corpus_path,
                           first_pass_markings=first_pass_markings,
                           file_path=file_path,
                           lw_list=lwlist)
    # graceful exiting
    except ExitAnnotation:
        console.print("Exiting Annotation", end="\n", style="red bold")
        with console.status("",spinner="simpleDots"):
            # to reassure the user into thinking it's doing a lot here, get tricked lol
            time.sleep(.5)


@click.command()
@click.option("--corpus", "-c", type=str)
@click.option("--lang", "-l", type=str)
@click.option("--mode", "-m", type=str)
def main(corpus, lang, mode="WordNet"):
    # check given (in command-line) and get missing arguments needed for annotation:
    # - Language name (may be passed when calling the script)
    # - Name of the corpus (may be passed when calling the script)
    # - Path where the corpus' files are located
    # - Filename of the corpus' language specific file
    while True:
        try:
            lang, corpus_name, corpus_path, file_path = launch(corpus=corpus, lang=lang)
            break
        except KeyboardInterrupt:
            try:
                interrupt_startup()
            except ResetSentence:
                continue
            except ExitAnnotation:
                console.print("Exiting Annotation", end="\n", style="red bold")
                with console.status("",spinner="simpleDots"):
                    time.sleep(.5)
                return
            continue
    # load tokenizer, detokenizer globally. (need language code for that)
    global tokenizer, detokenizer
    tokenizer, detokenizer = load_tok_detok(lang)
    # Start annotating.
    annotate_wrapper(lang, corpus_name, corpus_path, file_path)
    # console.log(corpus)
    # console.log(lang)
    pass


if __name__ == "__main__":
    main()
