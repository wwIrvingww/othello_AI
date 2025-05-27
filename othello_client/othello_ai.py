import random
import time
import copy
import torch
from evaluator_utils import load_model, evaluate

import os
model_path = os.path.join(os.path.dirname(__file__), "model.pt")
model, device = load_model(os.path.abspath(model_path))


DIRECTIONS = [
    (-1, -1),  # UP-LEFT
    (-1, 0),   # UP
    (-1, 1),   # UP-RIGHT
    (0, -1),   # LEFT
    (0, 1),    # RIGHT
    (1, -1),   # DOWN-LEFT
    (1, 0),    # DOWN
    (1, 1)     # DOWN-RIGHT
]

def in_bounds(x, y):
    return 0 <= x < 8 and 0 <= y < 8

def valid_movements(board, player):
    opponent = -player
    valid_moves = []

    for x in range(8):
        for y in range(8):
            if board[x][y] != 0:
                continue

            for dx, dy in DIRECTIONS:
                i, j = x + dx, y + dy
                found_opponent = False

                while in_bounds(i, j) and board[i][j] == opponent:
                    i += dx
                    j += dy
                    found_opponent = True

                if found_opponent and in_bounds(i, j) and board[i][j] == player:
                    valid_moves.append((x, y))
                    break

    return valid_moves
 

def ai_move(board, player):
    #model, device = load_model("model.pt")
    def simulate_move(board, move, symbol):
        row, col = move
        if board[row][col] != 0:
            return board

        new_board = copy.deepcopy(board)
        new_board[row][col] = symbol

        for dr, dc in DIRECTIONS:
            pieces_to_flip = []
            r, c = row + dr, col + dc

            while in_bounds(r, c) and new_board[r][c] == -symbol:
                pieces_to_flip.append((r, c))
                r += dr
                c += dc

            if in_bounds(r, c) and new_board[r][c] == symbol and pieces_to_flip:
                for flip_r, flip_c in pieces_to_flip:
                    new_board[flip_r][flip_c] = symbol

        return new_board

    def prioritize_opening_moves(valid_moves):
        corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
        bad_spots = [(0, 1), (1, 0), (1, 1), (0, 6), (1, 6), (1, 7),
                    (6, 0), (6, 1), (7, 1), (6, 6), (6, 7), (7, 6)]

        for move in valid_moves:
            if move in corners:
                return move
        safe_moves = [m for m in valid_moves if m not in bad_spots]
        return random.choice(safe_moves) if safe_moves else random.choice(valid_moves)

    def minimax(board, depth, alpha, beta, maximizing_player, symbol, start_time, time_limit=2.5):
        if time.time() - start_time >= time_limit:
            return evaluate(board, model, device, symbol)

        current_symbol = symbol if maximizing_player else -symbol
        valid_moves = valid_movements(board, current_symbol)
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
                eval_score = minimax(next_board, depth - 1, alpha, beta, False, symbol, start_time, time_limit)
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
                eval_score = minimax(next_board, depth - 1, alpha, beta, True, symbol, start_time, time_limit)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    valid_moves = valid_movements(board, player)
    if not valid_moves:
        return random.randint(0, 7), random.randint(0, 7)

    piece_count = sum(1 for row in board for cell in row if cell != 0)
    if piece_count < 10:
        return prioritize_opening_moves(valid_moves)

    best_score = float('-inf')
    best_move = None
    start_time = time.time()
    depth = 3 if piece_count < 20 else 4 if piece_count < 40 else 5

    for move in valid_moves:
        next_board = simulate_move(board, move, player)
        if next_board == board:
            continue
        score = minimax(next_board, depth, float('-inf'), float('inf'),
                        maximizing_player=False, symbol=player, start_time=start_time)
        if score > best_score:
            best_score = score
            best_move = move

    return best_move if best_move else random.choice(valid_moves)


if __name__ == "__main__":
    # Tablero inicial de prueba
    board = [[0 for _ in range(8)] for _ in range(8)]
    board[3][3], board[4][4] = 1, 1
    board[3][4], board[4][3] = -1, -1

    move = ai_move(board, player=1)
    print("Best move:", move)