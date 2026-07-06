from django.test import TestCase

from .models import GameRoom
from .views import apply_move, get_winner, is_board_full, request_rematch


class TicTacToeLogicTests(TestCase):
    def test_detects_horizontal_winner(self):
        board = ['X', 'X', 'X', '', '', '', '', '', '']
        self.assertEqual(get_winner(board), 'X')

    def test_detects_diagonal_winner(self):
        board = ['O', '', '', '', 'O', '', '', '', 'O']
        self.assertEqual(get_winner(board), 'O')

    def test_detects_full_board(self):
        board = ['X', 'O', 'X', 'X', 'O', 'O', 'O', 'X', 'X']
        self.assertTrue(is_board_full(board))

    def test_apply_move_updates_board_and_turn(self):
        room = GameRoom.objects.create(code='TEST01', player_x_name='Ana', player_o_name='Bia', started=True)
        apply_move(room, 0, 'X')
        room.refresh_from_db()
        self.assertEqual(room.board[0], 'X')
        self.assertEqual(room.current_player, 'O')

    def test_request_rematch_requires_both_players(self):
        room = GameRoom.objects.create(code='TEST02', player_x_name='Ana', player_o_name='Bia', started=True)
        request_rematch(room, 'X')
        room.refresh_from_db()
        self.assertEqual(room.rematch_requests, ['X'])
        request_rematch(room, 'O')
        room.refresh_from_db()
        self.assertEqual(room.rematch_requests, [])
        self.assertEqual(room.board, [''] * 9)
        self.assertEqual(room.current_player, 'X')
