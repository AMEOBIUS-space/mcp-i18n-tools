"""i18n engine — zero dependencies.
Provides translations, locales, pluralization, interpolation.
"""
import time, json, re
from typing import Any, Dict, List, Optional

class I18nEngine:
    @staticmethod
    def create_store(default_locale: str = "en") -> Dict:
        return {"locales": {}, "default": default_locale, "current": default_locale, "fallback": True, "stats": {"translations": 0, "misses": 0, "by_locale": {}}}

    @staticmethod
    def add_locale(store: Dict, code: str, name: str = "") -> Dict:
        if code in store["locales"]:
            return {"success": False, "error": f"Locale '{code}' already exists"}
        store["locales"][code] = {"code": code, "name": name or code, "translations": {}, "plural_rules": {"one": "n == 1", "other": "n != 1"}, "created": time.time()}
        store["stats"]["by_locale"][code] = 0
        return {"success": True, "locale": code, "name": name or code}

    @staticmethod
    def remove_locale(store: Dict, code: str) -> Dict:
        if code not in store["locales"]:
            return {"success": True, "deleted": False}
        del store["locales"][code]
        if code in store["stats"]["by_locale"]:
            del store["stats"]["by_locale"][code]
        if store["current"] == code:
            store["current"] = store["default"]
        return {"success": True, "deleted": True}

    @staticmethod
    def list_locales(store: Dict) -> Dict:
        return {"success": True, "locales": [{"code": k, "name": v["name"], "translation_count": len(v["translations"])} for k, v in store["locales"].items()], "count": len(store["locales"]), "current": store["current"], "default": store["default"]}

    @staticmethod
    def set_current(store: Dict, code: str) -> Dict:
        if code not in store["locales"] and code != store["default"]:
            return {"success": False, "error": f"Locale '{code}' not found"}
        store["current"] = code
        return {"success": True, "current": code}

    @staticmethod
    def set_default(store: Dict, code: str) -> Dict:
        if code not in store["locales"]:
            return {"success": False, "error": f"Locale '{code}' not found"}
        store["default"] = code
        return {"success": True, "default": code}

    @staticmethod
    def add_translation(store: Dict, locale: str, key: str, value: str) -> Dict:
        if locale not in store["locales"]:
            return {"success": False, "error": f"Locale '{locale}' not found"}
        store["locales"][locale]["translations"][key] = value
        return {"success": True, "locale": locale, "key": key}

    @staticmethod
    def add_translations(store: Dict, locale: str, translations: Dict) -> Dict:
        if locale not in store["locales"]:
            return {"success": False, "error": f"Locale '{locale}' not found"}
        store["locales"][locale]["translations"].update(translations)
        return {"success": True, "locale": locale, "added": len(translations), "total": len(store["locales"][locale]["translations"])}

    @staticmethod
    def get_translation(store: Dict, locale: str, key: str) -> Dict:
        if locale not in store["locales"]:
            return {"success": False, "error": f"Locale '{locale}' not found"}
        if key in store["locales"][locale]["translations"]:
            return {"success": True, "locale": locale, "key": key, "value": store["locales"][locale]["translations"][key]}
        return {"success": True, "locale": locale, "key": key, "value": None, "found": False}

    @staticmethod
    def remove_translation(store: Dict, locale: str, key: str) -> Dict:
        if locale not in store["locales"]:
            return {"success": False, "error": f"Locale '{locale}' not found"}
        if key in store["locales"][locale]["translations"]:
            del store["locales"][locale]["translations"][key]
            return {"success": True, "deleted": True, "key": key}
        return {"success": True, "deleted": False, "key": key}

    @staticmethod
    def translate(store: Dict, key: str, locale: str = None, params: Dict = None) -> Dict:
        loc = locale or store["current"]
        store["stats"]["translations"] += 1
        value = None
        if loc in store["locales"] and key in store["locales"][loc]["translations"]:
            value = store["locales"][loc]["translations"][key]
            store["stats"]["by_locale"][loc] = store["stats"]["by_locale"].get(loc, 0) + 1
        elif store["fallback"] and store["default"] in store["locales"] and key in store["locales"][store["default"]]["translations"]:
            value = store["locales"][store["default"]]["translations"][key]
        else:
            store["stats"]["misses"] += 1
            value = key
        if params:
            for k, v in params.items():
                value = value.replace("{" + k + "}", str(v))
        return {"success": True, "key": key, "locale": loc, "value": value}

    @staticmethod
    def translate_plural(store: Dict, key: str, count: int, locale: str = None) -> Dict:
        loc = locale or store["current"]
        store["stats"]["translations"] += 1
        if count == 1:
            plural_key = f"{key}.one"
        else:
            plural_key = f"{key}.other"
        value = None
        if loc in store["locales"]:
            value = store["locales"][loc]["translations"].get(plural_key)
        if value is None and store["fallback"] and store["default"] in store["locales"]:
            value = store["locales"][store["default"]]["translations"].get(plural_key)
        if value is None:
            store["stats"]["misses"] += 1
            value = plural_key
        value = value.replace("{count}", str(count))
        return {"success": True, "key": key, "locale": loc, "count": count, "value": value}

    @staticmethod
    def list_keys(store: Dict, locale: str) -> Dict:
        if locale not in store["locales"]:
            return {"success": False, "error": f"Locale '{locale}' not found"}
        return {"success": True, "locale": locale, "keys": list(store["locales"][locale]["translations"].keys()), "count": len(store["locales"][locale]["translations"])}

    @staticmethod
    def export_locale(store: Dict, locale: str) -> Dict:
        if locale not in store["locales"]:
            return {"success": False, "error": f"Locale '{locale}' not found"}
        return {"success": True, "locale": locale, "data": json.dumps(store["locales"][locale]["translations"], indent=2, ensure_ascii=False)}

    @staticmethod
    def import_locale(store: Dict, locale: str, data: str) -> Dict:
        if locale not in store["locales"]:
            return {"success": False, "error": f"Locale '{locale}' not found"}
        try:
            translations = json.loads(data)
            store["locales"][locale]["translations"].update(translations)
            return {"success": True, "locale": locale, "imported": len(translations), "total": len(store["locales"][locale]["translations"])}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_stats(store: Dict) -> Dict:
        return {"success": True, "locale_count": len(store["locales"]), "current": store["current"], "default": store["default"], "total_translations": store["stats"]["translations"], "total_misses": store["stats"]["misses"], "by_locale": dict(store["stats"]["by_locale"])}

    @staticmethod
    def reset(store: Dict) -> Dict:
        old = I18nEngine.get_stats(store)
        store["locales"] = {}
        store["current"] = store["default"]
        store["stats"] = {"translations": 0, "misses": 0, "by_locale": {}}
        return {"success": True, "reset": old}
