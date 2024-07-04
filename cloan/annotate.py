##################  IMPORTS  ######################
# Generic
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
try:
    import pyautogui
    USE_PYAUTOGUI = True
except KeyError:
    # os.environ['DISPLAY'] = ':0'
    # import pyautogui
    USE_PYAUTOGUI = False

from util.language_mappings import FLORES_NAMES, WORDNET_NAMES, ARABIC_SCRIPT #, GET_FILENAMES, AVAILABLE_LANGUAGES
from util.util import locate_lwlist,\
                        load_lwlist,\
                        load_config,\
                        load_bidict,\
                        save_config,\
                        persistence_load,\
                        persistence_save,\
                        find_loanwords_in_sentence,\
                        highlight_all_loanwords, \
                        detect_changes, \
                        interrupt_menu_main, \
                        interrupt_manual_replacement, \
                        load_tok_detok, \
                        interrupt_startup, \
                        update_annmem, \
                        save_annmem, \
                        load_prev_output, \
                        load_wordnet


# demo
from startup import launch
###################################################



# Global Variables
console = Console()
use_annotation_memory = True
remember_position = True
wipe_previous = False
find_alternatives_mode = ""
starttime = 0.
wordnet = None

from utoken import utokenize, detokenize
tokenizer = utokenize.Tokenizer()
detokenizer = detokenize.Detokenizer()

############# STYLES ##############
from util.styles import default_select_style, interrupt_style, SENT_STYLE, MARK_LW, yellowbold, yellow_light, orange_light, magentabold

############# INTERRUPTS #################
from util.interrupts import *


##### DATA PATHS: ADJUST IF NECESSARY #####
# SRC_FOLDER = f"{os.path.dirname(os.path.realpath(__file__))}"
SRC_FOLDER = os.getcwd()
ROOT = os.path.join(os.getcwd(), "..")
SRC_FOLDER = os.path.join(os.getcwd(), "..")
console.log("src folder= ",SRC_FOLDER)
# console.log(SRC_FOLDER)
# console.log(os.getcwd())
DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/"))
DATA_PATH = os.path.abspath(os.path.join(ROOT,"data/"))
PERSIST = os.path.abspath(os.path.join(DATA_PATH, "internal/PERSISTENCE.json"))

annotation_vars = {}

# initialise annotation memory
annotation_memory = {"native-loan": {},
                     "loan-native": {}}





def manual_replacement(sentence: str, direction="replace-loans", display_menu: bool=True) -> tuple[str, dict[str:str]]:
    
    # Save original sentence:
    global annotation_memory
    original_sentence = sentence
    replacements = {}


    if direction == "replace-loans":
        msg = "\nDo you want to manually replace any other loanwords in the current sentence?"
        title = "Replacing loanwords with native words"
        # ASK user whether to do any manual replacement-operations at all
        if display_menu:
            try:
                choice = questionary.select(
                    message=msg,
                    choices=("YES, please.", "NO, take me to the next step"),
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
                console.print(Rule())
                return sentence, replacements
        
    elif direction == "replace-native":
        # msg = "\nDo you want to manually replace any other native words in the current sentence?"
        title = "Replacing native words with loanwords"


    console.print(Rule(title=title))
    console.print(f"Sentence:", style="bold")
    console.print(sentence)


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
                console.log("The sentence wasn't modified. Please try again or continue with the next sentence") #keep
                raise ResetSentence

            deleted_word, position = detect_changes(old_sentence, intermediate_sent)

            # 2. insert
            instruction = yellow_light("Replacing: ") + magentabold(deleted_word) + "\n" + yellow_light("Now INSERT the word at the appropriate place:")
            console.print(instruction, style="yellow")
            new_sentence = edit_manual(intermediate_sent, position)
            if intermediate_sent == new_sentence:
                console.log("No alternative word was inserted. Please try again or continue with the next sentence") #keep
                raise ResetSentence
            
            inserted_word, position = detect_changes(old_sent=intermediate_sent, new_sent=new_sentence)

            # 3. edit
            instruction = yellow_light("If needed, you can now edit the sentence.")
            console.print(instruction, style="yellow")
            new_sentence = edit_manual(new_sentence, position)

            # --> store difference in both operations
            replacements[deleted_word] = inserted_word
            
            # update annotation memory
            if direction == "replace-loans":
                annotation_memory=update_annmem(annotation_memory, replacements={deleted_word : inserted_word})
            elif direction == "replace-native":
                # inserted_word = loan, thus the different direction
                annotation_memory=update_annmem(annotation_memory, replacements={inserted_word : deleted_word})
        
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
        except KeyboardInterrupt:
            console.log("raised ExitAnnotation, raising another ExitAnnotation")
            raise ExitAnnotation
            
            

    # console.log(replacements)

    # update the annotation memory
    # annotation_memory = update_annmem(annotation_memory, replacements=replacements)

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

    ####### V keyboard
    # keyboard.send("ctrl+v")
    # if position:
    #     position = len(sentence[position:].split())
    #     for i in range(position):
    #         keyboard.send("ctrl+left")
    #     keyboard.send("left")

    ####### V pyautogui
    pyautogui.hotkey("ctrl", "v")
    if position:
        position = len(sentence[position:].split())
        with pyautogui.hold('ctrl'):
            pyautogui.press(["left"]*(position))
        pyautogui.press(["left"])

    try:
        corrected_sentence = input()
        return corrected_sentence
    except KeyboardInterrupt:
        interrupt_manual_replacement()



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




def select_and_edit_mono(focus_word: str, pre: list[str], post: list[str], direction="replace-loans") -> tuple[str, str, str] | None:
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

    global annotation_memory

    post_string = " ".join(post)
    pre_string = " ".join(pre)
    skip_message="-SKIP WORD-"
    # choices = [skip_message, "-CUSTOM INPUT-", "-DISCARD SENTENCE ALTOGETHER-"]
    choices = [skip_message, "-CUSTOM INPUT-"]
    
    if find_alternatives_mode == "wordnet":
        choices.extend([wordform.__str__() 
                for synset in wordnet.synsets(focus_word) 
                for word in synset.words() 
                for wordform in word.forms()])
    elif find_alternatives_mode == "bi-dict":
        # under the loanword's entry in the bi_dict, get the list of alternatives 
        choices.extend(bi_dict[focus_word])

    try:
        if direction == "replace-loans":
            choices.extend(annotation_memory["loan-native"][focus_word])
        elif direction == "replace-native":
            choices.extend(annotation_memory["native-loan"][focus_word])
    except KeyError:
        pass

    if focus_word in choices:
        choices.remove(focus_word)
    
    instruction = "Choose the most suitable alternative for the highlighted word or replace it with a custom word - if possible:"
    try:
        console.print("Sentence:", style="bold")
        console.print(pre_string, end=" ", style=SENT_STYLE)
        console.print(focus_word, style=MARK_LW, end="")
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
            sentence = pre_string+ " " +focus_word+ " " +post_string
            console.print(Rule(style="green3"))

            return sentence, None, None
        elif selected_alternative == "-DISCARD SENTENCE ALTOGETHER-":
            raise DiscardSentence
        # custom input
        elif selected_alternative == "-CUSTOM INPUT-":
            console.print("\n")
            try:
                selected_alternative = console.input(yellowbold("Enter your proposed alternative in its lemma form. \
    You can edit this in the next step.\n"))
                
                # Add the custom word to the BIDIRECTIONAL annotation memory
                #   Make sure they're stored under the right entries.
                #   update_annmem expects them as {loan : native}
                if direction == "replace-loans":
                    annotation_memory = update_annmem(annotation_memory, replacements={focus_word:selected_alternative})
                elif direction == "replace-native":
                    annotation_memory = update_annmem(annotation_memory, replacements={selected_alternative:focus_word})

            # if adding a custom word is interrupted: simply move on via the 'SkipLoanword'-Exception
            except KeyboardInterrupt:
                raise SkipLoanword

                sentence = pre_string + " " + focus_word + " " + post_string
                console.print(Rule(style="green3"))
                return sentence, None, None
            
        # TODO : allow user to select additional (secondary) alternatives that won't be implemented (but stored for potential later use)

        ###### EDIT SENTENCE #######
        console.print(Rule())
        # actually edit it
        new_sentence = edit(pre_string, selected_alternative, post)
        

        # if all's well
        console.print(Rule(style="green3"))
        return new_sentence, focus_word, selected_alternative

    except SkipLoanword:
        sentence = pre_string + " " + focus_word + " " + post_string
        console.print(Rule(title="Skipping current word", style="green3"))
        return sentence, None, None
    except KeyboardInterrupt:
        interrupt_menu_main()



def cli_replace_na(sentence: str, language: str) -> tuple[str,dict[str:str]]:
    """Replace NATIVE WORDS in a sentence with LOANWORDS"""
    # console.log("This would be the cli_replace_na")
    changes = {}
    try:
        # tokenize
        sentence = tokenizer.utokenize_string(sentence)
        # split sentence into list of tokens
        sentlist = sentence.split()
        sentlen = len(sentlist)

        # iterate through tokens via negative indexing 
        #           (necessary because the front of the list may be modified)
        for i in range(-sentlen, 0):
            word = sentlist[i]
            
            if word in annotation_memory["native-loan"].keys() \
                or araby.strip_diacritics(word) in annotation_memory["native-loan"].keys():
                # ...also match the stripped word in abjads 

                rest = sentlist[i+1:]
                full_sent, native_word, loan_alternative = select_and_edit_mono(focus_word=word, pre=sentlist[:i], post=rest[i+1:], direction="replace-native")
                if native_word is not None:
                    changes[native_word] = loan_alternative
                sentlist = full_sent.split()

        sentence = " ".join(sentlist)

        sentence, replacements = manual_replacement(sentence, direction="replace-native")
        sentence = detokenizer.detokenize_string(sentence)

        changes.update(replacements)

        return sentence, changes

    except ResetSentence:
        return cli_replace_na(sentence, language)
    except KeyboardInterrupt:
        raise ExitAnnotation
    except ExitAnnotation:
        raise ExitAnnotation
    pass



def cli_replace_lw(lw_list: list[str], sentence: str, language: str) -> tuple[str,dict[str:str]]:
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
    # return_dict = {"only_native":"", "changes":changes}
    try:
        # tokenize
        sentence = tokenizer.utokenize_string(sentence)
        if lw_list:
            lw_candidates = find_loanwords_in_sentence(sentence, lw_list, abjad_match=(language in ARABIC_SCRIPT))
        else:
            lw_candidates = []
        # split sentence into list of tokens
        sentlist = sentence.split()
        sentlen = len(sentlist)

        # iterate through tokens via negative indexing 
        #           (necessary because the front of the list may be modified)
        if lw_candidates:
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
                    full_sent, loanword, alternative = select_and_edit_mono(focus_word=word, pre=sentlist[:i], post=rest[i+1:])
                    if loanword is not None:
                        changes[loanword] = alternative
                    sentlist = full_sent.split()
        
        sentence = " ".join(sentlist)
        sentence, replacements = manual_replacement(sentence, display_menu=bool(lw_candidates))
        sentence = detokenizer.detokenize_string(sentence)
        changes.update(replacements)

        # return_dict["only_native"] = sentence
        # console.log(return_dict)
        
        return sentence, changes
            
    except ResetSentence:
        return cli_replace_lw(lw_list, sentence, language)
    except KeyboardInterrupt:
        raise ExitAnnotation

def single_pass(language: str,
                corpus_name: str,
                corpus_path: str,
                file_path: str,
                lw_list: list[str]):
    """Do the whole annotation in a single pass. No first pass to mark the interesting sentences."""
    ##### FILENAMES #####
    console.log(corpus_path)
    console.log(os.path.relpath(corpus_path))
    console.log(file_path)
    console.log(os.path.relpath(file_path))
    sents_path = os.path.relpath(os.path.join(os.path.relpath(corpus_path),os.path.relpath(file_path)))
    console.log(sents_path)
    annmem_path = os.path.abspath(f'{DATA_PATH}/internal/annotation_memory-{language}.json')
    output_file = os.path.abspath(f"{DATA_PATH}/output/OUT_{corpus_name}_{language}.json")


    # Read sentences from file to list
    with open(sents_path, "r", encoding="utf-8") as sentfile:
        sentences = sentfile.readlines()
    num_sentences = len(sentences)

    # load previous output
    results = load_prev_output(output_file)
    # console.log(results)

    ########### PERSISTENCE ########### 
    # If you want your annotation to continue from where you last left off:
    if remember_position:
        position = persistence_load(language, corpus_name=corpus_name, num_sentences=num_sentences)
        console.log("Starting annotation from sentence ", position) #keep
        # single pass mode
        n_pass = -1

    ########### SET ALTERNATIVE-FINDING-MODE ############
    config = load_config()
    
    global find_alternatives_mode
    try:
        find_alternatives_mode = config["find_alternatives"][language]
    except KeyError:
        find_alternatives_mode = ""
    # use WORDNET to find alternatives
    if find_alternatives_mode == "wordnet":
        if language in WORDNET_NAMES.keys():
            global wordnet
            wordnet = wn.Wordnet(WORDNET_NAMES[language])
            console.log("Using the following WordNets: ", wordnet.lexicons()) #keep
        else:
            console.log(f"Found no Wordnet-lexicon for {language}.") #keep
            find_alternatives_mode = "wordnet"
        # MAYBE TODO : wordnet download menu
        # console.print(f"The following are available wordnet lexica that can be downloaded")
    # use BILINGUAL-DICT to find alternatives
    elif find_alternatives_mode == "bi-dict":
        global bi_dict
        bi_dict = load_bidict(language)

    ######## LOAD ANNOTATION MEMORY ########
    if use_annotation_memory:
        console.log("Using annotation memory") #keep

        global annotation_memory
        try:
            with open(annmem_path, "r", encoding="utf-8") as am:
                _annotation_memory = json.load(am)
            # json doesn't have sets, only lists - convert all lists to sets: 

            for word, alt_list in _annotation_memory["native-loan"].items():
                annotation_memory["native-loan"][word] = set(alt_list)
            for word, alt_list in _annotation_memory["loan-native"].items():
                annotation_memory["loan-native"][word] = set(alt_list)
            console.log("loaded annotation memory") #keep
            # console.log(annotation_memory)
        except FileNotFoundError:
            annotation_memory = {"native-loan": {},"loan-native": {}}
            console.log("No file containing an Annotation-Memory could not be found.\nCreating file and starting annotation with an empty Annotation-Memory.") #keep
            
        except json.decoder.JSONDecodeError:
            # global annotation_memory
            # annotation_memory = {}
            annotation_memory = {"native-loan": {},
                     "loan-native": {}}
            console.log("A file for the Annotation-Memory was found, but didn't contain a valid store.\nStarting annotation with an empty Annotation-Memory.") #keep


    ##### SINGLE PASS MAIN #####
    console.log("Single pass:") #keep
    idx = position

        # timing
    global starttime
    starttime = time.time()

    console.log("Starting annotation") #keep
    while idx < num_sentences:
        try:
            console.print(Rule(title=f"Sentence {idx}",characters="#", style="spring_green3"))
            # get sentence from list via current index
            sentence = sentences[idx]
            # tokenize & strip of newlines
            # console.log(sentence)
            # console.print(sentence)
            sentence = tokenizer.utokenize_string(sentence.strip("\n"))
            # console.log(sentence)
            if lw_list:
                # console.log(lw_candidates)
                lw_candidates = find_loanwords_in_sentence(sentence, lw_list, abjad_match=(language in ARABIC_SCRIPT))
            else:
                lw_candidates = []
            highlight_all_loanwords(sentence, lw_candidates, abjad=(language in ARABIC_SCRIPT))
            # select which direction(s) to modify the sentence
            choices = {0 : "Replace LOANWORDS with native alternatives.", 1: "Replace NATIVE WORDS with loanwords"}
            try:
                user_choices = questionary.checkbox(
                message="What do you want to do? (you may select both)",
                style=default_select_style,
                choices=choices.values(),
                default=None,
                qmark="",
            ).unsafe_ask()
            except KeyboardInterrupt:
                interrupt_menu_main()
            
            # SKIP SENTENCE if no modifications are made
            if user_choices == []:
                console.log(f"Skipping Sentence {idx}") #keep
                idx += 1
                continue

            
            # initialize output if there's annotation to be done
            native_to_loan = {}
            loan_to_native = {}
            outdict_current_sent = {
                "changes-native-to-loan" : native_to_loan,
                "changes-loan-to-native" : loan_to_native,
                "original_sentence" : detokenizer.detokenize_string(sentence)}


            # replace loanwords w/ native
            if choices[0] in user_choices:
                console.print("  Replacing loanwords with native alternatives")
                console.print(Rule(style="green"))
                native_only_sent, changes = cli_replace_lw(lw_candidates, sentence, language)

                # update current output with the results
                outdict_current_sent["only_native_sentence"] = native_only_sent
                loan_to_native.update(changes)
            else:
                outdict_current_sent["only_native_sentence"] = outdict_current_sent["original_sentence"]

            # replace native words w/ loans
            if choices[1] in user_choices:
                console.print("  Replacing loanwords with native alternatives")
                console.print(Rule(style="green"))

                loans_only_sent, changes = cli_replace_na(sentence, language)

                # update current output with the results
                outdict_current_sent["only_loans_sentence"] = loans_only_sent
                native_to_loan.update(changes)
            else:
                outdict_current_sent["only_loans_sentence"] = outdict_current_sent["original_sentence"]

            # console.log(outdict_current_sent)
            # save results
            if outdict_current_sent["only_loans_sentence"] != outdict_current_sent["only_native_sentence"]:
                results[str(idx)] = outdict_current_sent
            # console.log(results)
            
            idx += 1
            # Save after each annotation
            if remember_position:
                # console.log("saving position")
                persistence_save(language=language, corpus_name=corpus_name, position=idx, time=time.time()-starttime)
                starttime = time.time()
            with open(output_file, 'w', encoding="utf-8") as f:
                # console.log("Saving results in:\n",yellow_light(output_file)) #keep
                json.dump(results, f, indent=4, separators=(',', ': '))
            if use_annotation_memory:
                save_annmem(annotation_memory, path=annmem_path)
            
            continue

        # EXCEPTION HANDLING
        except ResetSentence:
            # no incrementing the index, thus continuing with the same sentence
            console.log("Raised ResetSentence") #keep
            continue
        except DiscardSentence:
            console.log("Raised DiscardSentence") #keep
            # move on by incrementing the index
            idx += 1
            continue
        
        except PreviousSentence:
            console.log("Going back 1 sentence...")
            # move back by decrementing the index
            idx -= 1
            continue

        except ExitAnnotation:
            console.print("Exiting Annotation", end="\n", style="red bold")
            with console.status("",spinner="simpleDots"):
                time.sleep(.5)
            break
    
    # EXITING:
    # progress saving that has to be done inside the current function (access to variables)
    if remember_position:
        console.print("saving position")
        persistence_save(language=language, corpus_name=corpus_name, position=idx, time=time.time()-starttime)

    with open(output_file, 'w', encoding="utf-8") as f:
        console.log("Saving results in:\n",yellow_light(output_file)) #keep
        # console.log(results)
        json.dump(results, f, indent=4, separators=(',', ': '))
    # save annotation memory
    if use_annotation_memory:
        save_annmem(annotation_memory, path=annmem_path)
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

    try:
    ############### PATHS ###############
    # lw_path = f'{DATA_PATH}loanwords/{language}_loanwords.tsv'
        if not os.path.exists(f'{DATA_PATH}/output'):
            os.makedirs(f'{DATA_PATH}/output')
        
        output = f'{DATA_PATH}output/RESULTS_{language}.json'


        #######################################
        ######## LOADING LOANWORD-LIST ########
        try:
            lwlist = load_lwlist(language)
            console.log("loaded Loanword-list") #keep
        except FileNotFoundError:
            console.print(Rule())
            console.log(f"Couldn't find a list of loanwords for {language}") #keep
            options = ["YES, continue without loanword-list", "NO, locate loanword-list"]
            choice = questionary.select(
                f"Do you want to annotate the sentences {language.capitalize()} without a list of loanwords?\nYou'll have to identify and replace the loanwords yourself.",
                choices=options,
                style=default_select_style,
            ).ask()
            if choice == options[0]:
                # save "null"-filename
                config = load_config()
                console.log()
                filename = None
                config["wordlists"][language] = filename
                save_config(config)
                # set lwlist to empty, evaluates to false
                lwlist = set()
            else:
                filename = locate_lwlist()
                # save filename to config
                config = load_config()
                config["wordlists"][language] = filename
                save_config(config)
                lwlist = load_lwlist(language=language)
        # console.log(lwlist)

        single_pass(language=language,
                        corpus_name=corpus_name,
                        corpus_path=corpus_path,
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

    global wordnet

    # Start annotating.
    annotate_wrapper(lang, corpus_name, corpus_path, file_path)
    # console.log(corpus)
    # console.log(lang)
    pass


if __name__ == "__main__":
    main()
