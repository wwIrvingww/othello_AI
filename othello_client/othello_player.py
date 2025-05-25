import requests
import random
import sys
import time
import copy
import torch

from board_evaluator import BoardEvaluator
from evaluator_utils import load_model, evaluate

host_name = 'http://localhost:8000'

class OthelloPlayer:
    def __init__(self, username):
        ### Player username
        self.username = username
        ### Player symbol in a match
        self.current_symbol = 0
        # Cargar el modelo de Irving
        self.model, self.device = load_model("model.pt")
    def connect(self, session_name) -> bool:
        """
        :param session_name:
        :return:
        """
        new_player = requests.post(
            host_name + '/player/new_player',
            params={
                'session_name': session_name,
                'player_name': self.username
            }
        )
        new_player = new_player.json()
        self.session_name = session_name
        print(new_player['message'])
        return new_player['status'] == 200

    def play(self) -> bool:
        """
        :return:
        """
        session_info = requests.post(
            host_name + '/game/game_info',
            params={'session_name': self.session_name}
        ).json()

        while session_info['session_status'] == 'active':
            try:
                if session_info['round_status'] == 'ready':
                    match_info = requests.post(
                        host_name + '/player/match_info',
                        params={
                            'session_name': self.session_name,
                            'player_name': self.username
                        }
                    ).json()

                    while match_info['match_status'] == 'bench':
                        print('You are benched this round. Take a rest while you wait.')
                        time.sleep(15)
                        match_info = requests.post(
                            host_name + '/player/match_info',
                            params={
                                'session_name': self.session_name,
                                'player_name': self.username
                            }
                        ).json()

                    if match_info['match_status'] == 'active':
                        self.current_symbol = match_info['symbol']
                        if self.current_symbol == 1:
                            print('Lets play! You are the white pieces.')
                        if self.current_symbol == -1:
                            print('Lets play! You are the black pieces.')

                    while match_info['match_status'] == 'active':
                        turn_info = requests.post(
                            host_name + '/player/turn_to_move',
                            params={
                                'session_name': self.session_name,
                                'player_name': self.username,
                                'match_id': match_info['match']
                            }
                        ).json()

                        while not turn_info['game_over']:
                            if turn_info['turn']:
                                print('SCORE ', turn_info['score'])
                                row, col = self.AI_MOVE(turn_info['board'])
                                move = requests.post(
                                    host_name + '/player/move',
                                    params={
                                        'session_name': self.session_name,
                                        'player_name': self.username,
                                        'match_id': match_info['match'],
                                        'row': row,
                                        'col': col
                                    }
                                ).json()
                                print(move['message'])
                            time.sleep(2)
                            turn_info = requests.post(
                                host_name + '/player/turn_to_move',
                                params={
                                    'session_name': self.session_name,
                                    'player_name': self.username,
                                    'match_id': match_info['match']
                                }
                            ).json()

                        print('Game Over. Winner : ' + turn_info['winner'])
                        match_info = requests.post(
                            host_name + '/player/match_info',
                            params={
                                'session_name': self.session_name,
                                'player_name': self.username
                            }
                        ).json()

                else:
                    print('Waiting for match lottery...')
                    time.sleep(5)

            except requests.exceptions.ConnectionError:
                continue

            session_info = requests.post(
                host_name + '/game/game_info',
                params={'session_name': self.session_name}
            ).json()

    ### Solo modifique esta función
    def AI_MOVE(self, board):

        def get_valid_moves(board, symbol):
            valid_moves = set()
            directions = [(0, 1), (1, 1), (1, 0), (1, -1),
                        (0, -1), (-1, -1), (-1, 0), (-1, 1)]

            for row in range(8):
                for col in range(8):
                    if board[row][col] != 0:
                        continue

                    for dr, dc in directions:
                        r, c = row + dr, col + dc
                        has_opponent_between = False

                        while 0 <= r < 8 and 0 <= c < 8:
                            if board[r][c] == -symbol:
                                has_opponent_between = True
                            elif board[r][c] == symbol and has_opponent_between:
                                valid_moves.add((row, col))
                                break
                            else:
                                break
                            r += dr
                            c += dc

            return sorted(valid_moves)

        def simulate_move(board, move, symbol):
            row, col = move
            if board[row][col] != 0:
                return board  # Already occupied

            new_board = copy.deepcopy(board)
            new_board[row][col] = symbol
            directions = [(0, 1), (1, 1), (1, 0), (1, -1),
                        (0, -1), (-1, -1), (-1, 0), (-1, 1)]

            flipped_any = False
            for dr, dc in directions:
                pieces_to_flip = []
                r, c = row + dr, col + dc

                while 0 <= r < 8 and 0 <= c < 8 and new_board[r][c] == -symbol:
                    pieces_to_flip.append((r, c))
                    r += dr
                    c += dc

                if 0 <= r < 8 and 0 <= c < 8 and new_board[r][c] == symbol and pieces_to_flip:
                    for flip_r, flip_c in pieces_to_flip:
                        new_board[flip_r][flip_c] = symbol
                    flipped_any = True

            return new_board if flipped_any else board

        def prioritize_opening_moves(valid_moves):
            corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
            bad_spots = [(0, 1), (1, 0), (1, 1), (0, 6), (1, 6), (1, 7), 
                        (6, 0), (6, 1), (7, 1), (6, 6), (6, 7), (7, 6)]

            for move in valid_moves:
                if move in corners:
                    return move
            safe_moves = [m for m in valid_moves if m not in bad_spots]
            return random.choice(safe_moves) if safe_moves else random.choice(valid_moves)

        def minimax(board, depth, alpha, beta, maximizing_player, model, device, symbol, start_time, time_limit=2.5):
            if time.time() - start_time >= time_limit:
                return evaluate(board, model, device, symbol)

            current_symbol = symbol if maximizing_player else -symbol
            valid_moves = get_valid_moves(board, current_symbol)
            if depth == 0 or not valid_moves:
                return evaluate(board, model, device, symbol)

            if maximizing_player:
                max_eval = float('-inf')
                for move in valid_moves:
                    next_board = simulate_move(board, move, current_symbol)
                    if next_board == board:
                        continue
                    if time.time() - start_time >= time_limit:
                        break
                    eval_score = (
                        minimax(next_board, depth - 1, alpha, beta, False, model, device, symbol, start_time, time_limit)
                        if depth > 1 else evaluate(next_board, model, device, symbol)
                    )
                    max_eval = max(max_eval, eval_score)
                    alpha = max(alpha, eval_score)
                    if beta <= alpha:
                        break
                return max_eval
            else:
                min_eval = float('inf')
                for move in valid_moves:
                    next_board = simulate_move(board, move, current_symbol)
                    if next_board == board:
                        continue
                    if time.time() - start_time >= time_limit:
                        break
                    eval_score = (
                        minimax(next_board, depth - 1, alpha, beta, True, model, device, symbol, start_time, time_limit)
                        if depth > 1 else evaluate(next_board, model, device, symbol)
                    )
                    min_eval = min(min_eval, eval_score)
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        break
                return min_eval

        valid_moves = get_valid_moves(board, self.current_symbol)
        if not valid_moves:
            return random.randint(0, 7), random.randint(0, 7)  # No valid moves

        piece_count = sum(1 for row in board for cell in row if cell != 0)
        if piece_count < 10:
            move = prioritize_opening_moves(valid_moves)
            if move:
                return move

        best_score = float('-inf')
        best_move = None
        start_time = time.time()
        search_depth = 3 if piece_count < 20 else 4 if piece_count < 40 else 5

        for move in valid_moves:
            simulated_board = simulate_move(board, move, self.current_symbol)
            if simulated_board == board:
                continue  # Invalid move (no pieces flipped)

            score = minimax(simulated_board, search_depth, float('-inf'), float('inf'),
                            maximizing_player=False, model=self.model, device=self.device,
                            symbol=self.current_symbol, start_time=start_time, time_limit=2.5)

            if score > best_score:
                best_score = score
                best_move = move

        if best_move:
            return best_move
        return random.randint(0, 7), random.randint(0, 7)


if __name__ == '__main__':
    session_id = sys.argv[1]
    player_id = sys.argv[2]
    print('Bienvenido ' + player_id + '!')
    othello_player = OthelloPlayer(player_id)
    if othello_player.connect(session_id):
        othello_player.play()
    print('Hasta pronto!')
