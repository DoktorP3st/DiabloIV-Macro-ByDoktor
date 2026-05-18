"""
i18n.py — Internationalisation pour WW Barb Macro
  Utilisation : i18n.load("fr")  puis  i18n.t("section.cle")
"""
import json, os

_dir  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "locales")
_data: dict = {}
_lang: str  = "fr"

LANGUAGES: dict = {
    "fr": "Français",
    "en": "English",
    "de": "Deutsch",
    "es": "Español",
    "it": "Italiano",
}

def load(code: str) -> None:
    global _lang, _data
    if code not in LANGUAGES:
        code = "en"
    path = os.path.join(_dir, f"{code}.json")
    if not os.path.exists(path):
        code, path = "en", os.path.join(_dir, "en.json")
    with open(path, encoding="utf-8") as f:
        _data = json.load(f)
    _lang = code

def t(key: str, **kw) -> str:
    """Accès par chemin pointé.
    Exemples : t('overlay.status_off')
               t('overlay.footer_active', m=3, s=45)
    """
    node = _data
    for part in key.split("."):
        if not isinstance(node, dict):
            return key
        node = node.get(part, key)
    if isinstance(node, dict):
        return key
    s = str(node)
    return s.format(**kw) if kw else s

def current() -> str:
    return _lang
