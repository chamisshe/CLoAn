import time

from rich.console import Console
from styles import yellow

console = Console()


def typewriter(sentence: str):
    for char in sentence:
        console.print(char, end="")
        time.sleep(0.5)

def demo(console: Console):
    console.print(yellow("TBD: this would be the demo"))
    time.sleep(5.0)
    pass


a_string = "aaaa"
print(a_string.capitalize())