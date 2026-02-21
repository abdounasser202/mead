"""Auth plugin — authentication & user management."""
from mead.core.plugin import Plugin


class AuthPlugin(Plugin):
    name = "auth"
    version = "1.0.0"
    description = "Authentication & user management"

    def setup(self, app, db):
        # Import models so SQLAlchemy registers them
        from .models import User
        from mead.core.registry import registry

        registry.register_model("User", User)

        # User loader for Flask-Login
        from mead.core.extensions import login_manager

        @login_manager.user_loader
        def load_user(user_id):
            return User.query.get(int(user_id))

        # Register blueprint
        from .views import auth_bp
        app.register_blueprint(auth_bp)


plugin = AuthPlugin()
