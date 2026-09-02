# Dashboard Usage Guide

The web dashboard is served at `GET /` and provides a single-page interface to
explore collected OVOS metrics — no login, no build step, just a page the
server renders.

## Summary Cards

Three cards at the top show live counts of Total Intents, Total Wake Words, and Total Utterances, fetched from `GET /dashboard/stats`. A status line next to the heading shows when the data was last updated, or an error message if the request failed. Numbers are formatted with the browser's locale via `Intl.NumberFormat`. Stats are cached server-side for `DASHBOARD_CACHE_TTL` seconds (default 60) so repeated dashboard loads don't hammer the database.

## Auto-Refresh

The dashboard re-fetches `/dashboard/stats` every 60 seconds in the background and updates the cards and charts in place (existing Chart.js instances are updated, not recreated, so there is no flicker or memory leak from repeated renders).

## Tabs

Tab buttons switch between panels client-side; no page reload occurs.

### Intents Tab

- Language doughnut chart and intent doughnut chart, rendered from
  `/dashboard/stats`.
- Filters: language, intent name, date range.
- Paginated table (50 rows/page) with ID, intent, language, utterance, and
  timestamp.
- Export links dynamically update to include your active filters: CSV
  (`/intents/export?format=csv`) and JSON.

### Wake Words Tab

- Bar chart of wake-word name distribution.
- Filters: name, plugin.
- Paginated table with a **Play** button per row — streams audio from
  `/wake_words/{id}/audio` via a browser blob URL.

### Utterances Tab

- Filters: language, model, plugin.
- Paginated table with a **Play** button per row — streams audio from
  `/utterances/{id}/audio`.

Each tab shows its own loading/error status line above its table, so a slow
or failed request on one tab doesn't block the others.

Each tab shows a small status line above its table (loading / error) so a failed request never leaves the UI stuck on stale placeholders.

## Audio Modal

Clicking **Play** opens a modal with an HTML `<audio>` element. Audio is
fetched as a blob and played inline. Close with the × button.

## Charts

Three cards at the top show live counts of Total Intents, Total Wake Words, and Total Utterances, fetched from `GET /dashboard/stats`. A status line next to the heading shows when the data was last updated, or an error message if the request failed. Numbers are formatted with the browser's locale via `Intl.NumberFormat`. Stats are cached server-side for `DASHBOARD_CACHE_TTL` seconds (default 60) so repeated dashboard loads don't hammer the database.

## Auto-Refresh

The dashboard re-fetches `/dashboard/stats` every 60 seconds in the background and updates the cards and charts in place (existing Chart.js instances are updated, not recreated, so there is no flicker or memory leak from repeated renders).

## Static Assets

- `/static/css/dashboard.css` — `app/static/css/dashboard.css`
- `/static/js/dashboard.js` — `app/static/js/dashboard.js`
Three cards at the top show live counts of Total Intents, Total Wake Words, and Total Utterances, fetched from `GET /dashboard/stats`. A status line next to the heading shows when the data was last updated, or an error message if the request failed. Numbers are formatted with the browser's locale via `Intl.NumberFormat`. Stats are cached server-side for `DASHBOARD_CACHE_TTL` seconds (default 60) so repeated dashboard loads don't hammer the database.

## Auto-Refresh

The dashboard re-fetches `/dashboard/stats` every 60 seconds in the background and updates the cards and charts in place (existing Chart.js instances are updated, not recreated, so there is no flicker or memory leak from repeated renders).
