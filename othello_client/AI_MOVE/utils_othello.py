import copy

def get_valid_moves(board, symbol):
    opponent = 'W' if symbol == 'B' else 'B'
    directions = [(-1, -1), (-1, 0), (-1, 1),
                  (0, -1),          (0, 1),
                  (1, -1),  (1, 0),  (1, 1)]

    valid_moves = set()

    for r in range(8):
        for c in range(8):
            if board[r][c] != '.':
                continue

            for dr, dc in directions:
                i, j = r + dr, c + dc
                has_opponent_piece = False

                while 0 <= i < 8 and 0 <= j < 8 and board[i][j] == opponent:
                    i += dr
                    j += dc
                    has_opponent_piece = True

                if has_opponent_piece and 0 <= i < 8 and 0 <= j < 8 and board[i][j] == symbol:
                    valid_moves.add((r, c))
                    break

    return list(valid_moves)


def simulate_move(board, move, symbol):
    opponent = 'W' if symbol == 'B' else 'B'
    directions = [(-1, -1), (-1, 0), (-1, 1),
                  (0, -1),          (0, 1),
                  (1, -1),  (1, 0),  (1, 1)]

    r, c = move
    new_board = copy.deepcopy(board)
    new_board[r][c] = symbol

    for dr, dc in directions:
        i, j = r + dr, c + dc
        pieces_to_flip = []

        while 0 <= i < 8 and 0 <= j < 8 and new_board[i][j] == opponent:
            pieces_to_flip.append((i, j))
            i += dr
            j += dc

        if 0 <= i < 8 and 0 <= j < 8 and new_board[i][j] == symbol:
            for x, y in pieces_to_flip:
                new_board[x][y] = symbol

    return new_board


def create_initial_board():
    board = [['.' for _ in range(8)] for _ in range(8)]
    board[3][3] = board[4][4] = 'W'
    board[3][4] = board[4][3] = 'B'
    return board
