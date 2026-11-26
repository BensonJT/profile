# Cornerstone (experiment)

A consultant-facing landing page, inspired by the structure of a professional consulting site but with its own
look, copy and motion. Static HTML, CSS and a little JS, in the same style as the rest of the repo.

-   Page: `index.html`, styles: `cornerstone.css`, script: `cornerstone.js`
-   Palette: default is midnight (deep navy and copper). Try the site-brand olive and gold with `?palette=olive`. All colours are tokens at the top of the CSS.
-   The page is `noindex` while it is an experiment.

## Still to connect

1. **Calendar link:** set in `CAL_URL` at the top of `cornerstone.js` (cal.com intro link). If it is ever emptied, the "Book a time" button hides.
2. **Contact form:** it posts to a form-relay service so the destination address never appears on the page. Put the
   service's access key in the hidden `access_key` field in `index.html` (currently `REPLACE_WITH_ACCESS_KEY`). The form is
   written for Web3Forms; Formspree or similar need only a different `action`.

## Hero motion

`media/hero.mp4` is a 10-second loop (1080p, no audio, about 2.5 MB) cut from a Pexels clip of a stone-arch
colonnade (Pexels video 12399366, 4K original, used under the Pexels licence). The last second dissolves into the first so
the loop is seamless. `media/hero-poster.webp` is the still frame shown while it loads and for visitors who prefer reduced
motion. The CSS tint in `.hero__tint` keeps the headline legible; the drifting-light CSS layer is a soft colour wash on top.
Keep the 4K original out of the repo (it is 500 MB). Check the licence of any replacement clip, and avoid
recognisable faces unless a model release is clear.
