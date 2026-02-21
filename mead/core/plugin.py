"""Base Plugin class for Mead CMF."""
from pathlib import Path


class Plugin:
    """
    Base class for all Mead plugins.

    Each plugin subclass should:
    - Set class-level metadata (name, version, …)
    - Implement setup(app, db) to register blueprints / models / hooks
    - Export a singleton instance named ``plugin``
    """

    name: str = None
    version: str = "1.0.0"
    description: str = ""
    depends: list = []

    # ------------------------------------------------------------------ #
    # Lifecycle                                                            #
    # ------------------------------------------------------------------ #

    def setup(self, app, db):
        """Register the plugin's blueprints, models, filters, etc.

        Called once during application startup, in dependency order.
        """

    def on_load(self, app):
        """Called after ALL plugins have been set up.

        Use this for cross-plugin wiring that requires other plugins to
        already be registered.
        """

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    @property
    def _plugin_dir(self) -> Path:
        """Absolute path to the directory containing this plugin."""
        return Path(self.__class__.__module__.replace(".", "/")).parent.resolve()

    def get_template_folder(self) -> str | None:
        p = self._plugin_dir / "templates"
        return str(p) if p.exists() else None

    def get_static_folder(self) -> str | None:
        p = self._plugin_dir / "static"
        return str(p) if p.exists() else None

    def __repr__(self):
        return f"<Plugin {self.name} v{self.version}>"
