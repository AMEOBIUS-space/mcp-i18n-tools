"""mcp-i18n-tools package — MCP server for internationalization."""
from .i18n_engine import I18nEngine
from .server import MCPI18nToolsServer, TOOL_DEFS
__all__ = ["I18nEngine", "MCPI18nToolsServer", "TOOL_DEFS"]
__version__ = "1.0.0"
