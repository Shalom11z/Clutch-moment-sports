# Clutch Moment Sports

A Django app that polls the ESPN scoreboard API for live soccer matches, flags
"clutch" moments (close games late on, extra time, penalty shootouts), pushes
Discord alerts when one starts, and serves a live-updating dashboard.

## History

Originally built to track the **2026 FIFA World Cup**: polling
`soccer/fifa.world/scoreboard`, detecting extra-time and penalty-shootout
games, and sending Discord notifications for close finishes (see
`games/management/commands/poll_scores.py` git history and the
`Add Discord notifications for clutch moments`, `Implement is_clutch() logic`,
and `Add poll_scores command to fetch and save World Cup games` commits).

With the World Cup finished, the poller now targets the **2026-27 English
Premier League** (`soccer/eng.1/scoreboard`) for the upcoming season. The
underlying model, clutch-detection logic, and dashboard are competition-agnostic —
switching competitions is a one-line change to the ESPN endpoint in
`poll_scores.py`.

## How it works

- `games/management/commands/poll_scores.py` — polls the ESPN scoreboard API,
  upserts `Game` rows (score, status, minute, extra time, penalty shootout
  score), and sends a Discord webhook notification the first time a game
  becomes "clutch."
- `games/models.py` — `Game.is_clutch()` flags a match as clutch when it's
  in a penalty shootout, went to extra time, or is within one goal in the
  final 10 minutes of regulation.
- `games/views.py` / `games/templates/games/` — a live dashboard
  (`/`) that auto-refreshes via a polling partial (`/partial/games/`) every
  15 seconds, highlighting clutch games.

## Running locally

```bash
python manage.py migrate
python manage.py poll_scores   # fetch current scoreboard once
python manage.py runserver
```

To keep scores updating automatically, run `poll_scores` with `--loop` in a
long-running process (e.g. a second terminal, or a background service) instead
of calling it once:

```bash
python manage.py poll_scores --loop --interval 60   # poll every 60s, forever
```

Set `DISCORD_WEBHOOK_URL` in the environment to enable clutch notifications.

To poll a different competition, change the ESPN slug in `poll_scores.py`
(e.g. `fifa.world` for the World Cup, `eng.1` for the Premier League, `uefa.champions` for the Champions League).

## Deploying (Render)

`render.yaml` defines a Render Blueprint with three pieces, so the site and
poller keep running without your laptop:

- **web** — `gunicorn`-served dashboard (free plan; sleeps after 15 min of
  no traffic and wakes on the next request).
- **poller** — a background worker running `poll_scores --loop --interval
  60` continuously (`starter` plan — Render's free tier doesn't run
  always-on workers, so this incurs a small monthly cost).
- **db** — a managed Postgres database shared by both.

Steps:

1. Push this repo to GitHub (already done if you're reading this from the
   remote).
2. In the [Render dashboard](https://dashboard.render.com), click
   **New > Blueprint** and connect this repo. Render will read `render.yaml`
   and create the db, web service, and worker.
3. Set the `DISCORD_WEBHOOK_URL` env var (marked `sync: false` in
   `render.yaml`, so Render won't auto-fill it) on **both** the web and
   worker services, in their dashboard's Environment tab.
4. Deploy. `SECRET_KEY` is auto-generated per service and `DATABASE_URL` is
   wired to the Postgres instance automatically.

Local development is unaffected: without a `DATABASE_URL` env var it still
falls back to `db.sqlite3`, and without `DEBUG=False` set it still runs in
debug mode.
