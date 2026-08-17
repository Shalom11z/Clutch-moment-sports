from django.db.models import Case, When
from django.shortcuts import render

from .models import Game

STATUS_ORDER = Case(
    When(status="in", then=0),
    When(status="pre", then=1),
    default=2,
)


def dashboard(request):
    games = Game.objects.order_by(STATUS_ORDER, "-id")
    return render(request, "games/dashboard.html", {"games": games})


def games_partial(request):
    games = Game.objects.order_by(STATUS_ORDER, "-id")
    return render(request, "games/_games_list.html", {"games": games})
