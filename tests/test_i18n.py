"""Tests for MCP I18n Tools — locales, translations, pluralization, export."""
import json, pytest, os, sys
from unittest.mock import patch
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.server import MCPI18nToolsServer, TOOL_DEFS
from src.i18n_engine import I18nEngine

class TestToolDefs:
    def test_names(self):
        for t in TOOL_DEFS: assert "name" in t and len(t["name"])>0
    def test_descs(self):
        for t in TOOL_DEFS: assert "description" in t and len(t["description"])>10
    def test_schema(self):
        for t in TOOL_DEFS: assert "inputSchema" in t and t["inputSchema"]["type"]=="object"
    def test_count(self):
        assert len(TOOL_DEFS)==16
    def test_required(self):
        names={t["name"] for t in TOOL_DEFS}
        expected={"add_locale","remove_locale","list_locales","set_current","set_default","add_translation","add_translations","get_translation","remove_translation","translate","translate_plural","list_keys","export_locale","import_locale","get_stats","reset"}
        assert names==expected

class TestManifest:
    def test_manifest(self):
        s=MCPI18nToolsServer();m=s.manifest()
        assert m["server"]["name"]=="mcp-i18n-tools"
        assert len(m["tools"])==16

class TestLocales:
    def test_add(self):
        s=I18nEngine.create_store()
        r=I18nEngine.add_locale(s,"en","English")
        assert r["success"] is True
    def test_duplicate(self):
        s=I18nEngine.create_store()
        I18nEngine.add_locale(s,"en")
        r=I18nEngine.add_locale(s,"en")
        assert r["success"] is False
    def test_remove(self):
        s=I18nEngine.create_store()
        I18nEngine.add_locale(s,"fr")
        r=I18nEngine.remove_locale(s,"fr")
        assert r["deleted"] is True
    def test_list(self):
        s=I18nEngine.create_store()
        I18nEngine.add_locale(s,"en")
        I18nEngine.add_locale(s,"fr")
        assert I18nEngine.list_locales(s)["count"]==2
    def test_set_current(self):
        s=I18nEngine.create_store()
        I18nEngine.add_locale(s,"fr")
        I18nEngine.set_current(s,"fr")
        assert I18nEngine.list_locales(s)["current"]=="fr"
    def test_set_default(self):
        s=I18nEngine.create_store()
        I18nEngine.add_locale(s,"fr")
        I18nEngine.set_default(s,"fr")
        assert I18nEngine.list_locales(s)["default"]=="fr"

class TestTranslations:
    def test_add(self):
        s=I18nEngine.create_store()
        I18nEngine.add_locale(s,"en")
        r=I18nEngine.add_translation(s,"en","hello","Hello")
        assert r["success"] is True
    def test_add_batch(self):
        s=I18nEngine.create_store()
        I18nEngine.add_locale(s,"en")
        r=I18nEngine.add_translations(s,"en",{"hello":"Hello","bye":"Goodbye"})
        assert r["added"]==2
    def test_get(self):
        s=I18nEngine.create_store()
        I18nEngine.add_locale(s,"en")
        I18nEngine.add_translation(s,"en","hello","Hello")
        r=I18nEngine.get_translation(s,"en","hello")
        assert r["value"]=="Hello"
    def test_not_found(self):
        s=I18nEngine.create_store()
        I18nEngine.add_locale(s,"en")
        r=I18nEngine.get_translation(s,"en","nonexistent")
        assert r["found"] is False
    def test_remove(self):
        s=I18nEngine.create_store()
        I18nEngine.add_locale(s,"en")
        I18nEngine.add_translation(s,"en","hello","Hello")
        r=I18nEngine.remove_translation(s,"en","hello")
        assert r["deleted"] is True

class TestTranslate:
    def test_basic(self):
        s=I18nEngine.create_store()
        I18nEngine.add_locale(s,"en")
        I18nEngine.add_translation(s,"en","hello","Hello")
        r=I18nEngine.translate(s,"hello")
        assert r["value"]=="Hello"
    def test_with_params(self):
        s=I18nEngine.create_store()
        I18nEngine.add_locale(s,"en")
        I18nEngine.add_translation(s,"en","greeting","Hello {name}")
        r=I18nEngine.translate(s,"greeting",params={"name":"Alice"})
        assert "Alice" in r["value"]
    def test_fallback(self):
        s=I18nEngine.create_store("en")
        I18nEngine.add_locale(s,"en")
        I18nEngine.add_locale(s,"fr")
        I18nEngine.add_translation(s,"en","hello","Hello")
        I18nEngine.set_current(s,"fr")
        r=I18nEngine.translate(s,"hello")
        assert r["value"]=="Hello"
    def test_miss(self):
        s=I18nEngine.create_store("en")
        I18nEngine.add_locale(s,"en")
        r=I18nEngine.translate(s,"nonexistent")
        assert r["value"]=="nonexistent"

class TestPlural:
    def test_singular(self):
        s=I18nEngine.create_store("en")
        I18nEngine.add_locale(s,"en")
        I18nEngine.add_translation(s,"en","items.one","{count} item")
        I18nEngine.add_translation(s,"en","items.other","{count} items")
        r=I18nEngine.translate_plural(s,"items",1)
        assert "1 item" in r["value"]
    def test_plural(self):
        s=I18nEngine.create_store("en")
        I18nEngine.add_locale(s,"en")
        I18nEngine.add_translation(s,"en","items.one","{count} item")
        I18nEngine.add_translation(s,"en","items.other","{count} items")
        r=I18nEngine.translate_plural(s,"items",5)
        assert "5 items" in r["value"]

class TestKeys:
    def test_list(self):
        s=I18nEngine.create_store()
        I18nEngine.add_locale(s,"en")
        I18nEngine.add_translation(s,"en","a","A")
        I18nEngine.add_translation(s,"en","b","B")
        r=I18nEngine.list_keys(s,"en")
        assert r["count"]==2

class TestExportImport:
    def test_export(self):
        s=I18nEngine.create_store()
        I18nEngine.add_locale(s,"en")
        I18nEngine.add_translation(s,"en","hello","Hello")
        r=I18nEngine.export_locale(s,"en")
        assert "Hello" in r["data"]
    def test_import(self):
        s=I18nEngine.create_store()
        I18nEngine.add_locale(s,"en")
        data = json.dumps({"hello":"Hello","bye":"Goodbye"})
        r=I18nEngine.import_locale(s,"en",data)
        assert r["imported"]==2
    def test_invalid_import(self):
        s=I18nEngine.create_store()
        I18nEngine.add_locale(s,"en")
        r=I18nEngine.import_locale(s,"en","invalid json")
        assert r["success"] is False

class TestStatsReset:
    def test_stats(self):
        s=I18nEngine.create_store("en")
        I18nEngine.add_locale(s,"en")
        I18nEngine.add_translation(s,"en","hello","Hello")
        I18nEngine.translate(s,"hello")
        r=I18nEngine.get_stats(s)
        assert r["total_translations"]==1
    def test_reset(self):
        s=I18nEngine.create_store("en")
        I18nEngine.add_locale(s,"en")
        r=I18nEngine.reset(s)
        assert r["reset"]["locale_count"]==1
        assert I18nEngine.get_stats(s)["locale_count"]==0

class TestDispatch:
    def test_unknown(self):
        s=MCPI18nToolsServer();assert "error" in json.loads(s.handle_tool_call("nope",{}))
    def test_missing(self):
        s=MCPI18nToolsServer();assert "error" in json.loads(s.handle_tool_call("add_locale",{}))
    def test_add_locale_dispatch(self):
        s=MCPI18nToolsServer()
        r=json.loads(s.handle_tool_call("add_locale",{"code":"en"}))
        assert r["success"] is True

class TestSTDIO:
    def test_manifest_flag(self,capsys):
        from src.server import main
        with patch("sys.argv",["server","--manifest"]):main()
        parsed=json.loads(capsys.readouterr().out.strip())
        assert parsed["server"]["name"]=="mcp-i18n-tools"
