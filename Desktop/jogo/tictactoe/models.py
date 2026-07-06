import secrets

from django.db import models


class GameRoom(models.Model):
    code = models.CharField(max_length=8, unique=True)
    player_x_name = models.CharField(max_length=80, blank=True)
    player_o_name = models.CharField(max_length=80, blank=True)
    board = models.JSONField(default=list)
    current_player = models.CharField(max_length=1, default='X')
    winner = models.CharField(max_length=10, blank=True)
    status = models.CharField(max_length=80, default='Aguardando jogadores')
    started = models.BooleanField(default=False)
    rematch_requests = models.JSONField(default=list)
    winning_line = models.JSONField(default=list, blank=True)
    password = models.CharField(max_length=128, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code

    @classmethod
    def create_room(cls):
        while True:
            code = secrets.token_hex(3).upper()
            if not cls.objects.filter(code=code).exists():
                return cls.objects.create(code=code, board=[''] * 9)
