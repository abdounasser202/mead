"""Flask application factory with automatic plugin discovery."""
import json
import importlib
from datetime import datetime
from pathlib import Path

from flask import Flask
from jinja2 import ChoiceLoader, FileSystemLoader

from .extensions import db, login_manager
from .registry import registry


# ------------------------------------------------------------------ #
# Plugin discovery helpers                                             #
# ------------------------------------------------------------------ #

def _discover_plugin_dirs(search_dirs: list[Path]) -> list[dict]:
    """Return all plugin info dicts found in *search_dirs*."""
    found = []
    for base in search_dirs:
        if not base.exists():
            continue
        for plugin_dir in sorted(base.iterdir()):
            if not plugin_dir.is_dir():
                continue
            manifest = plugin_dir / "plugin.json"
            if not manifest.exists():
                continue
            with open(manifest) as f:
                data = json.load(f)
            if not data.get("enabled", True):
                continue
            found.append({"manifest": data, "dir": plugin_dir})
    return found


def _topo_sort(plugins: list[dict]) -> list[dict]:
    """Topological sort so dependencies load before dependents."""
    by_name = {p["manifest"]["name"]: p for p in plugins}
    order, visited = [], set()

    def visit(name: str):
        if name in visited or name not in by_name:
            return
        visited.add(name)
        for dep in by_name[name]["manifest"].get("depends", []):
            visit(dep)
        order.append(by_name[name])

    for name in by_name:
        visit(name)
    return order


def _import_plugin_module(plugin_info: dict):
    """Import the Python module for a plugin directory."""
    plugin_dir: Path = plugin_info["dir"]
    if not (plugin_dir / "__init__.py").exists():
        return None

    # Build dotted module path relative to the project root
    # e.g.  .../mead/base_plugins/blog  →  mead.base_plugins.blog
    try:
        pkg_root = Path(__file__).parent.parent.parent  # project root
        rel = plugin_dir.resolve().relative_to(pkg_root.resolve())
        module_path = ".".join(rel.parts)
        return importlib.import_module(module_path)
    except (ValueError, ImportError) as exc:
        print(f"[mead] Warning: could not load plugin {plugin_dir.name!r}: {exc}")
        return None


# ------------------------------------------------------------------ #
# Template loader                                                      #
# ------------------------------------------------------------------ #

def _build_template_loader(app: Flask, mead_dir: Path) -> None:
    """Configure Jinja2 to search template folders in priority order:
    1. external_plugins  (highest — full overrides)
    2. active theme
    3. base_plugins      (lowest — defaults)
    """
    dirs = []

    # 1. External plugins
    for p in sorted((mead_dir / "external_plugins").glob("*/templates")):
        dirs.append(str(p))

    # 2. Active theme
    theme = app.config.get("ACTIVE_THEME", "default")
    theme_tpl = mead_dir / "themes" / theme / "templates"
    if theme_tpl.exists():
        dirs.append(str(theme_tpl))

    # 3. Base plugins
    for p in sorted((mead_dir / "base_plugins").glob("*/templates")):
        dirs.append(str(p))

    if dirs:
        app.jinja_loader = ChoiceLoader([FileSystemLoader(d) for d in dirs])


# ------------------------------------------------------------------ #
# Plugin loading                                                       #
# ------------------------------------------------------------------ #

def _load_plugins(app: Flask) -> None:
    mead_dir = Path(__file__).parent.parent

    plugins = _discover_plugin_dirs([
        mead_dir / "base_plugins",
        mead_dir / "external_plugins",
    ])
    plugins = _topo_sort(plugins)

    loaded = []
    for info in plugins:
        mod = _import_plugin_module(info)
        if mod is None:
            continue
        plugin_instance = getattr(mod, "plugin", None)
        if plugin_instance is None:
            continue
        try:
            registry.register_plugin(plugin_instance)
            plugin_instance.setup(app, db)
            loaded.append(plugin_instance)
            print(f"[mead] Loaded plugin: {plugin_instance.name} v{plugin_instance.version}")
        except Exception as exc:
            print(f"[mead] Error loading plugin {info['manifest']['name']!r}: {exc}")
            raise

    for p in loaded:
        p.on_load(app)


# ------------------------------------------------------------------ #
# CLI                                                                  #
# ------------------------------------------------------------------ #

def _register_cli(app: Flask) -> None:
    @app.cli.command("init-db")
    def init_db():
        """Create all database tables."""
        with app.app_context():
            db.create_all()
            print("Database initialised.")

    @app.cli.command("list-plugins")
    def list_plugins():
        """List all registered plugins."""
        for p in registry.get_all_plugins():
            print(f"  • {p.name} v{p.version} — {p.description}")


# ------------------------------------------------------------------ #
# Factory                                                              #
# ------------------------------------------------------------------ #

def create_app(config_object=None):
    """Create and return a configured Flask application."""
    mead_dir = Path(__file__).parent.parent

    app = Flask(__name__, template_folder=None, static_folder=None)

    # --- Configuration ---
    if config_object is None:
        from mead.config import Config
        config_object = Config
    app.config.from_object(config_object)

    # --- Extensions ---
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # --- Theme static files ---
    theme = app.config.get("ACTIVE_THEME", "default")
    theme_static = mead_dir / "themes" / theme / "static"
    if theme_static.exists():
        from flask import Blueprint
        theme_bp = Blueprint("theme_static", __name__,
                             static_folder=str(theme_static),
                             static_url_path="/static")
        app.register_blueprint(theme_bp)

    # --- Template loaders ---
    _build_template_loader(app, mead_dir)

    # --- Plugins ---
    _load_plugins(app)

    # --- Global template context ---
    @app.context_processor
    def _inject_globals():
        from flask_login import current_user
        settings = None
        Settings = registry.get_model("Settings")
        if Settings:
            try:
                settings = Settings.query.first()
            except Exception:
                pass
        return dict(
            now=datetime.utcnow(),
            settings=settings,
            registry=registry,
            admin_menu=registry.get_menu_items(),
            current_user=current_user,
        )

    # --- CLI ---
    _register_cli(app)

    return app
