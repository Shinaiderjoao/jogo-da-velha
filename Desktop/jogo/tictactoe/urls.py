from django.urls import path

from . import views

urlpatterns = [
    path('', views.game_view, name='game'),
    path('play/', views.play_view, name='play'),
    path('reset/', views.reset_view, name='reset'),
]
