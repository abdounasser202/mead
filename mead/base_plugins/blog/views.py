"""Blog plugin — public & admin routes."""
from flask import (Blueprint, render_template, redirect, url_for,
                   request, flash, abort)
from flask_login import login_required, current_user
from slugify import slugify

from mead.core.extensions import db
from mead.base_plugins.admin.views import admin_required

blog_bp = Blueprint("blog", __name__, url_prefix="")


# ------------------------------------------------------------------ #
# Helpers                                                              #
# ------------------------------------------------------------------ #

def _get_models():
    from mead.core.registry import registry
    return (
        registry.get_model("Post"),
        registry.get_model("Category"),
        registry.get_model("Tag"),
        registry.get_model("PageView"),
    )


def _track_view(post):
    """Record a page view for *post*."""
    _, _, _, PageView = _get_models()
    if PageView is None:
        return
    try:
        ua_string = request.headers.get("User-Agent", "")
        pv = PageView(
            post_id=post.id,
            url=request.url,
            ip_address=request.remote_addr,
            user_agent=ua_string[:300],
            referrer=(request.referrer or "")[:500],
        )
        db.session.add(pv)
        db.session.commit()
    except Exception:
        db.session.rollback()


# ------------------------------------------------------------------ #
# Public routes                                                        #
# ------------------------------------------------------------------ #

@blog_bp.route("/")
def home():
    Post, Category, Tag, _ = _get_models()
    recent = Post.query.filter_by(is_page=False).order_by(Post.created_at.desc()).limit(10).all()
    return render_template("main/home.html", posts=recent)


@blog_bp.route("/blog")
def index():
    Post, Category, Tag, _ = _get_models()
    posts = Post.query.filter_by(is_page=False).order_by(Post.created_at.desc()).all()
    return render_template("blog/index.html", posts=posts)


@blog_bp.route("/post/<slug>")
def post(slug):
    Post, _, _, _ = _get_models()
    p = Post.query.filter_by(slug=slug).first_or_404()
    if not current_user.is_authenticated:
        _track_view(p)
    return render_template("blog/post.html", post=p)


@blog_bp.route("/category/<slug>")
def category(slug):
    Post, Category, _, _ = _get_models()
    cat = Category.query.filter_by(slug=slug).first_or_404()
    posts = Post.query.filter_by(category_id=cat.id, is_page=False).order_by(
        Post.created_at.desc()).all()
    return render_template("blog/index.html", posts=posts, active_category=cat)


@blog_bp.route("/tag/<slug>")
def tag(slug):
    Post, _, Tag, _ = _get_models()
    t = Tag.query.filter_by(slug=slug).first_or_404()
    return render_template("blog/index.html", posts=t.posts, active_tag=t)


# ------------------------------------------------------------------ #
# Admin — Posts                                                        #
# ------------------------------------------------------------------ #

@blog_bp.route("/admin/posts")
@admin_required
def post_list():
    Post, _, _, _ = _get_models()
    posts = Post.query.filter_by(is_page=False).order_by(Post.created_at.desc()).all()
    return render_template("blog/posts/list.html", posts=posts)


@blog_bp.route("/admin/posts/new", methods=["GET", "POST"])
@admin_required
def post_new():
    Post, Category, Tag, _ = _get_models()
    categories = Category.query.order_by(Category.name).all()
    tags = Tag.query.order_by(Tag.name).all()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        external_url = request.form.get("external_url", "").strip() or None
        category_id = request.form.get("category_id") or None
        tag_ids = request.form.getlist("tags")

        post = Post(
            title=title,
            slug=slugify(title),
            content=content,
            external_url=external_url,
            category_id=int(category_id) if category_id else None,
            author_id=current_user.id,
        )
        post.tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()
        db.session.add(post)
        db.session.commit()
        flash("Article créé.", "success")
        return redirect(url_for("blog.post_list"))

    return render_template("blog/posts/form.html",
                           categories=categories, tags=tags, post=None)


@blog_bp.route("/admin/posts/<int:post_id>/edit", methods=["GET", "POST"])
@admin_required
def post_edit(post_id):
    Post, Category, Tag, _ = _get_models()
    p = Post.query.get_or_404(post_id)
    categories = Category.query.order_by(Category.name).all()
    tags = Tag.query.order_by(Tag.name).all()

    if request.method == "POST":
        p.title = request.form.get("title", p.title).strip()
        p.slug = slugify(p.title)
        p.content = request.form.get("content", p.content).strip()
        p.external_url = request.form.get("external_url", "").strip() or None
        cat_id = request.form.get("category_id")
        p.category_id = int(cat_id) if cat_id else None
        tag_ids = request.form.getlist("tags")
        p.tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()
        db.session.commit()
        flash("Article mis à jour.", "success")
        return redirect(url_for("blog.post_list"))

    return render_template("blog/posts/form.html",
                           post=p, categories=categories, tags=tags)


@blog_bp.route("/admin/posts/<int:post_id>/delete", methods=["POST"])
@admin_required
def post_delete(post_id):
    Post, _, _, _ = _get_models()
    p = Post.query.get_or_404(post_id)
    db.session.delete(p)
    db.session.commit()
    flash("Article supprimé.", "success")
    return redirect(url_for("blog.post_list"))


# ------------------------------------------------------------------ #
# Admin — Pages                                                        #
# ------------------------------------------------------------------ #

@blog_bp.route("/admin/pages")
@admin_required
def page_list():
    Post, _, _, _ = _get_models()
    pages = Post.query.filter_by(is_page=True).order_by(Post.title).all()
    return render_template("blog/pages.html", pages=pages)


@blog_bp.route("/admin/pages/new", methods=["GET", "POST"])
@admin_required
def page_new():
    Post, _, _, _ = _get_models()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        p = Post(
            title=title,
            slug=slugify(title),
            content=content,
            is_page=True,
            author_id=current_user.id,
        )
        db.session.add(p)
        db.session.commit()
        flash("Page créée.", "success")
        return redirect(url_for("blog.page_list"))

    return render_template("blog/posts/form.html", post=None,
                           categories=[], tags=[], is_page=True)


@blog_bp.route("/admin/pages/<int:post_id>/edit", methods=["GET", "POST"])
@admin_required
def page_edit(post_id):
    Post, _, _, _ = _get_models()
    p = Post.query.filter_by(id=post_id, is_page=True).first_or_404()

    if request.method == "POST":
        p.title = request.form.get("title", p.title).strip()
        p.slug = slugify(p.title)
        p.content = request.form.get("content", p.content).strip()
        db.session.commit()
        flash("Page mise à jour.", "success")
        return redirect(url_for("blog.page_list"))

    return render_template("blog/posts/form.html", post=p,
                           categories=[], tags=[], is_page=True)


@blog_bp.route("/admin/pages/<int:post_id>/delete", methods=["POST"])
@admin_required
def page_delete(post_id):
    Post, _, _, _ = _get_models()
    p = Post.query.filter_by(id=post_id, is_page=True).first_or_404()
    db.session.delete(p)
    db.session.commit()
    flash("Page supprimée.", "success")
    return redirect(url_for("blog.page_list"))


# ------------------------------------------------------------------ #
# Admin — Categories                                                   #
# ------------------------------------------------------------------ #

@blog_bp.route("/admin/categories")
@admin_required
def category_list():
    _, Category, _, _ = _get_models()
    cats = Category.query.order_by(Category.name).all()
    return render_template("blog/categories/list.html", categories=cats)


@blog_bp.route("/admin/categories/new", methods=["GET", "POST"])
@admin_required
def category_new():
    _, Category, _, _ = _get_models()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        cat = Category(name=name, slug=slugify(name))
        db.session.add(cat)
        db.session.commit()
        flash("Catégorie créée.", "success")
        return redirect(url_for("blog.category_list"))

    return render_template("blog/categories/form.html", category=None)


@blog_bp.route("/admin/categories/<int:cat_id>/edit", methods=["GET", "POST"])
@admin_required
def category_edit(cat_id):
    _, Category, _, _ = _get_models()
    cat = Category.query.get_or_404(cat_id)

    if request.method == "POST":
        cat.name = request.form.get("name", cat.name).strip()
        cat.slug = slugify(cat.name)
        db.session.commit()
        flash("Catégorie mise à jour.", "success")
        return redirect(url_for("blog.category_list"))

    return render_template("blog/categories/form.html", category=cat)


@blog_bp.route("/admin/categories/<int:cat_id>/delete", methods=["POST"])
@admin_required
def category_delete(cat_id):
    _, Category, _, _ = _get_models()
    cat = Category.query.get_or_404(cat_id)
    db.session.delete(cat)
    db.session.commit()
    flash("Catégorie supprimée.", "success")
    return redirect(url_for("blog.category_list"))


# ------------------------------------------------------------------ #
# Admin — Tags                                                         #
# ------------------------------------------------------------------ #

@blog_bp.route("/admin/tags")
@admin_required
def tag_list():
    _, _, Tag, _ = _get_models()
    tags = Tag.query.order_by(Tag.name).all()
    return render_template("blog/tags/list.html", tags=tags)


@blog_bp.route("/admin/tags/new", methods=["GET", "POST"])
@admin_required
def tag_new():
    _, _, Tag, _ = _get_models()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        t = Tag(name=name, slug=slugify(name))
        db.session.add(t)
        db.session.commit()
        flash("Tag créé.", "success")
        return redirect(url_for("blog.tag_list"))

    return render_template("blog/tags/form.html", tag=None)


@blog_bp.route("/admin/tags/<int:tag_id>/edit", methods=["GET", "POST"])
@admin_required
def tag_edit(tag_id):
    _, _, Tag, _ = _get_models()
    t = Tag.query.get_or_404(tag_id)

    if request.method == "POST":
        t.name = request.form.get("name", t.name).strip()
        t.slug = slugify(t.name)
        db.session.commit()
        flash("Tag mis à jour.", "success")
        return redirect(url_for("blog.tag_list"))

    return render_template("blog/tags/form.html", tag=t)


@blog_bp.route("/admin/tags/<int:tag_id>/delete", methods=["POST"])
@admin_required
def tag_delete(tag_id):
    _, _, Tag, _ = _get_models()
    t = Tag.query.get_or_404(tag_id)
    db.session.delete(t)
    db.session.commit()
    flash("Tag supprimé.", "success")
    return redirect(url_for("blog.tag_list"))
