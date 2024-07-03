from rich.text import Text
from rich.console import Console
from rich.rule import Rule
import os
import yaml
import questionary

from demo import demo
############# STYLES ##############
from util.styles import default_select_style, interrupt_style, SENT_STYLE, MARK_LW, yellowbold, yellow_light, orange_light
from util.util import load_config, save_config

console = Console()
new_corpus = False


# ROOT = os.path.abspath(os.path.join( os.path.dirname(__file__), ".."))
# ######## CONFIG saving
# def load_config(config_file: str="data/.config/config.yml") -> dict:
#     with open(os.path.abspath(os.path.join(ROOT,config_file)), "r", encoding="utf-8") as config_stream:
#         config_dict = yaml.safe_load(config_stream)
#     return config_dict

# def save_config(config_dict, config_file: str="data/.config/config.yml"):
#     with open(os.path.abspath(os.path.join(ROOT,config_file)), "w", encoding="utf-8") as config_stream:
#         yaml.dump(config_dict, config_stream)
#     pass


######### CORPUS checking/loading ###############
def locate_corpus(corpus_name) -> str:
    """Make the user enter the directory of a given corpus."""
    try:
        console.print(Rule())
        # TODO: use questionary.path to look for the path
        corpus_path = console.input(Text(f"The program doesn't know yet where you have stored the files of the {corpus_name} Corpus.\n\n")
                                    + yellow_light(f"Please enter (or paste) the path of the DIRECTORY where the files of the {corpus_name} Corpus can be found:\n"))
        # check if path exists
        assert os.path.isdir(corpus_path)
    # ensure the passed string is a directory
    except AssertionError:
        corpus_path = locate_corpus(corpus_name)
    config["corpora"][corpus_name] = corpus_path
    return corpus_path


def user_choose_corpus() -> tuple[str, str]:
    """Make the user either choose an existing corpus or add a new one."""
    # define choices for menu
    choices = list(set(config["corpora"].keys()))
    choices.append("-OTHER-")
    corpus_name = questionary.select(
        "Which corpus would you like to annotate?",
        choices=choices,
        style=default_select_style,
        ).unsafe_ask()
    # add a new corpus
    if corpus_name == "-OTHER-":
        global new_corpus
        new_corpus = True
        console.print(Rule())
        corpus_name = console.input(yellowbold("Enter the name of your corpus:\n"))
        corpus_path = locate_corpus(corpus_name)
        return corpus_name,corpus_path
    corpus_path = config["corpora"][corpus_name]
    # corpus path is not defined yet:
    if corpus_path is None:
        corpus_path = locate_corpus(corpus_name)
    return corpus_name, corpus_path


def check_corpus(corpus_name: str|None) -> str:
    if corpus_name is not None:
        try:
            corpus_path = config["corpora"][corpus_name]
            if corpus_path is None:
                console.log("working as intended")
                corpus_path = locate_corpus(corpus_name)
            return corpus_name, corpus_path
        except KeyError:
            console.print(Rule(style="red"))
            console.print("The name of the corpus you entered was not recognized.\n")
    corpus_name, corpus_path=user_choose_corpus()
    return corpus_name, corpus_path



######### LANG checking / FILE loading
def check_language(language: str, corpus_name: str, corpus_path: str):
    if new_corpus:
        console.print(Rule(style="#fc9e32"))
        console.print("It seems we don't know that corpus all too well yet.")
        console.print("We'll need to know the name of the language you'll annotate.\nTo avoid using multiple names for the one language, you'll be shown a list of languages names.")
        config["filenames"][corpus_name] = {}
        language, file_path = add_new_language_and_file(corpus_name, corpus_path)
        return language, file_path
    elif language is None:
        language, file_path = user_choose_language(corpus_name,corpus_path)
        return language, file_path
        
    # fast case: language was passed as an argument, and it's an existing corpus
    else:
        language = language.lower()
        try:
            file_path = config["filenames"][corpus_name][language]
            return language, file_path
        except KeyError:
            console.print(Rule(style="orange"))
            console.log(f"The language '{language}' wasn't recognized.")
            language, file_path = user_choose_language(corpus_name=corpus_name, corpus_path=corpus_path)
            file_path = config["filenames"][corpus_name][language]
            return language, file_path


def user_choose_language(corpus_name, corpus_path) -> tuple[str, str]:

    possible_langs = [x.capitalize() for x in list(config["filenames"][corpus_name].keys())]
    possible_langs.append("-NEW LANGUAGE-")
    console.print(Rule())
    
    lang_name = questionary.select(
        "Select the target language: ",
        choices=possible_langs,
        style=default_select_style,
    ).unsafe_ask().lower()

    if lang_name == "-NEW LANGUAGE-":
        lang_name, file_path = add_new_language_and_file(corpus_name, corpus_path)
        return lang_name, file_path
    else:
        file_path = config["filenames"][corpus_name][lang_name]
        return lang_name, file_path

    

def add_new_language_and_file(corpus_name, corpus_path):
    console.print(Rule(style="#fc9e32"))
    language_names = config["all_languages"].copy()
    language_names.append("-NEW LANGUAGE-")
    console.print("We'll need to know the name of the language you'll annotate.\nTo avoid using multiple names for the one language, you'll be shown a list of languages names.")

    lang_name = questionary.select(
            "If the list contains your target language, select it. Press -NEW LANGUAGE- otherwise",
            choices=language_names,
            style=default_select_style,).ask()
    if lang_name == "-NEW LANGUAGE-":
        lang_name = console.input(yellow_light("Enter the name of your language:\n"))
        # add new language to known languages
        config["all_languages"].append(lang_name)

    console.print(Rule())
    console.print("To annotate anything, we'll also need to know the name of the file you would like to annotate.")
    file_path = new_corpus_find_files(corpus_path)
    config["filenames"][corpus_name][lang_name] = file_path

    return lang_name, file_path


def new_corpus_find_files(corpus_path) -> str:
    """take corpus_path\n
    return filename
    """
    try:
        console.print(f"The following is the directory for the selected corpus: ")
        console.print(f"\n    {orange_light(corpus_path)}\n")

        # ask the user to enter the directory-path
        filename = console.input(yellow_light("Looking from this directory, please enter the relative path of your file:\n"))
        file_fullpath = os.path.join(corpus_path, filename)

        # Check 1: file exists and is a file (not a directory)
        assert os.path.isfile(file_fullpath)
        
        # PREVIEW
        with open(file_fullpath, "r", encoding="utf-8") as f:
            for i in range(5):
                console.print(yellow_light(f'{str(i)}\t'),f.readline()[:50].strip("\n")," ...")
        # USER: confirm file
        user_feedback = questionary.select(
            "These are the starts of the first few sentences. Is this the right file?",
            choices=["YES, continue to annotation.", "NO, choose another."],
            style=default_select_style,
        ).ask()
        
        # Check 2: user actually wants this file
        assert user_feedback == "YES, continue to annotation."
        
        return filename

    # If one of the checks fails
    except AssertionError:
        console.print(Rule(style="red"))
        console.print("Hmm, something didn't quite go right. Let's try again:")
        return new_corpus_find_files()


######## DEMO
def show_demo():
    if config["show_demo"] is True:
        try:
            # Show demo
            demo(console)
        # abort demo when interrupted
        except KeyboardInterrupt:
            pass
        
        # Ask the user whether to keep running the demo on startup
        choices=["YES, keep showing the demo on startup", "NO, don't show the demo on startup"]
        show = questionary.select(
        "Do you want to keep starting the annotation-process with the Demo?",
        choices=choices,
        style=default_select_style,
        ).unsafe_ask()

        # NO, don't show demo on startup anymore
        if show == choices[1]:
            config["show_demo"] = False


def launch(corpus, lang):
    """
    
    returns:
    language, corpus_name, corpus_path, file_path
    """
    # load configuration, make it globally accessible
    global config
    config = load_config()
    show_demo()
    # check for and/or get the right corpus-name and -path
    corpus_name, corpus_path = check_corpus(corpus_name=corpus)
    console.log("corpus path= ", corpus_path)
    # check for and/or get the right language-name and file-path
    lang, file_path = check_language(lang, corpus_name, corpus_path)
    save_config(config_dict=config)
    console.log(f"Updated config file.")
    return lang, corpus_name, corpus_path, file_path