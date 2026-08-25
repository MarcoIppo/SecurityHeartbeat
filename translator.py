"""IT->EN translation using Google Translate (via deep-translator)."""
import logging

log = logging.getLogger("secheartbeat.translator")


def translate_to_english(text: str) -> str:
    """Translate Italian text to English using Google Translate."""
    if not text.strip():
        return text
    log.debug(f"Translating text ({len(text)} chars)")
    try:
        from deep_translator import GoogleTranslator
        result = GoogleTranslator(source='it', target='en').translate(text)
        log.debug(f"  Translation OK ({len(result)} chars)")
        return result
    except Exception as e:
        log.error(f"Translation failed: {e}")
        return text
