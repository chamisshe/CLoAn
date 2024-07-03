# README

## What is CLoAn?

_CLoAn_ stands for _**C**ontrastive **Lo**anword **An**notator_. It is an annotation tool to create contrastive bitext, with one side containing loanwords and the other only "native" alternatives. It is part of my Bachelor's Thesis.

## Installing

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

## Bugs and other Issues
_CLoAn_ is by no means bug-free (barely any software is). Bugs encountered during development are mostly accounted for and handled, but that most likely doesn't include every possible edge case. For any bugs or inconveniences you may encounter, or suggestions for improvement, you can either [open an Issue](https://github.com/chamisshe/CLoAn/issues/new) or [write me an email.](mailto:michadavid.hess@uzh.ch)
