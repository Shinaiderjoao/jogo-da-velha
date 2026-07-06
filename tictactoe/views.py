from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .models import GameRoom


WINNING_LINES = [
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
]


def get_winner(board):
    for line in WINNING_LINES:
        a, b, c = line
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    return None


def find_winning_line(board):
    for line in WINNING_LINES:
        a, b, c = line
        if board[a] and board[a] == board[b] == board[c]:
            return list(line)
    return []


def is_board_full(board):
    return all(cell != '' for cell in board)


def apply_move(room, position, player_symbol):
    # Ensure board has correct length before applying move
    normalize_room_board(room)

    if room.winner or room.started is False:
        return None

    board = list(room.board)
    if 0 <= position < 9 and board[position] == '' and room.current_player == player_symbol:
        board[position] = player_symbol
        room.board = board
        winner = get_winner(board)
        if winner:
            room.winner = winner
            room.winning_line = find_winning_line(board)
            room.status = f'Jogador {winner} venceu!'
        elif is_board_full(board):
            room.winner = 'draw'
            room.status = 'Empate!'
            room.winning_line = []
        else:
            room.current_player = 'O' if player_symbol == 'X' else 'X'
            room.status = f'Sua vez: {room.current_player}'
        room.save()
        return room
    return None


def request_rematch(room, player_symbol):
    requests = list(room.rematch_requests)
    if player_symbol not in requests:
        requests.append(player_symbol)
    room.rematch_requests = requests
    if len(requests) == 2:
        room.board = [''] * 9
        room.current_player = 'X'
        room.winner = ''
        room.winning_line = []
        room.status = 'Sua vez: X'
        room.rematch_requests = []
    room.save()
    return room


def build_context(room, request):
    other_player = ''
    if request.session.get('player_symbol') == 'X':
        other_player = room.player_o_name or ''
    elif request.session.get('player_symbol') == 'O':
        other_player = room.player_x_name or ''

    return {
        'room': room,
        'player_name': request.session.get('player_name', ''),
        'player_symbol': request.session.get('player_symbol', ''),
        'is_creator': request.session.get('room_code') == room.code,
        'other_player': other_player,
        'can_start': room.player_o_name and not room.started and request.session.get('is_creator'),
    }


def normalize_room_board(room):
    if not room.board or len(room.board) != 9:
        room.board = [''] * 9
        room.save()


def get_room_from_request(request):
    room_code = request.session.get('room_code')
    if not room_code:
        return None
    room = get_object_or_404(GameRoom, code=room_code)
    normalize_room_board(room)
    return room


def game_view(request):
    room = None
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            room = GameRoom.create_room()
            request.session['room_code'] = room.code
            request.session['player_name'] = request.POST.get('player_name', 'Jogador 1').strip() or 'Jogador 1'
            request.session['player_symbol'] = 'X'
            request.session['is_creator'] = True
            room.player_x_name = request.session['player_name']
            # optional password for the room
            room.password = request.POST.get('room_password', '').strip()
            room.started = False
            room.status = 'Aguardando adversário'
            room.save()
            messages.success(request, 'Partida criada! Compartilhe o link com o adversário.')
            return redirect('game')

        if action == 'join':
            code_raw = request.POST.get('room_code', '')
            code = code_raw.strip().upper()
            room = GameRoom.objects.filter(code=code).first()
            if not room:
                # Return to the form and show an inline error instead of a 404 page
                join_error = 'Código de sala inválido ou inexistente.'
                context = {
                    'room': None,
                    'join_error': join_error,
                    'prefill_room_code': request.POST.get('room_code', ''),
                    'prefill_player_name': request.POST.get('player_name', ''),
                }
                return render(request, 'tictactoe/game.html', context)

            # If the room is protected by a password, validate it
            entered_password = request.POST.get('room_password', '')
            if room.password and room.password != entered_password:
                join_error = 'Senha da sala incorreta.'
                context = {
                    'room': None,
                    'join_error': join_error,
                    'prefill_room_code': request.POST.get('room_code', ''),
                    'prefill_player_name': request.POST.get('player_name', ''),
                }
                return render(request, 'tictactoe/game.html', context)

            request.session['room_code'] = room.code
            request.session['player_name'] = request.POST.get('player_name', 'Jogador 2').strip() or 'Jogador 2'
            request.session['player_symbol'] = 'O'
            request.session['is_creator'] = False
            room.player_o_name = request.session['player_name']
            normalize_room_board(room)
            if not room.started and room.player_x_name:
                room.started = True
                room.status = 'Sua vez: X'
            room.save()
            messages.success(request, 'Você entrou na partida!')
            return redirect('game')

        if action == 'leave':
            request.session.pop('room_code', None)
            request.session.pop('player_name', None)
            request.session.pop('player_symbol', None)
            request.session.pop('is_creator', None)
            return redirect('game')

    if request.session.get('room_code'):
        room = get_object_or_404(GameRoom, code=request.session['room_code'])
        if room.player_o_name and not room.started:
            room.started = True
            room.status = 'Sua vez: X'
            room.save()

    if room is None:
        return render(request, 'tictactoe/game.html', {'room': None})

    return render(request, 'tictactoe/game.html', build_context(room, request))


def play_view(request):
    room = get_room_from_request(request)
    if room is None:
        return render(request, 'tictactoe/partials/game_shell.html', {'room': None})

    if request.method == 'POST':
        position = request.POST.get('position')
        if position is not None:
            apply_move(room, int(position), request.session.get('player_symbol', ''))

    return render(request, 'tictactoe/partials/game_shell.html', build_context(room, request))


def reset_view(request):
    room = get_room_from_request(request)
    if room is not None:
        request_rematch(room, request.session.get('player_symbol', ''))
        if room.rematch_requests == [] and room.winner == '':
            messages.success(request, 'Revanche aceita — a partida reiniciou.')
    return redirect('game')
