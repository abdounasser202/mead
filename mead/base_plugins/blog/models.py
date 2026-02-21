"""Blog plugin — Category, Tag, Post, PageView models.

Post supports model inheritance: create a subclass with joined-table
inheritance in another plugin to add extra fields without touching this file.

Example (in an external plugin):
    class Article(Post):
        __tablename__ = "article"
        __mapper_args__ = {"polymorphic_identity": "article"}
        id = db.Column(db.Integer, db.ForeignKey("post.id"), primary_key=True)
        subtitle = db.Column(db.String(300))
"""
from datetime import datetime
from slugify import slugify
from mead.core.extensions import db


# Many-to-many association table
tags_posts = db.Table(
    "tags_posts",
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id"), primary_key=True),
    db.Column("post_id", db.Integer, db.ForeignKey("post.id"), primary_key=True),
)


class Category(db.Model):
    __tablename__ = "category"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)

    posts = db.relationship("Post", backref="category", lazy=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.name and not self.slug:
            self.slug = slugify(self.name)

    def __repr__(self):
        return f"<Category {self.name}>"


class Tag(db.Model):
    __tablename__ = "tag"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.name and not self.slug:
            self.slug = slugify(self.name)

    def __repr__(self):
        return f"<Tag {self.name}>"


class Post(db.Model):
    __tablename__ = "post"

    # Inheritance support
    type = db.Column(db.String(50), default="post")
    __mapper_args__ = {
        "polymorphic_on": type,
        "polymorphic_identity": "post",
    }

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    slug = db.Column(db.String(350), unique=True, nullable=False)
    content = db.Column(db.Text, default="")
    external_url = db.Column(db.String(500), nullable=True)
    is_page = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=True)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    tags = db.relationship("Tag", secondary=tags_posts, backref="posts", lazy=True)
    author = db.relationship("User", backref="posts")
    page_views = db.relationship("PageView", backref="post", lazy=True,
                                  cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.title and not self.slug:
            self.slug = slugify(self.title)

    def __repr__(self):
        return f"<Post {self.slug}>"


class PageView(db.Model):
    __tablename__ = "page_view"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=True)
    url = db.Column(db.String(500))
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(300))
    referrer = db.Column(db.String(500))
    device = db.Column(db.String(50))
    browser = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PageView {self.url}>"
