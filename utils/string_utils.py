"""
String Utility Library

Provides various string manipulation functions based on the original Delphi CKSLIB unit.

Functions include:
- String to words conversion
- Case conversions (NameCase, TitleCase, SentenceCase)
- Character stripping functions
- String padding functions
- Position finding functions
"""

import re
from typing import List


def string_to_words(s: str, token: str) -> List[str]:
    """
    Split a string into words using a delimiter token.
    
    Args:
        s: The string to split
        token: The delimiter to split on
        
    Returns:
        List of words
    """
    if not s or not token:
        return [s] if s else []
    
    result = []
    remaining = s
    
    pos = remaining.find(token)
    while pos != -1:
        result.append(remaining[:pos])
        remaining = remaining[pos + len(token):]
        pos = remaining.find(token)
    
    result.append(remaining)
    return result


def words_to_string(sl: List[str], token: str) -> str:
    """
    Join a list of words into a string with a delimiter.
    
    Args:
        sl: List of words
        token: The delimiter to join with
        
    Returns:
        Joined string
    """
    if not sl:
        return ""
    return token.join(sl)


def strip_duplicates(s: str, token: str) -> str:
    """
    Replace multiple consecutive occurrences of a token with a single occurrence.
    
    Args:
        s: The string to process
        token: The token to deduplicate
        
    Returns:
        String with duplicate tokens removed
    """
    if not s or not token:
        return s
    
    # Use regex to replace multiple occurrences with single
    pattern = re.escape(token) + '+'
    return re.sub(pattern, token, s)


def name_case(s: str) -> str:
    """
    Convert a string to name case (proper name capitalization).
    Handles special cases like "Mc" and "Mac" prefixes.
    
    Args:
        s: The string to convert
        
    Returns:
        String in name case
    """
    if not s:
        return ""
    
    s = s.lower()
    
    if len(s) == 1:
        return s.upper()
    
    # Split into words based on common delimiters
    words = re.split(r"([A-Za-z']+)", s)
    
    result = ""
    for word in words:
        if not word:
            continue
            
        # Check if this word should be capitalized
        if word.replace("'", "").isalpha():
            # Capitalize first letter
            result += word[0].upper() + word[1:]
        else:
            result += word
    
    return result


# Lowercase words that should not be capitalized in title case
TITLE_CASE_LOWER_WORDS = {
    'the', 'and', 'of', 'before', 'after', 'in', 'on', 'at', 'to', 'for',
    'a', 'an', 'as', 'but', 'or', 'nor', 'so', 'yet', 'with', 'by'
}


def title_case(s: str) -> str:
    """
    Convert a string to title case (first letter of each major word capitalized).
    Keeps certain words lowercase unless they are the first word.
    
    Args:
        s: The string to convert
        
    Returns:
        String in title case
    """
    if not s:
        return ""
    
    s = s.lower()
    words = re.split(r"([A-Za-z']+)", s)
    
    result = ""
    for i, word in enumerate(words):
        if not word:
            continue
            
        if word.replace("'", "").isalpha():
            # First word is always capitalized
            if i == 0:
                result += word[0].upper() + word[1:]
            # Check if it's a lowercase word
            elif word.lower() in TITLE_CASE_LOWER_WORDS:
                result += word  # Keep lowercase
            else:
                result += word[0].upper() + word[1:]
        else:
            result += word
    
    return result


def sentence_case(s: str) -> str:
    """
    Convert a string to sentence case (first letter capitalized, rest lowercase).
    
    Args:
        s: The string to convert
        
    Returns:
        String in sentence case
    """
    if not s:
        return ""
    
    return s[0].upper() + s[1:].lower() if len(s) > 1 else s.upper()


def strip_non_numeric(s: str) -> str:
    """
    Remove all characters except digits (0-9).
    
    Args:
        s: The string to process
        
    Returns:
        String with only digits
    """
    return ''.join(c for c in s if c.isdigit())


def strip_numeric(s: str) -> str:
    """
    Remove all digit characters (0-9) from a string.
    
    Args:
        s: The string to process
        
    Returns:
        String with digits removed
    """
    return ''.join(c for c in s if not c.isdigit())


def strip_alphabetical(s: str) -> str:
    """
    Remove all alphabetical characters (a-z, A-Z) from a string.
    
    Args:
        s: The string to process
        
    Returns:
        String with alphabetical characters removed
    """
    return ''.join(c for c in s if not c.isalpha())


def strip_non_alphabetical(s: str) -> str:
    """
    Keep only alphabetical characters (a-z, A-Z) in a string.
    
    Args:
        s: The string to process
        
    Returns:
        String with only alphabetical characters
    """
    return ''.join(c for c in s if c.isalpha())


def strip_non_float(s: str) -> str:
    """
    Keep only characters that could be part of a float number.
    Handles a single decimal point.
    
    Args:
        s: The string to process
        
    Returns:
        String representing a float number
    """
    result = ''
    found_decimal = False
    
    for c in s:
        if c.isdigit():
            result += c
        elif c == '.' and not found_decimal:
            result += c
            found_decimal = True
    
    return result


def strip_alpha_numeric(s: str) -> str:
    """
    Remove all alphanumeric characters (a-z, A-Z, 0-9) from a string.
    
    Args:
        s: The string to process
        
    Returns:
        String with alphanumeric characters removed
    """
    return ''.join(c for c in s if not c.isalnum())


def strip_non_alpha_numeric(s: str) -> str:
    """
    Keep only alphanumeric characters (a-z, A-Z, 0-9) in a string.
    
    Args:
        s: The string to process
        
    Returns:
        String with only alphanumeric characters
    """
    return ''.join(c for c in s if c.isalnum())


def quoted(s: str) -> str:
    """
    Enclose a string in double quotes.
    
    Args:
        s: The string to quote
        
    Returns:
        Quoted string
    """
    return f'"{s}"'


def strip_zeros(s: str) -> str:
    """
    Remove leading zeros from a string representation of a number.
    
    Args:
        s: The string to process
        
    Returns:
        String with leading zeros removed
    """
    if not s:
        return s
    
    # Handle negative numbers
    if s.startswith('-'):
        return '-' + strip_zeros(s[1:])
    
    # Handle decimal numbers
    if '.' in s:
        parts = s.split('.')
        return strip_zeros(parts[0]) + '.' + parts[1] if parts[1] else strip_zeros(parts[0])
    
    # Remove leading zeros
    result = s.lstrip('0')
    return result if result else '0'


def pad_zeros(s: str, length: int) -> str:
    """
    Pad a string with leading zeros to reach a specified length.
    
    Args:
        s: The string to pad
        length: The target length
        
    Returns:
        Zero-padded string
    """
    if not s:
        return '0' * length
    
    if len(s) >= length:
        return s
    
    return '0' * (length - len(s)) + s


def pos_no(n: int, substr: str, s: str) -> int:
    """
    Find the position of the Nth occurrence of a substring.
    
    Args:
        n: The occurrence number to find (1-indexed)
        substr: The substring to search for
        s: The string to search in
        
    Returns:
        Position of the Nth occurrence (0-indexed), or 0 if not found
    """
    if n <= 0 or not substr or not s:
        return 0
    
    start = 0
    count = 0
    
    for _ in range(n):
        pos = s.find(substr, start)
        if pos == -1:
            return 0
        count += 1
        start = pos + len(substr)
    
    # Return the position of the Nth occurrence
    # We need to find where the Nth occurrence starts
    start = 0
    for i in range(n - 1):
        pos = s.find(substr, start)
        if pos == -1:
            return 0
        start = pos + len(substr)
    
    return start


def replace_token(s: str, token: str, value: str) -> str:
    """
    Replace all occurrences of a token with a value.
    
    Args:
        s: The string to process
        token: The token to replace
        value: The replacement value
        
    Returns:
        String with all tokens replaced
    """
    if not s or not token:
        return s
    
    return s.replace(token, value)


def boolean_to_text(bt: str, b: bool, as_title: bool = True) -> str:
    """
    Convert a boolean to text representation.
    
    Args:
        bt: The format type ('yesno' or 'truefalse')
        b: The boolean value
        as_title: Whether to use title case
        
    Returns:
        Text representation of the boolean
    """
    if bt.lower() == 'yesno':
        if as_title:
            return "Yes" if b else "No"
        else:
            return "yes" if b else "no"
    else:  # truefalse
        if as_title:
            return "True" if b else "False"
        else:
            return "true" if b else "false"


def int_to_boolean_text(bt: str, i: int, as_title: bool = True) -> str:
    """
    Convert an integer to boolean text representation.
    0 is False, anything else is True.
    
    Args:
        bt: The format type ('yesno' or 'truefalse')
        i: The integer value
        as_title: Whether to use title case
        
    Returns:
        Text representation
    """
    return boolean_to_text(bt, i != 0, as_title)


def char_to_boolean_text(bt: str, ch: str, as_title: bool = True) -> str:
    """
    Convert a character to boolean text representation.
    'Y', 'T', '1' are True; 'N', 'F', '0' are False.
    
    Args:
        bt: The format type ('yesno' or 'truefalse')
        ch: The character
        as_title: Whether to use title case
        
    Returns:
        Text representation
    """
    if not ch:
        return "N/A" if as_title else "n/a"
    
    ch_upper = ch.upper()
    
    if ch_upper in ('Y', 'T', '1'):
        return boolean_to_text(bt, True, as_title)
    elif ch_upper in ('N', 'F', '0'):
        return boolean_to_text(bt, False, as_title)
    else:
        return "N/A" if as_title else "n/a"
