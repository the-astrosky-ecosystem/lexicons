from pathlib import Path

WORKING_DIRECTORY = Path(__file__).parent.parent.parent / ".temp"
WORKING_DIRECTORY.mkdir(exist_ok=True, parents=False)

LEXICON_DIRECTORY = WORKING_DIRECTORY.parent / "lexicons"
