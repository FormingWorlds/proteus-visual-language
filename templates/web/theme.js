// PROTEUS — light/dark theme toggle. Shared by website + docs pages.
// Applies as early as possible to minimise flash; wires buttons on load.
(function () {
  var KEY = 'pt-theme';
  var root = document.documentElement;

  function apply(theme) {
    if (theme === 'light') root.setAttribute('data-theme', 'light');
    else root.removeAttribute('data-theme');
  }

  var saved = null;
  try { saved = localStorage.getItem(KEY); } catch (e) {}
  var osLight = window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches;
  apply(saved || (osLight ? 'light' : 'dark'));

  function sync() {
    var light = root.getAttribute('data-theme') === 'light';
    document.querySelectorAll('[data-theme-toggle]').forEach(function (b) {
      b.setAttribute('aria-pressed', light ? 'true' : 'false');
      b.setAttribute('title', light ? 'Switch to dark theme' : 'Switch to light theme');
    });
  }

  function toggle() {
    var light = root.getAttribute('data-theme') === 'light';
    var next = light ? 'dark' : 'light';
    apply(next);
    try { localStorage.setItem(KEY, next); } catch (e) {}
    sync();
  }

  // Follow OS changes only when the user hasn't chosen explicitly.
  if (window.matchMedia) {
    window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', function (e) {
      var chosen = null;
      try { chosen = localStorage.getItem(KEY); } catch (err) {}
      if (!chosen) { apply(e.matches ? 'light' : 'dark'); sync(); }
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-theme-toggle]').forEach(function (b) {
      b.addEventListener('click', toggle);
    });
    sync();
  });
})();
