// PROTEUS docs — light interactivity shared across pages.
(function () {
  // TOC scroll-spy: highlight the section currently in view.
  const tocLinks = [...document.querySelectorAll('.toc a[href^="#"]')];
  if (tocLinks.length) {
    const ids = tocLinks.map(a => a.getAttribute('href').slice(1));
    const targets = ids.map(id => document.getElementById(id)).filter(Boolean);
    const byId = Object.fromEntries(tocLinks.map(a => [a.getAttribute('href').slice(1), a]));
    const spy = () => {
      let current = targets[0] && targets[0].id;
      const line = 140;
      for (const t of targets) {
        if (t.getBoundingClientRect().top <= line) current = t.id;
      }
      tocLinks.forEach(a => a.classList.remove('on'));
      if (current && byId[current]) byId[current].classList.add('on');
    };
    window.addEventListener('scroll', spy, { passive: true });
    spy();
  }

  // "/" focuses search (hint only — no real index in the static mock).
  const search = document.querySelector('.doc-search');
  if (search) {
    document.addEventListener('keydown', e => {
      if (e.key === '/' && document.activeElement === document.body) {
        e.preventDefault();
        search.style.borderColor = 'var(--pt-azure)';
        setTimeout(() => (search.style.borderColor = ''), 600);
      }
    });
  }
})();
