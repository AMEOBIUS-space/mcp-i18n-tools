"""MCP Server for i18n — translations, locales, pluralization."""
import json, sys, argparse
from .i18n_engine import I18nEngine

_store = I18nEngine.create_store()

TOOL_DEFS = [
    {"name":"add_locale","description":"Add a locale.","inputSchema":{"type":"object","properties":{"code":{"type":"string"},"name":{"type":"string"}},"required":["code"]}},
    {"name":"remove_locale","description":"Remove a locale.","inputSchema":{"type":"object","properties":{"code":{"type":"string"}},"required":["code"]}},
    {"name":"list_locales","description":"List all locales.","inputSchema":{"type":"object","properties":{},"required":[]}},
    {"name":"set_current","description":"Set current locale.","inputSchema":{"type":"object","properties":{"code":{"type":"string"}},"required":["code"]}},
    {"name":"set_default","description":"Set default locale.","inputSchema":{"type":"object","properties":{"code":{"type":"string"}},"required":["code"]}},
    {"name":"add_translation","description":"Add a single translation.","inputSchema":{"type":"object","properties":{"locale":{"type":"string"},"key":{"type":"string"},"value":{"type":"string"}},"required":["locale","key","value"]}},
    {"name":"add_translations","description":"Add multiple translations.","inputSchema":{"type":"object","properties":{"locale":{"type":"string"},"translations":{"type":"object"}},"required":["locale","translations"]}},
    {"name":"get_translation","description":"Get a translation.","inputSchema":{"type":"object","properties":{"locale":{"type":"string"},"key":{"type":"string"}},"required":["locale","key"]}},
    {"name":"remove_translation","description":"Remove a translation.","inputSchema":{"type":"object","properties":{"locale":{"type":"string"},"key":{"type":"string"}},"required":["locale","key"]}},
    {"name":"translate","description":"Translate a key with params.","inputSchema":{"type":"object","properties":{"key":{"type":"string"},"locale":{"type":"string"},"params":{"type":"object"}},"required":["key"]}},
    {"name":"translate_plural","description":"Translate with pluralization.","inputSchema":{"type":"object","properties":{"key":{"type":"string"},"count":{"type":"integer"},"locale":{"type":"string"}},"required":["key","count"]}},
    {"name":"list_keys","description":"List all keys for a locale.","inputSchema":{"type":"object","properties":{"locale":{"type":"string"}},"required":["locale"]}},
    {"name":"export_locale","description":"Export locale as JSON.","inputSchema":{"type":"object","properties":{"locale":{"type":"string"}},"required":["locale"]}},
    {"name":"import_locale","description":"Import locale from JSON.","inputSchema":{"type":"object","properties":{"locale":{"type":"string"},"data":{"type":"string"}},"required":["locale","data"]}},
    {"name":"get_stats","description":"Get i18n statistics.","inputSchema":{"type":"object","properties":{},"required":[]}},
    {"name":"reset","description":"Reset all i18n state.","inputSchema":{"type":"object","properties":{},"required":[]}},
]

class MCPI18nToolsServer:
    def __init__(self,name="mcp-i18n-tools",version="1.0.0"):
        self.name=name;self.version=version
    def list_tools(self):return TOOL_DEFS
    def manifest(self):return{"server":{"name":self.name,"version":self.version},"capabilities":{"tools":{"listChanged":False}},"tools":self.list_tools()}
    def handle_tool_call(self,name,args):
        try:
            if name=="add_locale":return json.dumps(I18nEngine.add_locale(_store,args["code"],args.get("name","")))
            elif name=="remove_locale":return json.dumps(I18nEngine.remove_locale(_store,args["code"]))
            elif name=="list_locales":return json.dumps(I18nEngine.list_locales(_store))
            elif name=="set_current":return json.dumps(I18nEngine.set_current(_store,args["code"]))
            elif name=="set_default":return json.dumps(I18nEngine.set_default(_store,args["code"]))
            elif name=="add_translation":return json.dumps(I18nEngine.add_translation(_store,args["locale"],args["key"],args["value"]))
            elif name=="add_translations":return json.dumps(I18nEngine.add_translations(_store,args["locale"],args["translations"]))
            elif name=="get_translation":return json.dumps(I18nEngine.get_translation(_store,args["locale"],args["key"]))
            elif name=="remove_translation":return json.dumps(I18nEngine.remove_translation(_store,args["locale"],args["key"]))
            elif name=="translate":return json.dumps(I18nEngine.translate(_store,args["key"],args.get("locale"),args.get("params")))
            elif name=="translate_plural":return json.dumps(I18nEngine.translate_plural(_store,args["key"],args["count"],args.get("locale")))
            elif name=="list_keys":return json.dumps(I18nEngine.list_keys(_store,args["locale"]))
            elif name=="export_locale":return json.dumps(I18nEngine.export_locale(_store,args["locale"]))
            elif name=="import_locale":return json.dumps(I18nEngine.import_locale(_store,args["locale"],args["data"]))
            elif name=="get_stats":return json.dumps(I18nEngine.get_stats(_store))
            elif name=="reset":return json.dumps(I18nEngine.reset(_store))
            else:return json.dumps({"error":f"Unknown tool: {name}"})
        except KeyError as e:return json.dumps({"error":f"Missing required parameter: {e}","tool":name})
        except Exception as e:return json.dumps({"error":str(e),"tool":name})

def _run_stdio():
    server=MCPI18nToolsServer()
    for line in sys.stdin:
        line=line.strip()
        if not line:continue
        try:request=json.loads(line)
        except json.JSONDecodeError:print(json.dumps({"jsonrpc":"2.0","error":{"code":-32700,"message":"Parse error"}}),flush=True);continue
        method=request.get("method","");req_id=request.get("id");params=request.get("params",{})
        if method=="initialize":response={"jsonrpc":"2.0","id":req_id,"result":{"server":server.name,"version":server.version}}
        elif method=="tools/list":response={"jsonrpc":"2.0","id":req_id,"result":{"tools":server.list_tools()}}
        elif method=="tools/call":
            result=server.handle_tool_call(params.get("name",""),params.get("arguments",{}))
            response={"jsonrpc":"2.0","id":req_id,"result":{"content":[{"type":"text","text":result}]}}
        elif method=="shutdown":response={"jsonrpc":"2.0","id":req_id,"result":{}};print(json.dumps(response),flush=True);break
        else:response={"jsonrpc":"2.0","id":req_id,"error":{"code":-32601,"message":f"Method not found: {method}"}}
        print(json.dumps(response),flush=True)

def main():
    parser=argparse.ArgumentParser(description="MCP I18n Tools Server")
    parser.add_argument("--stdio",action="store_true")
    parser.add_argument("--manifest",action="store_true")
    args=parser.parse_args()
    if args.manifest:print(json.dumps(MCPI18nToolsServer().manifest(),indent=2))
    elif args.stdio:_run_stdio()
    else:parser.print_help()

if __name__=="__main__":main()
