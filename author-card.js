(function () {
  var placeholder = document.getElementById('author-card');
  if (!placeholder) return;

  placeholder.innerHTML = [
    '<div style="background:#fff;border-left:4px solid var(--gold);border-radius:0 6px 6px 0;',
    'padding:28px 32px;margin:48px 0 0;display:flex;align-items:center;gap:24px;',
    'box-shadow:0 2px 10px rgba(0,0,0,0.06);">',
      '<img src="img/Gemini_Headshot.webp" alt="Jeffrey Benson"',
      ' style="width:72px;height:72px;border-radius:50%;object-fit:cover;',
      'flex-shrink:0;border:2px solid var(--gold);">',
      '<div>',
        '<p style="font-size:1rem;font-weight:700;color:var(--charcoal);margin-bottom:4px;">Jeffrey Benson</p>',
        '<p style="font-size:0.85rem;color:rgba(44,46,47,0.6);line-height:1.5;margin-bottom:8px;">',
          'Principal, Cornerstone Solutions &nbsp;&middot;&nbsp; Lean Six Sigma Black Belt',
        '</p>',
        '<p style="font-size:0.9rem;font-style:italic;color:var(--olive);margin-bottom:8px;">',
          'Let\'s build something better, together.',
        '</p>',
        '<a href="https://www.linkedin.com/in/jeffreytbenson/" target="_blank" rel="noopener noreferrer"',
        ' style="color:var(--gold);text-decoration:none;font-size:0.82rem;font-weight:700;">',
          'Connect on LinkedIn &rarr;',
        '</a>',
      '</div>',
    '</div>'
  ].join('');
})();
