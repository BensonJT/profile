/* Author card — single source for every article page.
   Each article carries only <div id="author-card"></div>; all markup lives
   here and all styling lives in css/article.css under .author-card.
   Change it once, every article updates. */
(function () {
    var mount = document.getElementById("author-card");
    if (!mount) return;

    mount.className = "author-card";
    mount.innerHTML = [
        '<img class="author-card__photo" src="img/headshot_jb_sm.webp" width="400" height="400"',
        ' loading="lazy" decoding="async" alt="Jeffrey Benson">',
        '<div class="author-card__body">',
        '<p class="author-card__name">Jeffrey Benson</p>',
        '<p class="author-card__role">Principal, Cornerstone Solutions',
        '<span class="author-card__dot">&middot;</span>Lean Six Sigma Black Belt</p>',
        '<p class="author-card__line">Let&rsquo;s build something better, together.</p>',
        '<a class="author-card__link" href="https://www.linkedin.com/in/jeffreytbenson/"',
        ' target="_blank" rel="noopener noreferrer">Connect on LinkedIn &rarr;</a>',
        "</div>",
    ].join("");
})();
