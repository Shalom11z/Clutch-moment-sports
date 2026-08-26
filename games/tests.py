from unittest.mock import patch, Mock

from django.test import TestCase
from django.urls import reverse

from .models import Game


def make_game(**overrides):
    defaults = dict(
        espn_id="1",
        round_name="2026-27",
        home_team="Arsenal",
        away_team="Chelsea",
        home_score=1,
        away_score=1,
        minute="10'",
        status="in",
    )
    defaults.update(overrides)
    return Game.objects.create(**defaults)


class IsClutchTests(TestCase):
    def test_not_in_progress(self):
        game = make_game(status="pre", minute="0'")
        self.assertEqual(game.is_clutch(), (False, None))

    def test_final_status_not_clutch(self):
        game = make_game(status="post", minute="90'")
        self.assertEqual(game.is_clutch(), (False, None))

    def test_extra_time_is_clutch(self):
        game = make_game(went_to_extra_time=True, minute="95'")
        is_clutch, reason = game.is_clutch()
        self.assertTrue(is_clutch)
        self.assertEqual(reason, "catch this game at extra time")

    def test_penalties_is_clutch(self):
        game = make_game(home_penalties=4, away_penalties=3, minute="120'")
        is_clutch, reason = game.is_clutch()
        self.assertTrue(is_clutch)
        self.assertEqual(reason, "catch this game at extra time")

    def test_late_close_game_is_clutch(self):
        game = make_game(minute="85'", home_score=1, away_score=2)
        is_clutch, reason = game.is_clutch()
        self.assertTrue(is_clutch)
        self.assertEqual(reason, "Catch this thriller game")

    def test_late_blowout_not_clutch(self):
        game = make_game(minute="85'", home_score=4, away_score=0)
        self.assertEqual(game.is_clutch(), (False, None))

    def test_early_close_game_not_clutch(self):
        game = make_game(minute="20'", home_score=0, away_score=0)
        self.assertEqual(game.is_clutch(), (False, None))


class DashboardViewTests(TestCase):
    def test_dashboard_orders_live_games_first(self):
        make_game(espn_id="post-1", status="post")
        make_game(espn_id="pre-1", status="pre")
        make_game(espn_id="in-1", status="in")

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        statuses = [g.status for g in response.context["games"]]
        self.assertEqual(statuses, ["in", "pre", "post"])

    def test_games_partial_renders_partial_template(self):
        make_game()

        response = self.client.get(reverse("games_partial"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "games/_games_list.html")
        self.assertTemplateNotUsed(response, "games/dashboard.html")


def make_espn_response(events):
    response = Mock()
    response.json.return_value = {"events": events}
    return response


def make_espn_event(
    event_id="100",
    state="in",
    display_clock="10'",
    period=1,
    home_score="1",
    away_score="1",
    home_penalties=None,
    away_penalties=None,
):
    home = {"homeAway": "home", "team": {"name": "Arsenal"}, "score": home_score}
    away = {"homeAway": "away", "team": {"name": "Chelsea"}, "score": away_score}
    if home_penalties is not None:
        home["shootoutScore"] = home_penalties
    if away_penalties is not None:
        away["shootoutScore"] = away_penalties

    return {
        "id": event_id,
        "season": {"slug": "2026-27"},
        "competitions": [
            {
                "status": {
                    "type": {"state": state},
                    "displayClock": display_clock,
                    "period": period,
                },
                "competitors": [home, away],
            }
        ],
    }


@patch("games.management.commands.poll_scores.requests.post")
@patch("games.management.commands.poll_scores.requests.get")
class PollScoresTests(TestCase):
    def test_creates_game_from_espn_event(self, mock_get, mock_post):
        mock_get.return_value = make_espn_response([make_espn_event()])

        from django.core.management import call_command
        call_command("poll_scores")

        game = Game.objects.get(espn_id="100")
        self.assertEqual(game.home_team, "Arsenal")
        self.assertEqual(game.away_team, "Chelsea")
        self.assertEqual(game.home_score, 1)
        self.assertEqual(game.away_score, 1)
        self.assertEqual(game.status, "in")
        self.assertFalse(game.went_to_extra_time)

    def test_updates_existing_game(self, mock_get, mock_post):
        make_game(espn_id="100", home_score=0, away_score=0)
        mock_get.return_value = make_espn_response(
            [make_espn_event(event_id="100", home_score="2", away_score="1")]
        )

        from django.core.management import call_command
        call_command("poll_scores")

        game = Game.objects.get(espn_id="100")
        self.assertEqual(game.home_score, 2)
        self.assertEqual(game.away_score, 1)

    def test_extracts_penalty_shootout_scores(self, mock_get, mock_post):
        mock_get.return_value = make_espn_response(
            [make_espn_event(period=4, home_penalties=5, away_penalties=4)]
        )

        from django.core.management import call_command
        call_command("poll_scores")

        game = Game.objects.get(espn_id="100")
        self.assertEqual(game.home_penalties, 5)
        self.assertEqual(game.away_penalties, 4)
        self.assertTrue(game.went_to_extra_time)

    def test_sends_discord_notification_for_new_clutch_game(self, mock_get, mock_post):
        mock_get.return_value = make_espn_response(
            [make_espn_event(display_clock="85'", home_score="1", away_score="2")]
        )

        from django.core.management import call_command
        call_command("poll_scores")

        mock_post.assert_called_once()
        game = Game.objects.get(espn_id="100")
        self.assertTrue(game.notified_clutch)

    def test_does_not_renotify_already_notified_game(self, mock_get, mock_post):
        make_game(
            espn_id="100",
            minute="85'",
            home_score=1,
            away_score=2,
            notified_clutch=True,
        )
        mock_get.return_value = make_espn_response(
            [make_espn_event(display_clock="86'", home_score="1", away_score="2")]
        )

        from django.core.management import call_command
        call_command("poll_scores")

        mock_post.assert_not_called()

    def test_no_notification_for_non_clutch_game(self, mock_get, mock_post):
        mock_get.return_value = make_espn_response(
            [make_espn_event(display_clock="10'", home_score="0", away_score="0")]
        )

        from django.core.management import call_command
        call_command("poll_scores")

        mock_post.assert_not_called()
        game = Game.objects.get(espn_id="100")
        self.assertFalse(game.notified_clutch)
