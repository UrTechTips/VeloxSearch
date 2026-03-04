from app.services import tokenizer as tokmod

# Tests for the normalize function
def test_normalize_basic():
    input_str = "Hello, World! This is a Test."
    expected_output = "hello world this is a test"
    assert tokmod.normalize(input_str) == expected_output

def test_normalize_empty_and_punctuation_only():
    assert tokmod.normalize("") == ""
    assert tokmod.normalize("!!!???,,,...") == ""

def test_normalize_apostrophes_and_case():
    assert tokmod.normalize("Don't STOP") == "dont stop"

# Tests for the tokenize function
def test_tokenize_basic_stemming_and_stopwords(monkeypatch):
    monkeypatch.setattr(tokmod, "word_tokenize", lambda s: s.split())

    mapping = {
        'running': 'run',
        'runners': 'runner',
        'ran': 'ran',
        'rapidly': 'rapid',
        'this': 'this',
        'is': 'is',
        'simple': 'simpl',
        'test': 'test',
        'tokenizer': 'token'
    }

    class FakeStemmer:
        def __init__(self, lang):
            self.lang = lang

        def stem(self, token):
            return mapping.get(token, token)

    monkeypatch.setattr(tokmod, 'SnowballStemmer', lambda lang: FakeStemmer(lang))

    input_str = "Running runners ran rapidly."
    expected = ['run', 'runner', 'ran', 'rapid']
    assert tokmod.tokenize_lexical(input_str) == expected

    input_str2 = "This is a simple test of the tokenizer."
    expected2 = ['simpl', 'test', 'token']
    assert tokmod.tokenize_lexical(input_str2) == expected2

def test_tokenize_empty_input(monkeypatch):
    monkeypatch.setattr(tokmod, "word_tokenize", lambda s: s.split())
    monkeypatch.setattr(tokmod, 'SnowballStemmer', lambda lang: type('S', (), {'stem': lambda self, t: t})())
    assert tokmod.tokenize_lexical("") == []

def test_tokenize_respects_lang_argument(monkeypatch):
    monkeypatch.setattr(tokmod, "word_tokenize", lambda s: s.split())

    recorded = {}

    class LangRecordingStemmer:
        def __init__(self, lang):
            recorded['lang'] = lang

        def stem(self, token):
            return token

    monkeypatch.setattr(tokmod, 'SnowballStemmer', lambda lang: LangRecordingStemmer(lang))

    tokmod.tokenize_lexical("token", lang='spanish')
    assert recorded.get('lang') == 'spanish'

def test_tokenize_preserves_non_stopwords_and_filters_stopwords(monkeypatch):
    monkeypatch.setattr(tokmod, "word_tokenize", lambda s: s.split())
    monkeypatch.setattr(tokmod, 'SnowballStemmer', lambda lang: type('S', (), {'stem': lambda self, t: t+'-stem'})())

    input_str = "The quick brown fox and the lazy dog"
    expected = ['quick-stem', 'brown-stem', 'fox-stem', 'lazy-stem', 'dog-stem']
    assert tokmod.tokenize_lexical(input_str) == expected

# Integration Test with real NLTK tokenizer and stemmer
def test_tokenize_integration_real_nltk():
    out = tokmod.tokenize_lexical("Running runners ran rapidly.")
    assert isinstance(out, list)
    assert all(isinstance(t, str) for t in out)
    # some basic sanity: at least one token and no stopwords (e.g., 'the') included
    assert len(out) > 0
    assert 'the' not in out

def test_tokenize_integration_real_nltk_spanish():
    out = tokmod.tokenize_lexical("Corriendo corredores corrió rápidamente.", lang='spanish')
    assert isinstance(out, list)
    assert all(isinstance(t, str) for t in out)
    assert len(out) > 0
    assert 'el' not in out  # 'el' is a Spanish stopword