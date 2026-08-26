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
