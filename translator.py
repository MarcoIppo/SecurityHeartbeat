"""IT->EN translation using Google Translate (via deep-translator)."""


def translate_to_english(text: str) -> str:
    """Translate Italian text to English using Google Translate."""
    if not text.strip():
        return text
    try:
        from deep_translator import GoogleTranslator
        return GoogleTranslator(source='it', target='en').translate(text)
    except Exception:
        return text
