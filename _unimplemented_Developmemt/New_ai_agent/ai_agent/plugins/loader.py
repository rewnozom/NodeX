"""
ai_agent/plugins/loader.py - Dynamic plugin loading system
"""

import os
import importlib
import inspect
from typing import Dict, Type, Any
from pathlib import Path
from ..core.agents.base import BaseAgent

class PluginRegistry:
    _plugins: Dict[str, Type[BaseAgent]] = {}
    
    @classmethod
    def register(cls, name: str, plugin_class: Type[BaseAgent]) -> None:
        cls._plugins[name] = plugin_class

    @classmethod
    def get(cls, name: str) -> Type[BaseAgent]:
        return cls._plugins[name]

    @classmethod
    def list_plugins(cls) -> Dict[str, str]:
        return {name: plugin.__doc__ or "" for name, plugin in cls._plugins.items()}

class PluginLoader:
    def __init__(self, plugin_dir: str = "plugins"):
        self.plugin_dir = Path(plugin_dir)
        
    def load_plugins(self) -> None:
        """Load all plugins from plugin directory"""
        plugin_files = self.plugin_dir.glob("*.py")
        
        for plugin_file in plugin_files:
            if plugin_file.stem.startswith("_"):
                continue
                
            try:
                self._load_plugin_module(plugin_file)
            except Exception as e:
                print(f"Error loading plugin {plugin_file}: {e}")

    def _load_plugin_module(self, plugin_file: Path) -> None:
        """Load single plugin module"""
        module_path = f"{self.plugin_dir.stem}.{plugin_file.stem}"
        spec = importlib.util.spec_from_file_location(module_path, plugin_file)
        if not spec or not spec.loader:
            return
            
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find plugin classes
        for item_name, item in inspect.getmembers(module):
            if (inspect.isclass(item) and 
                issubclass(item, BaseAgent) and 
                item != BaseAgent):
                PluginRegistry.register(item_name, item)

def register_plugin(name: str, plugin_class: Type[BaseAgent]) -> None:
    """Register a plugin class"""
    PluginRegistry.register(name, plugin_class)