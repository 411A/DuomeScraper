from playwright.async_api import (
    Playwright, async_playwright,
)
from playwright._impl._api_types import (
    TimeoutError as PWTimeOutErr,
)
import asyncio
from pathlib import Path
import re
from rich.console import Console
from rich import print as richprint
import random
from gtts import gTTS, gTTSError

import genanki
import json


DUOLINGO_WORDS_URL = "https://duome.eu/vocabulary/en/it"

# [
#   ['original_word', 'html_original_word', 'html_definition', 'category', 'html_category'],
#   [...]
# ]
LIST_WHOLE_WORDS_FOR_ANKI = list()

LIST_WHOLE_WORDS = list()

# e.g. EN-IT_3667.apkg
ANKI_APKG_FILENAME = "{ph_lang_code}_{ph_total_words}.apkg"
# e.g. ['EN', 'IT']
FOUND_LANGS = list()
# e.g. EN-IT_3667
VOICES_DIRECTORY_NAME = None

DICT_LANGS_CODES = {
    "EN": "English",
    "IT": "Italian",
}

DICT_COUNTRY_FLAGS = {
    "EN": "🇬🇧",
    "IT": "🇮🇹",
}


async def word2voice_using_google(
    word: str, lang_code: str
) -> None:
    
    '''
    Stores the voice of the given word on the given language.

    ### Parameters
        `word (str)`: The word the you want to store its voice.

        `lang_code (str)`: Language code of the word. e.g. `"it"` for Italian.
    '''

    global VOICES_DIRECTORY_NAME

    # Get Anki's apkg filename without its extension
    # Create a Path object from the filename
    path_obj_from_filename = Path(ANKI_APKG_FILENAME)

    # Get the filename stem (without extension) to use as the voices directory
    voices_directory_name = path_obj_from_filename.stem
    VOICES_DIRECTORY_NAME = voices_directory_name
    # Create the voices directory
    Path(voices_directory_name).mkdir(exist_ok=True)

    # Check if file is available in the directory
    # Create a Path object for the file
    voice_file_path = Path(voices_directory_name) / f"{word}.mp3"

    # Check if the file exists, don't download it again
    if voice_file_path.exists():
        return
    else:
        # If connection error happened, try again
        while True:
            try:
                tts = gTTS(
                    text=word,
                    # Make sure the lang_code is lower case
                    lang=lang_code.lower()
                )
                tts.save(f"{voices_directory_name}/{word}.mp3")
                break
            except gTTSError:
                richprint(f"Trying to get voice of [red]{word}[/red]")
                continue


async def prettifier_for_anki(
    type_of_text: str,
    text: str
) -> str:
    
    '''
    Takes type_of_text (original, definition or category) and returns the prettified string.

    ### Parameters
        `type_of_text (str)`: Can be one of `original`, `definition` or `category`.

        `text (str)`: The text to format as a HTML string.

    ### Returns
        `prettified_string (str)`: The HTML string of the given text.
    '''

    original_word_size = "30px"
    original_word_font_family = "Times New Roman"
    original_word_color = "blue"

    definition_text_size = "30px"
    definition_text_font_family = "Arial"
    definition_text_color = "black"

    if type_of_text.lower() == "original":

        prettified_string = f"""<center>
    <span style="font-weight: bold; font-size: {original_word_size}; font-family: {original_word_font_family}; color: {original_word_color};">
        {text}
    </span>
</center>"""
    elif type_of_text.lower() == "definition":
        prettified_string = f"""<center>
    <span style="font-size: {definition_text_size}; font-family: {definition_text_font_family}; color: {definition_text_color};">
        {text}
    </span>
</center>"""
    elif type_of_text.lower() == "category":
        prettified_string = f"""<center>
    <span>
        {text}
    </span>
</center>"""
    
    return prettified_string


async def pw_duome_scraper(playwright: Playwright) -> None:

    '''
    Scrapes the duome website's words, prettifies them using function `prettifier_for_anki` and stores them into the global variable `LIST_WHOLE_WORDS`.

    ### Parameters
        `playwright (Playwright)`: Takes the playwright's class to open the browser asynchronously.
    '''

    global ANKI_APKG_FILENAME, FOUND_LANGS

    # Get the path of the current script file (running Python)
    current_script_path = Path(__file__).resolve()
    # Use the resolved path to access the file or its parent directory
    resolve_persistent_dir = current_script_path.parent / "PersistentContext"

    browser_type = playwright.chromium
    browser = await browser_type.launch_persistent_context(
        user_data_dir=str(resolve_persistent_dir),
        headless=False,
        channel="msedge",
        #slow_mo=10,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.57",
        args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--disable-component-extensions-with-background-pages",
        ],
        # Set locale & timezone so websites always load in English
        locale="en-US",
        timezone_id="Europe/London"
    )

    page = await browser.new_page()

    # Set viewport size like a fake laptop
    await page.set_viewport_size({"width": 1244, "height": 830})

    # Extract language codes from the URL
    # Define the regex pattern to extract language codes
    extract_langcode_from_url_pattern = r"https://duome\.eu/vocabulary/([a-z]{2})/([a-z]{2})"

    # Use regular expression to extract language codes
    lang_code_matches = re.search(
        pattern=extract_langcode_from_url_pattern,
        string=DUOLINGO_WORDS_URL
    )
    language_codes_list = [lang.upper() for lang in lang_code_matches.groups()]
    LANGUAGE_CODE = "-".join(language_codes_list)
    FOUND_LANGS = language_codes_list

    await page.goto(
        url=DUOLINGO_WORDS_URL,
        wait_until="load",
        # Timeout: 3 minutes
        timeout=180000,
    )

    #* Get total available words count
    #? document.querySelector("small[class='cCCC']").textContent
    total_words_element = await page.query_selector(
        selector="small[class='cCCC']"
    )
    total_words_text = str(await total_words_element.text_content())
    total_words = int(
        re.search(
            pattern=r"\b\d+\b",
            string=total_words_text,
        ).group()
    )

    # Generate the Anki apkg filename
    ANKI_APKG_FILENAME = ANKI_APKG_FILENAME.format(
        ph_lang_code=LANGUAGE_CODE,
        ph_total_words=total_words,
    )

    #* Get a list of all words (li elements), exclude header alphabets that have class='single' 
    #? document.querySelectorAll("div[id='words'] li:not(.single)")
    # or: const word_element = document.querySelectorAll("div[id='words'] li:not(.single)")[0];

    all_visible_words_element = await page.query_selector_all(
        selector="div[id='words'] li:not(.single)",
    )
    # Colorize the final word count
    if len(all_visible_words_element) == total_words:
        colorized_word_count_result = "green"
    elif len(all_visible_words_element) < total_words:
        # FFC411 = orange
        colorized_word_count_result = "#FFC411"
    richprint(
        f"[bold]Total Words Found: [{colorized_word_count_result}]{len(all_visible_words_element)}[/{colorized_word_count_result}]/[green]{total_words}[/green][/bold] (Visible Words Elements/Total Words)"
    )

    rich_console = Console()

    # Iterate through elements & access their attributes|content
    for i, word_element in enumerate(all_visible_words_element):

        """ if i == 100:
            break """

        # end="\r" to print on same line as before (no print on newline, updating current line)
        rich_console.print(f"[bold][red]   Scarping Words:[/red] [#C5FF33]{i + 1}[/#C5FF33]/[green]{total_words}[/green][/bold]", end="\r")
        
        # List of current word (word, definition, category)
        LIST_CURRENT_WORD = list()

        #* Access original word
        #? word_element.querySelector("span[class='hide wN']").textContent
        original_word_element = await word_element.query_selector(
            selector="span[class='hide wN']"
        )
        original_word = str(await original_word_element.text_content())
        #* Access original word with phonetic symbols (e.g. ò)
        #? word_element.querySelector("span[class='speak xs voice']").textContent
        original_phoneticword_element = await word_element.query_selector(
            selector="span[class='speak xs voice']"
        )
        original_phoneticword = str(await original_phoneticword_element.text_content())
        # Make it beautiful to be used in Anki using HTML-CSS!
        pretty_original_word = await prettifier_for_anki(
            type_of_text="original",
            text=original_phoneticword
        )
        LIST_WHOLE_WORDS.append(original_phoneticword)
        LIST_CURRENT_WORD.append(original_phoneticword)
        LIST_CURRENT_WORD.append(pretty_original_word)
        #print(original_word)

        #* Store the pronunciation of the word as mp3
        await word2voice_using_google(
            word=original_phoneticword,
            lang_code=FOUND_LANGS[1]
        )

        #* Access definition (displayed on hover on the word)
        #? word_element.querySelector("span[class='wA']").getAttribute("title")
        word_definition_element = await word_element.query_selector(
            selector="span[class='wA']"
        )
        word_definition = str(
            await word_definition_element.get_attribute(
                name="title"
            )
        )
        #* Remove the [original_word] from the definition, only from the beginnig of the string
        word_definition = re.sub(
            # Remove the [original_word] and any whitespace after it
            pattern=rf"\[{original_word}\]\s*",
            repl="",
            string=word_definition,
            # Only from the beginning of the text
            count=1,
        )
        # Make it beautiful to be used in Anki using HTML-CSS!
        pretty_word_definition = await prettifier_for_anki(
            type_of_text="definition",
            text=word_definition
        )
        LIST_CURRENT_WORD.append(pretty_word_definition)
        #print(word_definition)

        #* Access word category (part of speech), like: Adverb, must remove "·  " from the string
        #? word_element.querySelector("small[class='cCCC wP']").textContent
        word_category_element = await word_element.query_selector(
            selector="small[class='cCCC wP']"
        )
        word_category_text = str(await word_category_element.text_content())
        #* Remove the dot and any number of whitespaces it have, only from the beginning of the string
        word_category = re.sub(
            # Remove the dot and any number of whitespaces it have
            pattern=r"·\s*",
            repl="",
            string=word_category_text,
            # Only from the beginning of the text
            count=1,
        )
        # Make it beautiful to be used in Anki using HTML-CSS!
        pretty_word_category = await prettifier_for_anki(
            type_of_text="category",
            text=word_category
        )
        LIST_CURRENT_WORD.append(word_category)
        LIST_CURRENT_WORD.append(pretty_word_category)
        #print(word_category)

        #print("🔶" * 10)
        
        # Append the collected list of current word to the main list of words
        LIST_WHOLE_WORDS_FOR_ANKI.append(LIST_CURRENT_WORD)
        LIST_CURRENT_WORD = list()

    #* Write Whole Words List to a file
    # Store the list in a file using JSON
    with open("original_words_list.json", "w", encoding="utf-8") as file:
        json.dump(LIST_WHOLE_WORDS, file)


async def anki_apkg_file_generator() -> None:

    '''
    Generates Anki's `.apkg` file based on three global variables: `ANKI_APKG_FILENAME`, `LANGUAGE_CODE`, `TOTAL_WORDS` by iterating over the list of lists (`LIST_WHOLE_WORDS`).
    '''

    global ANKI_APKG_FILENAME, FOUND_LANGS, DICT_COUNTRY_FLAGS

    # Generate a random unique ID
    random_model_id = random.randint(1, 999999999)

    # Create a model for the Anki deck
    model = genanki.Model(
        # Use a unique ID
        model_id=random_model_id,
        name=f"Duolingo's {DICT_LANGS_CODES[FOUND_LANGS[1]]} to {DICT_LANGS_CODES[FOUND_LANGS[0]]} Words",
        # Define the fields that each flashcard will have.
        # Each field is represented as a dictionary with a single key 'name' and a corresponding value indicating the name of the field.
        fields=[
            {"name": "Word"},
            {"name": "Definition"},
            {"name": "Category"},
        ],
        # Templates determine how the front and back of the flashcards will be formatted.
        # Each template is a dictionary with attributes that define the formatting for both the question (qfmt) and answer (afmt) sides of the card.
        templates=[
            {
                # Specifies the name of the template.
                "name": f"Duolingo {DICT_LANGS_CODES[FOUND_LANGS[1]]}-{DICT_LANGS_CODES[FOUND_LANGS[0]]}",
                # "qfmt" Defines the format of the question side of the card.
                # It uses the {{Word}} field to display the original word content on the question side.
                "qfmt": "{{Word}}",
                # "afmt" Defines the format of the answer side of the card.
                # It starts with {{FrontSide}} to show the content that's on the question side, followed by an HTML <hr> element with the id attribute set to "category", This is used as a separator line (horizontal rule).
                # Then, it displays the "Category" field and the "Definition" field.
                "afmt": "{{FrontSide}}<hr id='category'>{{Category}}<br>{{Definition}}",
            },
        ]
    )

    # Generate a random unique ID
    random_deck_id = random.randint(1, 999999999)

    # Create the Anki deck
    deck = genanki.Deck(
        # Use a unique ID
        deck_id=random_deck_id,
        name=f"Duolingo's {DICT_LANGS_CODES[FOUND_LANGS[1]]} to {DICT_LANGS_CODES[FOUND_LANGS[0]]} Vocabulary",
        description=f"Scraped from: {DUOLINGO_WORDS_URL}"
    )

    # Add cards to the deck
    for original_word, html_original_word, html_definition, category, html_category in LIST_WHOLE_WORDS_FOR_ANKI:
        # Replace consecutive whitespaces and non-word characters with underscores
        category_as_tag = re.sub(
            # Replace spaces with underscores, except at the beginning or end of words
            pattern=r"(?<=\S) +(?!$)",
            repl="_",
            string=category
        )
        # Replace consecutive underscores with a single underscore
        category_as_tag = re.sub(
            # Remove spaces at the beginning or end of words
            pattern=r"^ +| +$",
            #repl="_",
            repl="",
            string=category_as_tag
        )
        note = genanki.Note(
            model=model,
            # Add note with the word's voice in the top-center of each card
            fields=[f"<center>[sound:{original_word}.mp3]</center>\n{html_original_word}", html_definition, html_category],
            # Add category as tag to distinguish each word
            tags=[f"{DICT_COUNTRY_FLAGS[FOUND_LANGS[1]]}{DICT_LANGS_CODES[FOUND_LANGS[1]]}", category_as_tag]
        )
        deck.add_note(note)

    # Create a package and save it to a file
    package = genanki.Package(deck)
    # Get a list of all file names in the directory
    voices_dir_path = Path(VOICES_DIRECTORY_NAME)
    list_of_all_voices_media = [f"{VOICES_DIRECTORY_NAME}/{file.name}" for file in voices_dir_path.iterdir() if file.is_file()]
    package.media_files = list_of_all_voices_media
    package.write_to_file(ANKI_APKG_FILENAME)
    richprint(f"✅ Successfully created file: {ANKI_APKG_FILENAME} from {len(LIST_WHOLE_WORDS_FOR_ANKI)} words.")


async def main():

    '''
    Runs the functions that have `Playwright` as parameter, then runs other necessary functions after closing the browser.
    '''

    async with async_playwright() as playwright:

        await pw_duome_scraper(
            playwright=playwright
        )

    # As of now, all constant variables are ready, generate the apkg file
    await anki_apkg_file_generator()

# Run the async function
asyncio.run(
    main()
)