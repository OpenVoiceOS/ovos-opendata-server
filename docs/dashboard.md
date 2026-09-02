# Dashboard Usage Guide

The web dashboard is served at `GET /` and provides a single-page interface to explore collected OVOS metrics.

## Summary Cards

Three cards at the top show live counts of Total Intents, Total Wake Words, and Total Utterances, fetched from `GET /dashboard/stats`.

## Tabs

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

## Audio Modal

Clicking **Play** opens a modal with an HTML `<audio>` element. Audio is fetched as a blob and played inline. Close with the × button.

## Charts

Charts use Chart.js 4.x from CDN (`cdn.jsdelivr.net`). Data comes from `GET /dashboard/stats`. Stats are cached server-side for 60 seconds.

## Static Assets

- `/static/css/dashboard.css` — `app/static/css/dashboard.css`
- `/static/js/dashboard.js` — `app/static/js/dashboard.js`
