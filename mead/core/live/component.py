"""Server-side reactive component base class (Livewire-style via HTMX)."""
from flask import request, render_template_string, render_template


class LiveComponent:
    """Base class for HTMX-driven reactive components.

    Usage
    -----
    class Counter(LiveComponent):
        template = "components/counter.html"

        def mount(self):
            self.count = 0

        def increment(self):
            self.count += 1

    Counter.register(app, "counter")

    In templates:
        <div x-live="counter" hx-get="/live/counter" hx-trigger="load">
            ...
        </div>
    """

    template: str = None

    def __init__(self):
        self.mount()

    def mount(self):
        """Initialise component state — override in subclasses."""

    def render(self) -> str:
        if self.template:
            return render_template(self.template, component=self)
        return ""

    def _apply_action(self, action: str, payload: dict):
        if action and hasattr(self, action):
            getattr(self, action)(**payload)

    @classmethod
    def register(cls, app, endpoint: str):
        """Register an HTMX endpoint for this component at /live/<endpoint>."""

        def handler():
            comp = cls()
            if request.method == "POST":
                data = request.get_json(silent=True) or {}
                comp._apply_action(data.get("action", ""), data.get("payload", {}))
            return comp.render()

        app.add_url_rule(
            f"/live/{endpoint}",
            endpoint=f"live_{endpoint}",
            view_func=handler,
            methods=["GET", "POST"],
        )
        return handler
