import nltk
from nltk.tokenize import word_tokenize
from nltk.stem import SnowballStemmer
import string

nltk.download('punkt_tab')
stopwords = {'yourselves', "haven't", 'our', "you'd", 'whom', 'on', 'but', 'through', 'further', 'theirs', 'the', 's', 'him', "she's", 'from', 'myself', 'aren', 'yours', 'ours', 'such', 'yourself', 'between', 'were', 'if', 'her', 'd', "weren't", 'more', 'ain', 'being', "shouldn't", 'most', 'couldn', 'here', 'ma', "they've", 'doing', 'off', 'above', "we'd", 'has', 'and', "isn't", 'should', 'its', 'll', 'or', 'each', 'needn', 'o', "couldn't", 'did', "that'll", 'this', 'into', 'what', "he's", 'will', 'herself', 'had', "she'll", 'than', 'an', 'do', "i'm", "should've", 'i', 'while', 'over', 'because', 'a', 'too', 'again', 'having', 'nor', 'hers', 'me', 'she', "they're", 'does', "we've", "hadn't", "wouldn't", "i've", 'after', "doesn't", 're', 'weren', 'other', 'down', 'wasn', 'ourselves', 'in', 'isn', 'own', 'them', 'have', 'didn', 'don', 'his', 'before', 'y', "i'd", 'mustn', 'you', 'are', "won't", 'until', 'there', 'how', 'under', 'am', 'himself', "they'd", 've', "you've", 'to', "he'd", "mightn't", 'shouldn', 'any', 'shan', 'very', 'been', 'out', 't', 'only', 'both', 'mightn', "don't", "it'd", "aren't", "didn't", 'few', 'just', "she'd", 'their', "they'll", "mustn't", 'with', 'hasn', 'not', "wasn't", "we're", 'about', "it's", 'your', 'below', 'of', "needn't", 'when', 'where', 'now', 'hadn', 'we', 'against', 'wouldn', 'these', "hasn't", 'up', 'my', "shan't", 'be', 'no', 'then', 'that', 'it', 'is', 'he', 'for', 'm', 'they', "you'll", 'themselves', 'why', 'those', 'was', 'once', 'doesn', 'same', 'during', 'all', 'as', 'so', "we'll", "he'll", "you're", 'itself', "it'll", 'at', 'which', 'haven', 'by', 'can', 'some', 'won', "i'll", 'who'}

def normalize(input: str) -> str:
    """Noramlize the given input string by removing puntuations and making it lowercase.

    Args:
        input (str): Input string to be normalized.
    Returns:
        str: Normalized string.
    """

    input = input.lower()
    new_input = ""
    for char in input:
        if char not in string.punctuation:
            new_input += char
    return new_input

def tokenize_lexical(input: str, lang: str = "english") ->  list[str]:
    """Tokenize the given input string into a list of words. Performs lowercasing, punctuation removal, stopword removal, and stemming.

    Args:
        input (str): Input string to be tokenized.
        lang (str): Language of the input string.
    Returns:
        list[str]: List of tokenized words.
    """

    stemmer = SnowballStemmer(lang)
    normalized_input = normalize(input)
    tokens = word_tokenize(normalized_input)
    tokens = [token for token in tokens if token not in stopwords]
    tokens = [stemmer.stem(token) for token in tokens]
    return tokens

def tokenize_semantic(input: str, lang: str = "english") -> list[str]:
    """Tokenize the given input string into a list of words. Performs lowercasing and punctuation removal.

    Args:
        input (str): Input string to be tokenized.
        lang (str): Language of the input string.
    Returns:
        list[str]: List of tokenized words.
    """

    normalized_input = normalize(input)
    tokens = word_tokenize(normalized_input)
    return tokens

def tokenize_symspell(input: str, lang: str = "english") -> list[str]:
    """Tokenize the given input string into a list of words. Performs lowercasing, stopword removal, and punctuation removal.

    Args:
        input (str): Input string to be tokenized.
        lang (str): Language of the input string.
    Returns:
        list[str]: List of tokenized words.
    """

    normalized_input = normalize(input)
    tokens = word_tokenize(normalized_input)
    tokens = [token for token in tokens if token not in stopwords]
    return tokens