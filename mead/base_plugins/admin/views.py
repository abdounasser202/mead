"""Admin plugin — dashboard & settings routes."""
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from functools import wraps

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.role != "admin":
            flash("Accès réservé aux administrateurs.", "danger")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route("/")
@admin_bp.route("")
@admin_required
def dashboard():
    from mead.core.registry import registry
    Post = registry.get_model("Post")
    Category = registry.get_model("Category")
    Tag = registry.get_model("Tag")
    PageView = registry.get_model("PageView")

    stats = {
        "posts": Post.query.filter_by(is_page=False).count() if Post else 0,
        "pages": Post.query.filter_by(is_page=True).count() if Post else 0,
        "categories": Category.query.count() if Category else 0,
        "tags": Tag.query.count() if Tag else 0,
        "views": PageView.query.count() if PageView else 0,
    }
    menu = registry.get_menu_items(parent="admin")
    return render_template("admin/dashboard.html", stats=stats, menu=menu)


@admin_bp.route("/settings", methods=["GET", "POST"])
@admin_required
def settings():
    from mead.core.registry import registry
    Settings = registry.get_model("Settings")
    s = Settings.query.first()

    if request.method == "POST":
        s.blog_name = request.form.get("blog_name", s.blog_name).strip()
        s.blog_description = request.form.get("blog_description", s.blog_description).strip()
        from mead.core.extensions import db
        db.session.commit()
        flash("Paramètres enregistrés.", "success")
        return redirect(url_for("admin.settings"))

    return render_template("admin/settings.html", settings_obj=s)
