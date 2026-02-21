"""Setup plugin — initial configuration wizard."""
from flask import Blueprint, render_template, redirect, url_for, request, flash
from mead.core.extensions import db

setup_bp = Blueprint("setup", __name__, url_prefix="")


@setup_bp.route("/setup", methods=["GET", "POST"])
def setup():
    from mead.core.registry import registry

    Settings = registry.get_model("Settings")
    User = registry.get_model("User")
    Post = registry.get_model("Post")

    # Already configured → redirect home
    if Settings and Settings.query.first():
        return redirect(url_for("blog.home"))

    if request.method == "POST":
        blog_name = request.form.get("blog_name", "Mon blog").strip()
        blog_description = request.form.get("blog_description", "").strip()
        username = request.form.get("username", "admin").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        # Create settings
        settings = Settings(blog_name=blog_name, blog_description=blog_description)
        db.session.add(settings)

        # Create admin user
        user = User(username=username, email=email, role="admin")
        user.set_password(password)
        db.session.add(user)
        db.session.flush()  # get user.id

        # Default pages
        for title in ["À propos", "Projets"]:
            page = Post(
                title=title,
                content=f"# {title}\n\nContenu à venir…",
                is_page=True,
                author_id=user.id,
            )
            db.session.add(page)

        db.session.commit()
        flash("Installation terminée ! Connectez-vous.", "success")
        return redirect(url_for("auth.login"))

    return render_template("setup/setup.html")
