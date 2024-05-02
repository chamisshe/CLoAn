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

class SaveAndMoveOn(Exception):
    """Save what can be saved, move on with the next sentence"""

class PreviousSentence(Exception):
    """Go back a single sentence."""