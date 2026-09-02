# Dashboard Usage Guide

The web dashboard is served at `GET /` and provides a single-page interface to explore collected OVOS metrics.

## Summary Cards

Three cards at the top show live counts of Total Intents, Total Wake Words, and Total Utterances, fetched from `GET /dashboard/stats`. A status line next to the heading shows when the data was last updated, or an error message if the request failed. Numbers are formatted with the browser's locale via `Intl.NumberFormat`.

## Auto-Refresh

The dashboard re-fetches `/dashboard/stats` every 60 seconds in the background and updates the cards and charts in place (existing Chart.js instances are updated, not recreated, so there is no flicker or memory leak from repeated renders).

## Tabs

Tab buttons switch between panels client-side; no page reload occurs.

### Intents Tab
- Language doughnut chart and intent doughnut chart rendered from `/dashboard/stats`.
- Filters: language, intent name, date range.
- Paginated table (50 rows/page) with ID, intent, language, utterance, and timestamp.
- Export links dynamically update to include active filters: CSV (`/intents/export?format=csv`) and JSON.

### Wake Words Tab
- Bar chart of wake-word name distribution.
- Filters: name, plugin.
- Paginated table with a **Play** button per row — streams audio from `/wake_words/{id}/audio` via browser blob URL.

### Utterances Tab
- Filters: language, model, plugin.
- Paginated table with a **Play** button per row — streams audio from `/utterances/{id}/audio`.

Each tab shows a small status line above its table (loading / error) so a failed request never leaves the UI stuck on stale placeholders.

## Audio Modal

Clicking **Play** opens a modal with an HTML `<audio>` element. Audio is fetched as a blob and played inline. Close with the × button.

## Charts

Charts use Chart.js 4.x, vendored locally at `app/static/js/vendor/chart.umd.min.js` and served from `/static/js/vendor/chart.umd.min.js` — no external CDN is contacted at page load. Data comes from `GET /dashboard/stats`. Stats are cached server-side for `dashboard_cache_ttl` seconds (see `app/config.py`).

## Appearance

The dashboard follows the operating system's light/dark preference (`prefers-color-scheme`) using CSS custom properties for colors; Chart.js text and gridline colors adapt automatically when the OS theme changes. Layout is a responsive card/grid design with a mobile breakpoint around 640px — tables scroll horizontally on narrow screens instead of overflowing the page.

## Footer

The page footer links to the interactive API docs (`/docs`), the privacy policy, the FAQ, and the GitHub repository.

## Static Assets

- `/static/css/dashboard.css` — `app/static/css/dashboard.css`
- `/static/js/dashboard.js` — `app/static/js/dashboard.js`
- `/static/js/vendor/chart.umd.min.js` — vendored Chart.js UMD build
