##################  IMPORTS  ######################
# Generic
import re
import os
# import sys
import time
import json
from io import TextIOWrapper
import copy
# Visuals
from rich.style import Style
from rich.console import Console
from rich.rule import Rule
from rich.highlighter import Highlighter
from rich.prompt import Prompt
# Alternative Lookup
from rich.text import Text
import wn


# Interactivity
import click
from typing import Optional
import questionary
import pyperclip
import pyautogui


from language_mappings import NLLB_NAMES, WORDNET_NAMES #, GET_FILENAMES, AVAILABLE_LANGUAGES
from util.util import locate_lwlist,\
                        load_lwlist,\
                        load_position,\
                        save_position_and_pass,\
                        which_pass,\
                        find_loanwords_in_sentence,\
                        split_punctuation,\
                        highlight_all_loanwords, \
                        detect_changes, \
                        interrupt_menu_main, \
                        interrupt_manual_replacement, \
                        load_tok_detok, \
                        interrupt_startup


# demo
from startup import launch
from demo import demo
###################################################



# Global Variables
console = Console()
use_annotation_memory = True
remember_position = True
wipe_previous = False

from utoken import utokenize
from utoken import detokenize
tokenizer = utokenize.Tokenizer()
detokenizer = detokenize.Detokenizer()

############# STYLES ##############
from util.styles import default_select_style, interrupt_style, SENT_STYLE, MARK_LW, yellowbold, yellow_light, orange_light, magentabold
print(wn.lexicons())
wordnet = wn.Wordnet("odenet")

############# INTERRUPTS #################
from util.interrupts import *


##### DATA PATHS: ADJUST IF NECESSARY #####

DATA_PATH = "4 - CDA - Contrastive Dataset Annotator/data/"
SRC_FOLDER = f"{os.path.dirname(os.path.realpath(__file__))}"
DATA_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/")
PERSIST = f"{DATA_PATH}internal/PERSISTENCE.json"

annotation_vars = {}

# initialise annotation memory
annotation_memory = {}





def manual_replacement(sentence: str) -> tuple[str, dict[str:str]]:
    # TODO implement replacement
    
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
            if choice.startswith("YES"):
                continue
            else:    
                break
            sentence = new_sentence
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
    # starttime = time.time()
    # console.log(time.time() - starttime)
    pyperclip.copy(sentence)
    pyautogui.hotkey("ctrl", "v")
    # console.log(time.time() - starttime)

    # for i in range(len(post)):
        # pyautogui.hotkey("ctrl", "left")
    # pyautogui.press(['left']*(len(poststring)))
    if position:
        position = len(sentence[position:].split())
        with pyautogui.hold('ctrl'):
            pyautogui.press(["left"]*(position))
        pyautogui.press(["left"])
    
    # pyautogui.press(["left"]*(len(post)))
    # console.log(time.time() - starttime)
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
    starttime = time.time()
    instruction = "The target word has been replaced. You can now edit the sentence if it's necessary.\nHit ENTER when you're done:"
    try:
        # console.log(time.time() - starttime)
        console.print(instruction, style="yellow")
        poststring = " ".join(post)
        
        sentence = pre + " " + selected + " " + " ".join(post)
        
        pyperclip.copy(sentence)
        pyautogui.hotkey("ctrl", "v")
        # console.log(time.time() - starttime)

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


def select_and_edit_multi(loanword: str, pre: str, post: list) -> list[tuple[str,str]]:
    """
    Generate alternatives for a given loanword using WordNet.
    Let the user choose any number of suitable alternatives.

    Parameters
    ----------
    loanword : str
        A loanword

    Returns
    -------
    picked_alternatives, new_sents: tuple[list[str], list[str])
        a tuple of two lists, containing the chosen alternatives and edited output sentences respectively
    """
    picked_alternatives = []
    new_sents = []

    skip_message="-SKIP LOANWORD-"
    choices = [skip_message, "-CUSTOM INPUT-", "-DISCARD SENTENCE ALTOGETHER-"]
    
    choices.extend([wordform.__str__() 
              for synset in wordnet.synsets(loanword) 
              for word in synset.words() 
              for wordform in word.forms()])
    try:
        choices.extend(annotation_memory[loanword])
    except KeyError:
        pass
    if loanword in choices:
        choices.remove(loanword)
    instruction = "Choose a valid alternative for the highlighted word, if possible:"
    try:
        while True:
            # cosmetics
            console.print(Rule(characters="#", style="green"))
            console.print(f"Sentence:", style="bold")
            # print sentence with highlighted loanword
            console.print(pre, end=" ", style=SENT_STYLE)
            console.print(loanword, style=MARK_LW, end=" ")
            console.print(post, style=SENT_STYLE, end="\n\n")
            # alternative selection menu
            selected = questionary.select(
                message=instruction,
                style=default_select_style,
                instruction=False,
                choices=choices,
                use_shortcuts=True,
                default=None,
                qmark="",
                ).unsafe_ask()
            # flow-control:
            if selected == skip_message:
                break
            elif selected == "-DISCARD SENTENCE ALTOGETHER-":
                raise DiscardSentence
            # custom input
            elif selected == "-CUSTOM INPUT-":
                try:
                    console.print("\n")
                    selected = console.input(yellowbold("Enter your proposed alternative in its lemma form. \
You can edit this in the next step.\n"))
                # Add the custom word to the annotation memory
                    annotation_memory[loanword].add(selected)

                except KeyError:
                    annotation_memory[loanword] = {selected}
                except KeyboardInterrupt:
                    continue
            # default case
            else:
                choices.remove(selected)

            console.print(Rule())
            
            # Catch KeyboardInterrupt during Sentence-Editing
            try:
                new_sentence = edit(pre, selected, post)
            except SkipLoanword:
                # Just try again, basically
                continue
            
            # Add results to corresponding lists
            new_sents.append(new_sentence)
            picked_alternatives.append(selected)
            
            # Skip-message shenanigans
            choices.remove(skip_message)
            skip_message = "-NO MORE VALID ALTERNATIVES-"
            choices.insert(-2, skip_message)
            
            instruction = "Are there any other valid alternatives for the highlighted word? If so, select the next one. "
            
        # list[
        #   (loanword, alternative_1, sentence_v1),
        #   (loanword, alternative_2, sentence_v2),
        #   ...
        # ]
        return list(zip([loanword]*len(picked_alternatives),set(picked_alternatives), set(new_sents)))
    

    except KeyboardInterrupt:
        # Options given to the User when interrupting the process with ctrl+c
        interrupt_menu_main()
    
    # IDEA: PUT FUNCTION IN WHILE LOOP WITHIN TRY, RAISE INTERRUPT WHEN FINISHED
    # instead of recursive functions

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
    
    choices.extend([wordform.__str__() 
              for synset in wordnet.synsets(loanword) 
              for word in synset.words() 
              for wordform in word.forms()])
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
            
        # default case
        # else:
        #     choices.remove(selected)
        
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
            
    
def second_pass_cli(lw_list: list[str], sentence: str) -> dict[str:str, str:dict] | None:
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

    # TODO: implement multiple alternatives selection
    # TODO: implement key-binds menu to navigate (skip, break, restart current sentence)
    # all_results = []
    # final_sentences = []
    changes = {}
    return_dict = {"new_sentence":"", "changes":changes}
    try:
        # sentence = split_punctuation(sentence)
        sentence = tokenizer.utokenize_string(sentence)
        if lw_list:
            lw_candidates = find_loanwords_in_sentence(sentence, lw_list)
        else:
            lw_candidates = []
        # console.log("lw_candidates: ",lw_candidates)
        # for loanword in lw_candidates:
        sentlist = sentence.split()
        sentlen = len(sentlist)

        

        for i in range(-sentlen, 0):
            word = sentlist[i]

            if word in lw_candidates:
                # console.log("here here: ", word)
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
        return second_pass_cli(lw_list, sentence)
    # except DiscardSentence:
    #     console.log("Raised DiscardSentence")
    #     return None
    # except ExitAnnotation:
    #     raise ExitAnnotation
    except KeyboardInterrupt:
        raise ExitAnnotation
    
            # changes_file.write(f'{alternative}\t{loan}\n')
            # loan_file.write(sentence)
            # native_file.write(new_sent)
        # print(all_results)



# def first_pass_no_lwlist(language: str,
#                          corpus_name: str,
#                          corpus_path: str,
#                          file_path: str,):
    
#     sents_path = os.path.join(corpus_path,file_path)
#     # Read sentences from file to list
#     with open(sents_path, "r", encoding="utf-8") as sentfile:
#         sentences = sentfile.readlines()
#     num_sentences = len(sentences)


def first_pass_sentence_annotation(sentence: str, lw_list, position, marking_dict, mode="wordlist") -> dict:
    console.log(lw_list)
    console.log(bool(lw_list))

    # try:
    sentence = sentence.strip("\n")
    
    console.print(f'{yellowbold("Sentence")} ({(str(position))}):', end="")
    if mode == "wordlist" and (lw_list):
        # tokenize sentence for matching
        console.log("running first_pass_sentence_annotation")
        sentence = tokenizer.utokenize_string(sentence)
        lw_candidates = find_loanwords_in_sentence(sentence, lw_list)
        highlight_all_loanwords(sentence, lw_candidates)
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
    console.log(user_choices)
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
    marking_file = os.path.abspath(f'{DATA_PATH}marking/_marking{corpus_name}_{language}.json')

    # Read sentences from file to list
    with open(sents_path, "r", encoding="utf-8") as sentfile:
        sentences = sentfile.readlines()
    num_sentences = len(sentences)

    try:
        with open(marking_file, 'r', encoding="utf-8") as f:
            marking_dict = json.load(f)
    except FileNotFoundError: 
        marking_dict = {} 
    except json.decoder.JSONDecodeError:
        marking_dict = {}
    if type(marking_dict) is not dict:
        marking_dict = {}
        
            

    if remember_position:
        position = load_position(language, num_sentences)
        console.log(position)
        n_pass = 1
    # (position)


    ##############################################
    ############ FIRST PASS MAIN #################
    console.log("1st pass:")
    idx = position
    try:
        console.log("Starting iteration")
        for sentence in sentences[position:]:
            console.log("first iteration")
            try:
                marking_dict = first_pass_sentence_annotation(sentence, lw_list, position, marking_dict)
            except ResetSentence:
                console.log("ResetSentence")
                pass
            except DiscardSentence:
                console.log("DiscardSentence")
                pass
            # except ExitAnnotation:
            #     r
                # break
                # console.log("ExitAnnotation")
                # pass
            # sentence = sentence.strip("\n")
            # console.print(f'{yellowbold("Sentence")} ({(str(position))}):')
            # if lw_list:
            #     # sentence = tok.utokenize_string(sentence)
            #     sentence = isolate_punctuation(sentence)
            #     lw_candidates = find_loanwords_in_sentence(sentence, lw_list)
            #     highlight_all_loanwords(sentence, lw_candidates)
            # else:
            #     console.print(sentence)
            
            # choices = {"Obvious loanwords":"contains-LW",
            #            "Named Entities" : "contains-NE",
            #            "Code-switching": "contains-CS"}
            # try:
            #     user_choices = questionary.checkbox(
            #     message="(multiselect) Does the following sentence contain one or multiple instances of: ",
            #     style=default_select_style,
            #     choices=choices.keys(),
            #     default=None,
            #     qmark="",
            # ).unsafe_ask()
            # except KeyboardInterrupt:
            #     interrupt_menu()
            # console.log(user_choices)
            # marking_dict[position] = {"sentence": sentence,}
            # for choice, abbr in choices.items():
            #     if choice in user_choices:
            #         marking_dict[position][abbr] = True
            #     else:
            #         marking_dict[position][abbr] = False
            #     console.log(marking_dict)
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
            console.log(marking_dict)
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
    marking_file = os.path.abspath(f'{DATA_PATH}marking/_marking{corpus_name}_{language}.json')
    output_file = os.path.abspath(f"{DATA_PATH}output/OUT_{corpus_name}_{language}.json")
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
    

    ########### USE WORDNET OR NAH? ############
    if language in WORDNET_NAMES.keys():
        global wordnet
        wordnet = wn.Wordnet(WORDNET_NAMES[language])
        use_wordnet = True
        console.log("Using the following WordNets: ", wordnet.lexicons())
    else:
        console.log(f"Found no Wordnet-lexicon for {language}.")
        use_wordnet = False

        # MAYBE TODO : wordnet download menu
        # console.print(f"The following are available wordnet lexica that can be downloaded")


    ############ FILE HYGIENE ############
    # if wipe_previous:
    #     for file in [out_loans,out_nativized, changes_path]:
    #         with open(file, 'w') as f: pass

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

    #######

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
                single_result = second_pass_cli(lw_candidates, sentence)
                
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
    lw_path = f'{DATA_PATH}loanwords/{language}_loanwords.tsv'
    if not os.path.exists(f'{DATA_PATH}/output'):
        os.makedirs(f'{DATA_PATH}/output')
    
    output = f'{DATA_PATH}output/RESULTS_{language}.json'


    #######################################
    ######## LOADING LOANWORD-LIST ########
    try:
        lwlist = load_lwlist(lwlist_path=lw_path)
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
            lwlist = load_lwlist(lwlist_path=f'{DATA_PATH}loanwords/{filename}')
            # use_lwlist = True
    console.log(lwlist)
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
    except ExitAnnotation:
        console.print("Exiting Annotation", end="\n", style="red bold")
        with console.status("",spinner="simpleDots"):
            time.sleep(.5)




    ############# ANNOTATION #############
    ######################################
    # try:
    #     with open(out_loans, "a", encoding="utf-8") as loansents,\
    #         open(out_nativized, "a", encoding="utf-8") as nativesents,\
    #         open(changes_path, "a", encoding="utf-8") as changes:
            
    #         for sentence in sentences[position:]:
    #             sentence = sentence.strip("\n")
    #             found_words = [] 
    #             # found_words --> candidates
    #             # look for candidates in the current sentence
    #             for lw in lwlist:
    #                 lw = lw.strip("\n")
    #                 # only match full
    #                 if full_match_only:
    #                     lw = f' {lw} '
    #                 # ^ not necessary, i think?
    #                 if lw in sentence:
    #                     found_words.append(lw)
    #                 elif lw.lower() in sentence:
    #                     found_words.append(lw.lower())
    #             # If there were any candidates found:
    #             if found_words:

    #                 console.clear()
    #                 console.print(position)
    #                 cli(loanwords=found_words, 
    #                     sentence=sentence, 
    #                     changes_file = changes, 
    #                     loan_file = loansents,
    #                     native_file = nativesents)
    #             position += 1
    # # Graceful Exiting
    # except ExitAnnotation:
    #     console.print("Exiting Annotation", end="\n", style="red bold")
    #     with console.status("",spinner="simpleDots"):
    #         time.sleep(.5)

    # ############ PERSISTENCE #############
    # finally:
    #     # save annotation memory
    #     if load_and_save_annotation_memory:
    #         console.print("Annotation Memory: ", annotation_memory)
    #         out_annmem = {}
    #         for lw,alt_set in annotation_memory.items():
    #             out_annmem[lw] = list(alt_set)

    #         print(out_annmem)
    #         with open(annmem_path, 'w', encoding="utf-8") as am:
    #             json.dump(out_annmem, am)


# questionary.press_any_key_to_continue(">> Press ENTER to continue",style=default_select_style,).ask()



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
    console.print(yellowbold("Fairly good"))
    main()
    # print(wordnet.lexicons())
    # annotate(
    # est", remember_position=True, load_and_save_annotation_memory=True)


    # print(console.height)
    # TODO:
    # - Startup
    # - Demo
    # ...
    # n: packaging