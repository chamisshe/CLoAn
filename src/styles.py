from rich.style import Style
from rich.highlighter import Highlighter
from rich.text import Text
from questionary import Style as qstyle

SENT_STYLE = Style(dim=True)
MARK_LW = Style(color="#000000", bold=True, frame=True,bgcolor="white")
YELLOW = Style(color="yellow", bold=True)


YELLOW = Style(color="yellow", bold=True)
YELLOWLIGHT = Style(color="yellow")
ORANGELIGHT = Style(color="#fc9e32")
class MakeYellow(Highlighter):
    def highlight(self, text: Text) -> None:
        text.stylize(style=YELLOW)
        return super().highlight(text)

class MakeYellowLight(Highlighter):
    def highlight(self, text: Text) -> None:
        text.stylize(style=YELLOWLIGHT)
        return super().highlight(text)

class MakeOrangeLight(Highlighter):
    def highlight(self, text: Text) -> None:
        text.stylize(style=ORANGELIGHT)
        return super().highlight(text)
orange_light = MakeOrangeLight()
yellow = MakeYellow()
yellow_light = MakeYellowLight()


########## QUESTIONARY STYLES ###########
default_select_style = qstyle([
    ('qmark', 'fg:#673ab7 bold'),       # token in front of the question
    ('question', 'fg:ansiyellow'),
    ('answer', 'fg:ansibrightmagenta bold'),      # submitted answer text behind the question
    ('pointer', 'fg:#673ab7 bold'),     # pointer used in select and checkbox prompts
    # ('highlighted', 'fg:black bg:ansibrightmagenta bold'),
    ('highlighted', 'fg:ansibrightmagenta bold'),
    # ('highlighted', 'fg:#673ab7 bold'), # pointed-at choice in select and checkbox prompts
    ('selected', 'fg:#cc5454'),         # style for a selected item of a checkbox
    ('separator', 'fg:#cc5454'),        # separator in lists
    ('instruction', ''),                # user instructions for select, rawselect, checkbox
    ('text', ''),                       # plain text
    ('disabled', 'fg:#858585 italic')
])

interrupt_style = qstyle([
    ('question', 'fg:ansiyellow'),
    ('highlighted', 'fg:ansibrightred bold'),
    ('answer', 'fg:ansibrightmagenta bold'),      # submitted answer text behind the question
])