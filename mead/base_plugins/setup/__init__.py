"""Setup plugin — initial site configuration wizard."""
from mead.core.plugin import Plugin


class SetupPlugin(Plugin):
    name = "setup"
    version = "1.0.0"
    description = "Initial site setup wizard"
    depends = ["auth", "admin", "blog"]

    def setup(self, app, db):
        from .views import setup_bp
        app.register_blueprint(setup_bp)


plugin = SetupPlugin()
