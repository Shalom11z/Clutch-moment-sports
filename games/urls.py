from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("partial/games/", views.games_partial, name="games_partial"),
]
