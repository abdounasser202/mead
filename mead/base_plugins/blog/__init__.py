"""Blog plugin — posts, categories, tags, pages."""
import markdown2
from mead.core.plugin import Plugin


class BlogPlugin(Plugin):
    name = "blog"
    version = "1.0.0"
    description = "Blog engine — posts, categories, tags, pages"
    depends = ["auth", "admin"]

    def setup(self, app, db):
        # Register models
        from .models import Category, Tag, Post, PageView
        from mead.core.registry import registry

        registry.register_model("Category", Category)
        registry.register_model("Tag", Tag)
        registry.register_model("Post", Post)
        registry.register_model("PageView", PageView)

        # Jinja2 filter: markdown → html
        def markdown_filter(text):
            return markdown2.markdown(
                text or "",
                extras=["fenced-code-blocks", "tables", "header-ids", "footnotes"],
            )
        app.jinja_env.filters["markdown"] = markdown_filter

        # Register blueprint
        from .views import blog_bp
        app.register_blueprint(blog_bp)

        # Admin menu entries
        registry.register_menu_item(
            "blog.posts", "Articles", "/admin/posts",
            icon="bi-file-text", parent="admin", order=10
        )
        registry.register_menu_item(
            "blog.pages", "Pages", "/admin/pages",
            icon="bi-layout-text-window", parent="admin", order=20
        )
        registry.register_menu_item(
            "blog.categories", "Catégories", "/admin/categories",
            icon="bi-folder", parent="admin", order=30
        )
        registry.register_menu_item(
            "blog.tags", "Tags", "/admin/tags",
            icon="bi-tags", parent="admin", order=40
        )


plugin = BlogPlugin()
