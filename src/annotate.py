##################  IMPORTS  ######################
# Generic
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

# demo
from startup import launch
from demo import demo
###################################################


from language_mappings import NLLB_NAMES, WORDNET_NAMES #, GET_FILENAMES, AVAILABLE_LANGUAGES

# Global Variables
console = Console()

############# STYLES ##############
from styles import default_select_style, interrupt_style, SENT_STYLE, MARK_LW, yellow, yellow_light, orange_light

wordnet = wn.Wordnet()

##### DATA PATHS: ADJUST IF NECESSARY #####

DATA_PATH = "4 - CDA - Contrastive Dataset Annotator/data/"
SRC_FOLDER = f"{os.path.dirname(os.path.realpath(__file__))}"
DATA_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/")
PERSIST = f"{DATA_PATH}internal/PERSISTENCE.json"


# initialise annotation memory
annotation_memory = {}

# Custom Exceptions for navigating the annotation-flow
class SkipLoanword(Exception):
    """Skip to the next Sentence in the annotation process."""
    pass

class DiscardSentence(Exception):
    """Don't save anything for the current sentence, move on with the next one."""
    pass

class ResetSentence(Exception):
    """Restart the annotation process for the current sentence."""
    pass

class ExitAnnotation(Exception):
    """CTRL+C: Exit the annotation process entirely."""
    pass


def edit(pre: str, selected: str, post: str)-> str:
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

    instruction = "The target word has been replaced. You can edit the sentence now.\nHit ENTER when you're done:"
    try:
        console.print(instruction, style="yellow")
        sentence = pre + selected + post.strip("\n")
        pyperclip.copy(sentence)
        pyautogui.hotkey("ctrl", "v")
        pyautogui.press(['left']*(len(post)-1))
        corrected_sentence = input()
        return corrected_sentence
    except KeyboardInterrupt:
        raise SkipLoanword


def select_and_edit(loanword: str, pre: str, post: str, picked_alternatives: list=[]) -> list[tuple[str,str]]:
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
            console.print("\n", Rule(characters="#", style="green"))
            console.print("Sentence:", style="bold")
            # print sentence with highlighted loanword
            console.print(pre, end="", style=SENT_STYLE)
            console.print(loanword, style=MARK_LW, end="")
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
                    selected = console.input(yellow("Enter your proposed alternative in its lemma form. \
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
        options = ["RESTART annotation of the current sentence (already made annotations for this sentence will be lost)", "DISCARD the current Sentence, continue with the next one", "QUIT the annotation process."]
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
                # pointer=f'{(position-7)*" "}>>'
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
        # 3: EXIT annotation
        elif choice == options[2]:
            raise ExitAnnotation
    
    # IDEA: PUT FUNCTION IN WHILE LOOP WITHIN TRY, RAISE INTERRUPT WHEN FINISHED
    # instead of recursive functions


def cli(loanwords: list[str], sentence: str, changes_file: TextIOWrapper, loan_file: TextIOWrapper, native_file: TextIOWrapper) -> None:
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
    all_results = []
    final_sentences = []
    try:
        for loanword in loanwords:
            if sentence.count(loanword) > 1:
                print(f"Warning: there are multiple instances of '{loanword}' in this sentence.")
                # TODO: implement functionality for sentences where a loanword shows up more than once 
            pre,post= sentence.split(loanword, 1)
            # loans_alts_and_sents = print(select_and_edit(loanword, pre, post))
            loans_alts_and_sents = select_and_edit(loanword, pre, post)
            if loans_alts_and_sents is None:
                break
        # in each tuple 'tup' of the above list:
            # tup[0] = loanword
            # tup[1] = alternative
            # tup[2] = new sentence
        all_results.extend(loans_alts_and_sents)
        pass
        
    except ResetSentence:
        cli(loanwords, sentence, changes_file, loan_file, native_file)
    except DiscardSentence:
        pass
    except ExitAnnotation:
        raise ExitAnnotation
    except KeyboardInterrupt:
        raise ExitAnnotation
    else:
    # SAVING THE RESULTS:
        for loan, alternative, new_sent in all_results:
            changes_file.write(f'{alternative}\t{loan}\n')
            loan_file.write(sentence)
            native_file.write(new_sent)
        # print(all_results)


def util_start_annotating_from_sent_x(num_sents):
    userinput = input(f'From which sentence onward would you like to start annotating?\n(Valid range: 0 - {num_sents-1})')
    try:
        number = int(userinput)
        if number > num_sents:
            print(f'Your input ({userinput}) exceeds the number of available sentences.\nPlease pass in a value lower than {num_sents}.')
            number = util_start_annotating_from_sent_x(num_sents)
    except ValueError:
        print(f'{userinput} cannot be converted to an Integer.\nPlease only enter digits')
        number = util_start_annotating_from_sent_x(num_sents)
    return number


def annotate(language: str,
             corpus_name: str,
             corpus_path: str,
             file_path: str,
             remember_position: bool=True,
             wipe_previous: bool=False,
             load_and_save_annotation_memory: bool=True,
             full_match_only: bool=True):
    """"""
    ############### PATHS ###############
    if not os.path.exists(f'{DATA_PATH}/output'):
        os.makedirs(f'{DATA_PATH}/output')
    lw_path = f'{DATA_PATH}loanwords/{language}_loanwords.tsv'
    sents_path = os.path.join(corpus_path,file_path)
    out_nativized = f"{DATA_PATH}output/NATIVE_{language}.txt"
    out_loans = f"{DATA_PATH}output/LOANS_{language}.txt"
    changes_path = f"{DATA_PATH}CHANGES_{language}.tsv"
    annmem_path = f'{DATA_PATH}internal/annotation_memory-{language}.json'

    # Read sentences from file to list
    with open(sents_path, "r", encoding="utf-8") as sentfile:
        sentences = sentfile.readlines()
    num_sentences = len(sentences)

    # LOAD WORDNET
    if language in WORDNET_NAMES.keys():
        global wordnet
        wordnet = wn.Wordnet(WORDNET_NAMES[language])
        print(wordnet.lexicons())
    else:
        console.print(f"Found no Wordnet-resource for {language}.")


    ###### LOAD ANNOTATION MEMORY #####
    if load_and_save_annotation_memory:
        try:
            global annotation_memory
            with open(annmem_path, "r", encoding="utf-8") as am:
                _annotation_memory = json.load(am)
            for lw, alt_list in _annotation_memory.items():
                annotation_memory[lw] = set(alt_list)
        except FileNotFoundError:
            console.log("No file containing an Annotation-Memory could not be found.\nCreating file and starting annotation with an empty Annotation-Memory.")
            
        except json.decoder.JSONDecodeError:
            console.log("A file for the Annotation-Memory was found, but didn't contain a valid store.\nStarting annotation with an empty Annotation-Memory.")
            
            pass
    ########### PERSISTENCE ########### 
    # If you want your annotation to continue from where you last left off:
    if remember_position:
        try:
            # open the memory file, load the saved position for the current language
            with open(PERSIST, "r", encoding="utf-8") as f:
                memory = json.load(f)
            
            position = memory[language]["position"]
            # if a file has already been passed through completely:
            if memory[language]["position"] >= len(sentences):
                # Ask the user whether they want to reannotate the whole process again
                choice = questionary.select(
                    "You've already checked this corpus all the way through.\nDo you really want to go through it again?",
                    choices=("yes","no", "yes, but only from a certain line onwards")).ask()
                if choice == "no":
                    print("Exiting...")
                    time.sleep(1.0)
                elif choice == "yes, but only from a certain line onwards":                    
                    position = util_start_annotating_from_sent_x(num_sentences)            
                else:
                    position=0
        except FileNotFoundError:
            print("Memory-file could not be found.\nInitialising memory, and starting annotation from the start of the selected file.")
            memory = {}
            position = 0
        except json.decoder.JSONDecodeError:
            print("Memory-file was found, but didn't contain a valid store.\nInitialising memory, and starting annotation from the start of the selected file.")
            memory = {}
        # File exists, but "language" has no entry yet 
        except KeyError:
            position = 0
            memory[language] = {"position": position} 
    ################################
    else:
        position = 0

    ### LOADING LOANWORD-LIST
    with open(lw_path, "r", encoding="utf-8") as lwfile:
        lwlist = set(lwfile.read().split("\n"))
        # Remove empty string
        try:
            lwlist.remove("")
        except ValueError:
            pass

    ############ FILE HYGIENE ############
    if wipe_previous:
        for file in [out_loans,out_nativized, changes_path]:
            with open(file, 'w') as f: pass


    ############# ANNOTATION #############
    ######################################
    try:
        with open(out_loans, "a", encoding="utf-8") as loansents,\
            open(out_nativized, "a", encoding="utf-8") as nativesents,\
            open(changes_path, "a", encoding="utf-8") as changes:
            
            for sentence in sentences[position:]:
                sentence = sentence.strip("\n")
                found_words = [] 
                # found_words --> candidates
                # look for candidates in the current sentence
                for lw in lwlist:
                    lw = lw.strip("\n")
                    # only match full
                    if full_match_only:
                        lw = f' {lw} '
                    # ^ not necessary, i think?
                    if lw in sentence:
                        found_words.append(lw)
                    elif lw.lower() in sentence:
                        found_words.append(lw.lower())
                # If there were any candidates found:
                if found_words:

                    console.clear()
                    console.print(position)
                    cli(loanwords=found_words, 
                        sentence=sentence, 
                        changes_file = changes, 
                        loan_file = loansents,
                        native_file = nativesents)
                position += 1
    # Graceful Exiting
    except ExitAnnotation:
        console.print("Exiting Annotation", end="\n", style="red bold")
        with console.status("",spinner="simpleDots"):
            time.sleep(.5)

    ############ PERSISTENCE #############
    finally:
        # save file position
        if remember_position:
            try:
                memory[language]["position"] = position
            except KeyError:
                memory[language] = {"position": position}
            # console.log(memory)
            with open(PERSIST, 'w', encoding="utf-8") as f:
                json.dump(memory, f)
        # save annotation memory
        if load_and_save_annotation_memory:
            console.print("Annotation Memory: ", annotation_memory)
            out_annmem = {}
            for lw,alt_set in annotation_memory.items():
                out_annmem[lw] = list(alt_set)

            print(out_annmem)
            with open(annmem_path, 'w', encoding="utf-8") as am:
                json.dump(out_annmem, am)


# questionary.press_any_key_to_continue(">> Press ENTER to continue",style=default_select_style,).ask()



@click.command()
@click.option("--corpus", "-c", type=str)
@click.option("--lang", "-l", type=str)
def main(corpus, lang):
    # check given (in command-line) and get missing arguments needed for annotation:
    # - Language name (may be passed when calling the script)
    # - Name of the corpus (may be passed when calling the script)
    # - Path where the corpus' files are located
    # - Filename of the corpus' language specific file 
    lang, corpus_name, corpus_path, file_path = launch(corpus=corpus, lang=lang)
    
    # Start annotating.
    annotate(lang, corpus_name, corpus_path, file_path)
    # console.log(corpus)
    # console.log(lang)
    pass


if __name__ == "__main__":
    main()

    # annotate("test", remember_position=True, load_and_save_annotation_memory=True)


    # print(console.height)
    # TODO:
    # - Startup
    # - Demo
    # ...
    # n: packaging