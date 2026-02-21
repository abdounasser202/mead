"""Admin plugin — site Settings model."""
from datetime import datetime
from mead.core.extensions import db


class Settings(db.Model):
    __tablename__ = "settings"

    id = db.Column(db.Integer, primary_key=True)
    blog_name = db.Column(db.String(200), default="Mon blog")
    blog_description = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Settings {self.blog_name}>"
