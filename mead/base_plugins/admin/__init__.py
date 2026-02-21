"""Admin plugin — dashboard & settings."""
from mead.core.plugin import Plugin


class AdminPlugin(Plugin):
    name = "admin"
    version = "1.0.0"
    description = "Admin dashboard & site settings"
    depends = ["auth"]

    def setup(self, app, db):
        from .models import Settings
        from mead.core.registry import registry

        registry.register_model("Settings", Settings)

        from .views import admin_bp
        app.register_blueprint(admin_bp)

        # Register admin menu items
        registry.register_menu_item(
            "admin.settings", "Paramètres", "/admin/settings",
            icon="bi-gear", parent="admin", order=200
        )


plugin = AdminPlugin()
