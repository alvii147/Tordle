import re
import requests
import random
from collections import Counter
import textwrap
from art import text2art
from termcolor import colored

WORD_LENGTH = 5
FIVE_LETTER_WORD_API = 'https://www-cs-faculty.stanford.edu/~knuth/sgb-words.txt'
DICTIONARY_API = 'https://api.dictionaryapi.dev/api/v2/entries/en'
REQUEST_ATTEMPTS_LIMIT = 5

CLUE_COLORS = {
    # correct letter & position
    'C': 'green',
    # correct letter, wrong position
    'L': 'yellow',
    # wrong letter, wrong position
    'W': 'white',
}
ATTEMPTS_COLOR = 'yellow'
PROMPT_COLOR = 'cyan'
ERROR_COLOR = 'magenta'
GAME_OVER_COLOR = 'red'
SUCCESS_COLOR = 'green'

WORD_COLOR = 'cyan'
PHONETIC_COLOR = 'magenta'
PART_OF_SPEECH_COLOR = 'yellow'
DEFINITION_COLOR = 'blue'

TURTLE_ASCII_ART = '''
  _____     ____
 /      \  |  o | 
|        |/ ___\| 
|_________/     
|_|_| |_|_|
'''

def colorize_multiline_art(letter, color, attrs=[]):
    letter_lines = letter.split('\n')

    colored_letter_lines = []
    for line in letter_lines:
        colored_letter_lines.append(
            colored(
                line,
                color,
                attrs=attrs,
            )
        )

    colored_letter = '\n'.join(colored_letter_lines)

    return colored_letter

def colorize_word_art(word, colors):
    if (not isinstance(colors, str)) and len(word) != len(colors):
        raise ValueError('`word` and `colors` must have the same lengths')

    if isinstance(colors, str):
        colors_list = [colors] * len(word)
    else:
        colors_list = colors.copy()

    colored_word = ''
    for i in range(len(word)):
        block_letter = text2art(word[i], font='block', chr_ignore=False)
        colored_letter = colorize_multiline_art(
            block_letter,
            colors_list[i],
            attrs=['bold'],
        )

        if i == 0:
            colored_word = colored_letter
        else:
            colored_word = concat_letters(
                colored_word,
                colored_letter,
            )

    return colored_word

def concat_letters(letter1, letter2):
    letter1_lines = letter1.split('\n')
    letter2_lines = letter2.split('\n')

    if len(letter1_lines) != len(letter2_lines):
        raise ValueError('Unable to match lines')

    concat_lines = []
    for letter1_line, letter2_line in zip(letter1_lines, letter2_lines):
        concat_lines.append(letter1_line + letter2_line)

    concat_letters = '\n'.join(concat_lines)

    return concat_letters

def get_clue_colors(clues):
    clue_colors = [CLUE_COLORS[i] for i in clues]

    return clue_colors

def get_clues(correct_word, attempted_word):
    if len(correct_word) != len(attempted_word):
        raise ValueError(f'Attempted word must be of length {len(correct_word)}')

    clues = ['W'] * len(correct_word)
    letter_count = Counter(correct_word)
    all_correct = True
    for i in range(len(correct_word)):
        if correct_word[i] == attempted_word[i]:
            clues[i] = 'C'
            letter_count[correct_word[i]] -= 1
        else:
            all_correct = False

    for i in range(len(correct_word)):
        if clues[i] == 'C':
            continue

        if attempted_word[i] in correct_word:
            if letter_count[attempted_word[i]] > 0:
                clues[i] = 'L'
                letter_count[attempted_word[i]] -= 1

    clues = ''.join(clues)

    return clues, all_correct

def get_words():
    response = requests.get(FIVE_LETTER_WORD_API)
    words = response.text.split('\n')
    words = [word.strip().upper() for word in words if len(word.strip()) > 0]

    return words

def get_word_meaning(word):
    response = requests.get(DICTIONARY_API + '/' + word)
    word_meaning = response.json()[0]

    return word_meaning

def format_meaning(word_meaning):
    formatted_meaning = colored(word_meaning.get('word', ''), WORD_COLOR)
    phonetic = word_meaning.get('phonetic')
    if phonetic is not None:
        phonetic = '(' + phonetic + ')'
    else:
        phonetic = ''
    formatted_meaning += ' '
    formatted_meaning += colored(phonetic, PHONETIC_COLOR)

    for meaning in word_meaning.get('meanings', []):
        formatted_meaning += '\n' + colored('[' + meaning['partOfSpeech'] + ']', PART_OF_SPEECH_COLOR)
        for definition in meaning['definitions']:
            formatted_definition = textwrap.fill(colored(definition['definition'], DEFINITION_COLOR), 72)
            formatted_definition = formatted_definition.split('\n')
            formatted_definition = ['\n  - ' + d if i == 0 else '    ' + d for i, d in enumerate(formatted_definition)]
            formatted_definition = '\n'.join(formatted_definition)
            formatted_meaning += formatted_definition

    formatted_meaning += '\n'
    formatted_meaning = re.sub(r'[^\x00-\x7F]+', ' ', formatted_meaning)

    return formatted_meaning

if __name__ == '__main__':
    request_attempts = 0
    while True:
        try:
            words = get_words()
            random_word = random.choice(words)
            word_meaning = get_word_meaning(random_word)
            break
        except requests.exceptions.ConnectionError:
            if request_attempts < REQUEST_ATTEMPTS_LIMIT:
                print('Retrying, please check your internet connection')
                request_attempts += 1
            else:
                raise requests.exceptions.ConnectionError('Please check your internet connection')
        except KeyError:
            if request_attempts < REQUEST_ATTEMPTS_LIMIT:
                request_attempts += 1
            else:
                raise ValueError(f'Please check the validity of the API endpoint {DICTIONARY_API}')

    tordle_title = colorize_word_art(
        'TORDLE',
        ['magenta', 'red', 'yellow', 'green', 'blue', 'cyan'],
    )
    print(tordle_title)

    turtle_art = colorize_multiline_art(
        TURTLE_ASCII_ART,
        'green',
        attrs=['bold'],
    )
    print(turtle_art)

    attempts = 6
    while attempts > 0:
        print(colored(f'{attempts} attempts remaining', ATTEMPTS_COLOR))
        attempted_word = input(colored('Enter a 5-letter word: ', PROMPT_COLOR)).upper()
        if attempted_word not in words:
            print(colored('Not in the word list, try again\n', ERROR_COLOR))
        else:
            clues, all_correct = get_clues(random_word, attempted_word)
            clue_colors = get_clue_colors(clues)
            colored_word = colorize_word_art(attempted_word, clue_colors)
            print(colored_word)
            if all_correct:
                print(colored('You got it!', SUCCESS_COLOR))
                print('')
                break

            attempts -= 1

    if attempts == 0:
        print(colored('Game over, better luck next time! The word was ...', GAME_OVER_COLOR))
        colored_word = colorize_word_art(
            random_word,
            GAME_OVER_COLOR,
        )
        print(colored_word)

    print(format_meaning(word_meaning))
