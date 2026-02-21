/**
 * flask-live.js
 * Thin HTMX companion for Mead CMF reactive components.
 *
 * Markup convention:
 *   <div x-live="counter">          ← component root
 *     <button x-action="increment"> ← triggers an action via HTMX POST
 *   </div>
 */

(function () {
  "use strict";

  function init(root) {
    const name = root.getAttribute("x-live");
    if (!name) return;

    const endpoint = "/live/" + name;

    // Wire action buttons
    root.querySelectorAll("[x-action]").forEach(function (el) {
      const action = el.getAttribute("x-action");
      const payload = {};

      // Collect x-payload-* attributes as extra data
      Array.from(el.attributes).forEach(function (attr) {
        if (attr.name.startsWith("x-payload-")) {
          payload[attr.name.slice(10)] = attr.value;
        }
      });

      // Use HTMX if available; fall back to native fetch
      if (window.htmx) {
        el.setAttribute("hx-post", endpoint);
        el.setAttribute("hx-target", "closest [x-live]");
        el.setAttribute("hx-swap", "outerHTML");
        el.setAttribute(
          "hx-vals",
          JSON.stringify({ action: action, payload: payload })
        );
        htmx.process(el);
      } else {
        el.addEventListener("click", function () {
          fetch(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action: action, payload: payload }),
          })
            .then(function (r) { return r.text(); })
            .then(function (html) {
              root.outerHTML = html;
            });
        });
      }
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[x-live]").forEach(init);
  });

  // Re-initialise after HTMX swaps
  document.addEventListener("htmx:afterSwap", function (evt) {
    if (evt.detail && evt.detail.target) {
      evt.detail.target.querySelectorAll("[x-live]").forEach(init);
    }
  });
})();
