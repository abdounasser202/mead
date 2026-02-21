"""Central registry for plugins, models, hooks and UI menu items."""
from typing import Callable, Dict, List, Any


class Registry:
    """Singleton registry wiring the whole CMF together."""

    def __init__(self):
        self._plugins: Dict[str, "Plugin"] = {}
        self._hooks: Dict[str, List[tuple]] = {}   # hook_name -> [(priority, cb)]
        self._models: Dict[str, Any] = {}
        self._menu_items: List[Dict] = []

    # ------------------------------------------------------------------ #
    # Plugins                                                              #
    # ------------------------------------------------------------------ #

    def register_plugin(self, plugin):
        if plugin.name in self._plugins:
            raise ValueError(f"Plugin '{plugin.name}' is already registered.")
        self._plugins[plugin.name] = plugin

    def get_plugin(self, name: str):
        return self._plugins.get(name)

    def get_all_plugins(self) -> list:
        return list(self._plugins.values())

    # ------------------------------------------------------------------ #
    # Hooks / events                                                       #
    # ------------------------------------------------------------------ #

    def register_hook(self, hook_name: str, callback: Callable, priority: int = 10):
        """Add a callback to a hook.  Lower priority number = runs first."""
        self._hooks.setdefault(hook_name, [])
        self._hooks[hook_name].append((priority, callback))
        self._hooks[hook_name].sort(key=lambda x: x[0])

    def fire_hook(self, hook_name: str, *args, **kwargs) -> list:
        """Run all callbacks registered for *hook_name*."""
        return [cb(*args, **kwargs) for _, cb in self._hooks.get(hook_name, [])]

    def filter_hook(self, hook_name: str, value, *args, **kwargs):
        """Run filter callbacks: each receives *value* and must return it."""
        for _, cb in self._hooks.get(hook_name, []):
            value = cb(value, *args, **kwargs)
        return value

    # ------------------------------------------------------------------ #
    # Models                                                               #
    # ------------------------------------------------------------------ #

    def register_model(self, name: str, model_class):
        self._models[name] = model_class

    def get_model(self, name: str):
        return self._models.get(name)

    # ------------------------------------------------------------------ #
    # Admin menu                                                           #
    # ------------------------------------------------------------------ #

    def register_menu_item(
        self,
        menu_id: str,
        label: str,
        url: str,
        icon: str = None,
        parent: str = None,
        order: int = 100,
    ):
        self._menu_items.append(
            dict(id=menu_id, label=label, url=url, icon=icon, parent=parent, order=order)
        )
        self._menu_items.sort(key=lambda x: x["order"])

    def get_menu_items(self, parent: str = None) -> list:
        return [m for m in self._menu_items if m["parent"] == parent]


# Global singleton
registry = Registry()
