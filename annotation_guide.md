# Annotation Guide
Hi! Thanks for using CLoAn.

Manual annotation is often tedious, but I'm trying to make it **as easy as possible** for You, the Annotator &mdash; hence this custom Command-Line Interface (CLI) for this very particular type of annotation. It  works entirely within your console (CMD/PowerShell on Windows, Terminal on MacOS, bash on Linux).

The goal of the project is a contrastive dataset of loanwords/native words, thus the tool is named _**CLoAn**_, short for _**C**ontrastive **Lo**anword **An**notator_. 

The following chapters serve to provide a both an overview of the functionality of CLoAn and an annotation guide.

## Installing CLoAn

To use _CLoAn_, clone this repository in a directory of your choice:

```bash
    git clone git@github.com:chamisshe/CLoAn.git
```

Next, you'll want to run the included setup-scripts. This will create a virtual environment, install the required packages and create the necessary folder structure.

<details>
    
**<summary>Mac/Linux</summary>**

On a UNIX-based system, run the following commands:
    
```bash
    cd CLoAn
    source setup.sh
```

</details>

<details>

**<summary>Windows</summary>**

On Windows (CMD or PowerShell), run:
    
```powershell
    cd CLoAn
    setup.bat
```

</details>

#### Installing the Flores+ dataset
You will most likely will work with the `devtest` split of the **FLORES+** dataset. We cannot host the dataset on a public repository, therefore you will have to download the dataset from it's [source repository](https://github.com/openlanguagedata/flores?tab=readme-ov-file#download-the-dataset) yourself.<br>
**Important:** Keep track of the path where you stored it, as you'll need to tell _CLoAn_ when you use the tool for the first time.


## Using CLoAn

<details>

**<summary>Navigating CLoAn</summary>**

You can navigate all of _CLoAn_ using simply your keyboard, in fact your mouse won't be of much use here.<br>

#### Interrupting/Exiting

To **interrupt** _CLoAn_ at any point, press `CTRL + C`. <br> This raises what's called a _KeyboardInterrupt_. This is one of Python's built-in ways of letting the user stop the execution of a script.<br><br> 
In most cases, this should bring up a menu with various options of what to do next.

#### Menus

To navigate up and down between multiple options in the menus, use either
- the arrow keys (`up`/`down`)
- _vim_-style navigation: (`j` - down; `k` - up)

##### Select

In menus where you have to choose a single option (including Interrupt-menus), each item should have a number in front of itself. Pressing said number on your keyboard will take you directly to this item. 

The current item will be highlighted in magenta/purple.<br>
To select the current item, press enter.

##### Checkbox

In menus where you may want to select multiple options, you can **select/unselect** an item by pressing `SPACE`. By default, all items are unselected. Once you've selected the items you want, press `ENTER`.

</details>


### Starting up
Once you've installed the tool (instructions in the `README`), you'll want to run it. Since it relies on a number of Python-modules, make sure you're running it inside the proper virtual environment (or _venv_).
#### Activating the venv 
<details>
    
**<summary>Mac/Linux</summary>**

On a UNIX-based system such as Linux or MacOS, the following command will activate the virtual environment:
    
```bash
source .venv-cloan/bin/activate && cd cloan
```

</details>

<details>

**<summary>Windows</summary>**

On Powershell, run:

```powershell
.venv-cloan\Scripts\activate ; cd cloan
```

or on CMD, run:

```cmd
.venv-cloan\Scripts\activate && cd cloan
```
</details>


##### Regular Startup

Run the script from your terminal of choice.

`python annotate.py` / `python3 annotate.py`

You will then be presented with an interactive menu to guide you through the startup.<br>

###### Corpus selection

In a first step, you'll have to choose the corpus you're annotating. This will most likely be `FLORES+devtest`. Since it's the default, _CLoAn_ already knows about both `FLORES+devtest` and `FLORES+dev`.<br>
The first time you try to annotate any corpus, _CLoAn_ will need to know where to find the relevant files. You'll be asked to enter the path to the directory where **all** the corpus' files can be found.

<details>

**<summary>Example</summary>**

Let's say the FLORES+ dataset is stored in the following directory:<br>`C:/Users/Gimli/Documents/floresp-v2.0-rc.2`

It will contain two subdirectories, `dev` and `devtest`:

```powershell
floresp-v2.0-rc.2
├───dev
└───devtest
```

When prompted for the path of `FLORES+devtest`, you'll have to paste `C:/Users/Gimli/Documents/floresp-v2.0-rc.2/devtest`, as this is where all the files are stored. Let's call this the `<corpus_path>` for the remainder of this guide.

</details>

The good thing is: Once you've told CLoAn the (correct) path to the corpus, it remembers.

<details>

**<summary>Under the hood...</summary>**

...meta-information such as paths, filenames, language names are stored under `data/.config/config.yml`. When starting _CLoAn_, it tries to take as much info as it can from this config-file. When information is missing, it (ideally) asks the user to provide the necessary info. Less ideally, if it's an error I didn't encounter yet and thus didn't put any precautions in place, starting up fails.<br>
It is generally recommended that you **do not mess with the config file** &mdash; unless you like trouble or youreally know what you're doing.

</details>

###### Select Language

Next, you'll need to select the language you want to annotate.

Different corpora might use different naming schemes. Thus, _CLoAn_ needs to remember the specific filename for each corpus-language combination. For a few languages, where we anticipate annotation, the filenames are already stored.<br>
If you're choosing a different language (`> Other`), _CLoAn_ will ask for the filename, which we'll call `<filename>`. 

<details> 

**<summary>Example</summary>**

Let's say you want to annotate the FLORES+devtest corpus in _Sindarin_:

If FLORES+ had any resources in Sindarin (a fictional language in Tolkien's Middle-earth), they would be stored in the following file:<br>`devtest.sjn_Teng`

Let's break this down:
- `devtest` is the name of the subset (split). All filenames in FLORES+devtest start with it. the filename
- `sjn` is the language code according to [ISO-639-3](https://iso639-3.sil.org/code_tables/639/data)
- `Teng` is the code for the script the resources are written in according to [ISO-15924](https://en.wikipedia.org/wiki/ISO_15924)

_CLoAn_ will then try to open find the file `<corpus_name>/<filename>`.<br>In our series of examples, this would be `C:/Users/Gimli/Documents/floresp-v2.0-rc.2/devtest/devtest.sjn_Teng`. This will look different for you, because **A.** you've stored it under a different directory (your username probably isn't Gimli) and **B.** you're not going to be annotating Sindarin.

</details> 

Most languages have multiple names (e.g. _Finnish_/_Suomi_). We want to make sure that _CLoAn_ uses the same name for each language consistently. When adding a new language to a corpus, you'll be shown all language-names known to _CLoAn_ so far. If your language is present in this list, you should select it, otherwise you can the name for your \"new\" language.

##### Fast Startup

You can skip the extensive startup-menu by providing the name of both the corpus and the language when you call the program.<br>

To do so, you need to use the appropriate flags:
- `-l`/`--language` for the language
- `-c`/`--corpus` for the corpus

<details>

**<summary>Example</summary>**

```bash
python annotate.py -c FLORES+devtest -l Sindarin
```

</details>

If _CLoAn_ can find all the necessary files and configuration parameters, this will take you directly to the annotation. Otherwise, you might be asked to provide additional information such as paths and filenames.

## Annotating

Now to the actually important part: Annotating.

### Goal

Before walking you through the process, it makes sense to let you know what the goal of all this work is.

The aim of this annotation is to obtain a **Borrowing-Contrastive Dataset**.<br>The final data in each language consists of sentence-pairs. In each pair, sentence _A_ will contain loanwords, while sentence _B_ will be the same sentence, but (ideally) have all its **loanwords replaced by native alternatives**.

| A: including loanwords                 | B: excluding loanwords                       |
|----------------------------------------|----------------------------------------------|
| He bought himself a new **rucksack**.      | He bought himself a new **backpack**.            |
| I lost sight of my **doppelgänger** en route. | I lost sight of my **look-alike** along the way. |
| ...**et cetera**                           | ...**and so on** |


<!-- ### Annotation Process -->

### Marking
You'll go through each sentence of your target language in the corpus (most likely _FLORES+devtest_). Along with each sentence, you're presented with a multiselect-menu with two options:
- Does the sentence contain any **striking and replaceable** loanwords?
- Does the sentence contain any **replaceable** native words?

> [!HINT]
 > You can navigate it with the arrow-keys or \<j\> & \<k\> (\<j\>=down, \<k\>=up). To select/unselect an item, use the space-bar. Once you're done, press ENTER.

Select all options that are true for the current sentence. CLoAn will then automatically take you through the substeps that correspond to your selection.


> **Note**
 > There might be some strange and unexpected characters (`@`) in your sentence. You need not worry about this. To flag loanwords more effectively, sentences are tokenized first. These additional symbols are used to put the sentence back together when it is stored in the final output. Just ignore these special characters.
<!-- **WARNING:** You can only move forward through the corpus. Once you've made your choice, you can't go back to change your answers. -->

<br>Here are some more details about what exactly is meant by loanwords:


<details>

**<summary> Loanwords </summary>**

<!-- #### What are Loanwords? -->
<!-- <details>  -->

<!-- **<summary>Definition </summary>** -->
> **Definition**(from [Wikipedia](https://en.wikipedia.org/wiki/Loanword)): <br>
_"A loanword is a word at least partly assimilated from one language (the donor language) into another language (the recipient or target language), through the process of borrowing."_

<!-- </details> -->

We'll call words that are **not** borrowed _'native'_. Loanwords are hereafter also referred to as _borrowings_ or _loans_.

Some loanwords are easy to spot, others not quite. For example, many speakers of English could probably identify _cul-de-sac_  as a borrowing from French, but barely anyone would take note of _slogan_ ([from Scottish Gaelic _sluagh-ghairm](https://www.merriam-webster.com/dictionary/slogan#word-history)). As in this example, there is a big difference in how much the word has been changed to fit into the English language.

Initially, borrowings often refer to concepts that are novel in the target language. _Coffee_ is a loanword from Arabic, having arrived to the English languages alongside the drink and the roasted beans it refers to. Before that, there simply was no need for a word describing something nobody knew. Lacking any alternatives, we have no choice but to use the loanword in those kinds of cases.

If you, a speaker fluent in that language, can easily spot a word as a borrowing _**and**_ think of a suitable native alternative, then congrats, you've found a **obvious and replaceable** loanword! Any sentence containing one or more of these kinds of loans can be marked accordingly.

> Some examples: (loanwords in **bold**) <br>
>- :x: _The teacher was giving a lesson about **trigonometry**_ (from Greek; no suitable alternative)
>- :x: _Nike's **slogan** is very famous._ (most likely not an obvious loanword)
>- :white_check_mark: _We then visited the **plaza** in the city centre._ (from Spanish; _square_ is a suitable alternative)

Similarily, when you encounter a native word that you know has an **appropriate borrowed alternative**, 


These judgements will depend mainly on your intuition as a fluent speaker - both questions of how obviously borrowed a word _feels_ and of whether it has any adequate replacements in the current sentence. You are thus strongly encouraged to use your 'linguistic gut-feeling'.

As an aid, potential loanwords are highlighted in each sentence. Note that this highlighting is very rudimentary, as it just checks each word against a list of known loanwords (where such lists are available). It will mark some words as borrowed that aren't loanwords and certainly miss some that are.<br>**Do not fully rely on the highlighting!**

</details>


#### 2. Modifying a sentence

After you've marked a sentence, CLoAn continues to the corresponding next steps.

Your task now is to modify the sentences such that (where possible) all loanwords are replaced by native alternatives. _CLoAn_ does this in multiple substeps

##### Replace loanwords

In those languages where lists of known loanwords are available, the potential loanwords (= _candidates_) of each sentence will be flagged. 

For each of the candidates, you'll be presented with various options:
- `-SKIP LOANWORD-`: Do not replace the current word, leave it as is. Mostly when _A._ the candidate is not a loanword, or _B._ there is no adequate alternative
- `-CUSTOM INPUT-`: Replace it with a custom word.
- `-DISCARD SENTENCE ALTOGETHER-`: Skip the whole sentence, do **not save** any of it (including previous replacements!)

For some languages, _CLoAn_ is able to automatically suggest some alternatives. These will then also show up in the same menu.
- `Alternative 1`: The first alternative
- `Alternative 2`: The second alternative
- `...`


###### Option: `-CUSTOM INPUT-`

Here are some more details on how things work when you choose the `-CUSTOM INPUT-` option.

1. You will be asked to enter the selected alternative for the current candidate in its **lemma-form**.
<br> _CLoAn_ then does two things:
    - Internally, the candidate and the proposed alternative are stored in the _annotation-memory_. When you encounter the same loanword candidate again later, your custom alternative will be among the suggestions.
    - The sentence is modified: The candidate is replaced by the alternative.
2. Next, the modified sentence is pasted to the console. You can now edit the whole sentence to ensure it's well-formed and grammatical.<br>When you're finished, press ENTER.

##### Manual Replacement

Because the automatic detection **won't** catch all loanwords, you also have the option to replace words that haven't been flagged.

To keep track of all the replacements we make, manual replacement works in three consecutive steps:
1. Delete the loanword you want to replace. 
2. Enter the alternative (preferrably in lemma-form) in the appropriate place.
3. Edit the sentence to ensure it stays grammatical.

<details> 

**<summary>Example</summary>**

Goal: Replace _suave_ by _smooth_

Original sentence: <br>`I was convinced by a very suave salesman.` <br><br> → delete _suave_:<br>`I as convinced by a very  salesman.` <br><br> → insert _smooth_:<br>`I was convinced by a very smooth salesman.` <br><br> → edit (not necessary in this case):<br>`I was convinced by a very smooth salesman.`<br>

From now on, whenever _suave_ shows up in a sentence, _CLoAn_ will suggest _smooth_ as an alternative.

</details>

You can do multiple replacements in a given sentence.

##### Replace native words

Unless already replaced previously, native words won't be detected automatically. Therefore, replacing native words with loans follows the same principle as the [Manual Replacement](#manual-replacement).

### Results

The results will be stored in the following JSON-file:

```CLoAn/data/output/OUT_<corpus>_<language>.json```

For each modified sentence, it will store the original and the modified version of the sentence as strings. Additionally, the replacement operations made in each sentence are stored in dictionaries (`{loanword : alternative}` / `{alternative : loanword}`). The sentences themselves are indexed by their position in the corpus.
