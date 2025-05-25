import requests
import random
import sys
import time
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
        # === Josue ===
        def get_valid_moves(board, symbol):
            """
            Returns a list of valid moves (row, col) for the given symbol.
            """
            valid_moves = []
            directions = [(0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1)]
            
            for row in range(8):
                for col in range(8):
                    if board[row][col] != 0:  # Skip non-empty cells
                        continue
                        
                    # Check all 8 directions
                    for dr, dc in directions:
                        r, c = row + dr, col + dc
                        # Check if there's an opponent's piece adjacent
                        if (0 <= r < 8 and 0 <= c < 8 and 
                            board[r][c] == -symbol):
                            # Continue in this direction
                            r += dr
                            c += dc
                            found_opponent = False
                            
                            while 0 <= r < 8 and 0 <= c < 8:
                                if board[r][c] == -symbol:
                                    found_opponent = True
                                elif board[r][c] == symbol and found_opponent:
                                    # Found a valid move
                                    valid_moves.append((row, col))
                                    break
                                else:  # Empty cell or reached our own piece without opponent's piece
                                    break
                                r += dr
                                c += dc
            
            return valid_moves

        def simulate_move(board, move, symbol):
            """
            Returns a copy of the board with the move applied.
            Flips captured opponent pieces.
            """
            row, col = move
            new_board = [row[:] for row in board]  # Create a deep copy
            
            if new_board[row][col] != 0:  # Cell already occupied
                return new_board
                
            new_board[row][col] = symbol
            directions = [(0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1)]
            
            # Check all 8 directions
            for dr, dc in directions:
                pieces_to_flip = []
                r, c = row + dr, col + dc
                
                # Collect opponent pieces
                while 0 <= r < 8 and 0 <= c < 8 and new_board[r][c] == -symbol:
                    pieces_to_flip.append((r, c))
                    r += dr
                    c += dc
                    
                # If we find our own piece at the end, flip all collected pieces
                if 0 <= r < 8 and 0 <= c < 8 and new_board[r][c] == symbol and pieces_to_flip:
                    for flip_r, flip_c in pieces_to_flip:
                        new_board[flip_r][flip_c] = symbol
            
            return new_board

        def prioritize_opening_moves(valid_moves):
            """
            Prioritizes corner moves and avoids moves adjacent to corners.
            """
            corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
            bad_spots = [(0, 1), (1, 0), (1, 1), (0, 6), (1, 6), (1, 7), 
                         (6, 0), (6, 1), (7, 1), (6, 6), (6, 7), (7, 6)]
            
            # First priority: corners
            for move in valid_moves:
                if move in corners:
                    return move
                    
            # Filter out bad spots if possible
            safe_moves = [move for move in valid_moves if move not in bad_spots]
            if safe_moves:
                return random.choice(safe_moves)
            
            # If no choice, return any valid move
            return random.choice(valid_moves) if valid_moves else None

        # === Sebas ===
        def minimax(board, depth, alpha, beta, maximizing_player, model, device, symbol, start_time, time_limit=2.5):
            """
            Algoritmo Minimax con poda alfa-beta y límite de tiempo.
            """
            # Cortar si el tiempo excede
            if time.time() - start_time >= time_limit:
                return evaluate(board, model, device, symbol)

            # Obtener movimientos válidos para el jugador actual del turno
            current_symbol = symbol if maximizing_player else -symbol
            valid_moves = get_valid_moves(board, current_symbol)

            # Si no hay movimientos o se llegó al fondo
            if depth == 0 or not valid_moves:
                return evaluate(board, model, device, symbol)

            # Maximización (jugador actual)
            if maximizing_player:
                max_eval = float('-inf')
                for move in valid_moves:
                    next_board = simulate_move(board, move, current_symbol)

                    # Cortar por tiempo si se excede durante iteraciones
                    if time.time() - start_time >= time_limit:
                        break

                    # Solo una capa más de profundidad si hay tiempo
                    if depth > 1:
                        eval = minimax(next_board, depth - 1, alpha, beta, False, model, device, symbol, start_time, time_limit)
                    else:
                        eval = evaluate(next_board, model, device, symbol)

                    max_eval = max(max_eval, eval)
                    alpha = max(alpha, eval)
                    if beta <= alpha:
                        break  # poda
                return max_eval

            # Minimización (oponente)
            else:
                min_eval = float('inf')
                for move in valid_moves:
                    next_board = simulate_move(board, move, current_symbol)

                    if time.time() - start_time >= time_limit:
                        break

                    if depth > 1:
                        eval = minimax(next_board, depth - 1, alpha, beta, True, model, device, symbol, start_time, time_limit)
                    else:
                        eval = evaluate(next_board, model, device, symbol)

                    min_eval = min(min_eval, eval)
                    beta = min(beta, eval)
                    if beta <= alpha:
                        break  # poda
                return min_eval

        # === MAIN AI LOGIC - NOW USING MINIMAX ===
        # Get valid moves
        valid_moves = get_valid_moves(board, self.current_symbol)
        
        # If no valid moves, return a random move (fallback)
        if not valid_moves:
            return random.randint(0, 7), random.randint(0, 7)
        
        # For early game (first 10 moves), prioritize strategic positions
        piece_count = sum(1 for row in board for cell in row if cell != 0)
        if piece_count < 10:
            strategic_move = prioritize_opening_moves(valid_moves)
            if strategic_move:
                return strategic_move

        # Use minimax for decision making
        best_score = float('-inf')
        best_move = valid_moves[0]  # Default to first valid move
        start_time = time.time()
        
        # Determine search depth based on game phase
        if piece_count < 20:
            search_depth = 3  # Early game: moderate depth
        elif piece_count < 40:
            search_depth = 4  # Mid game: deeper search
        else:
            search_depth = 5  # End game: deep search
            
        # Evaluate each move using minimax
        for move in valid_moves:
            # Simulate making this move
            simulated_board = simulate_move(board, move, self.current_symbol)
            
            # Get score using minimax (opponent's turn after our move)
            score = minimax(
                simulated_board,
                depth=search_depth,
                alpha=float('-inf'),
                beta=float('inf'),
                maximizing_player=False,  # Opponent's turn next
                model=self.model,
                device=self.device,
                symbol=self.current_symbol,
                start_time=start_time,
                time_limit=2.5  # Time limit in seconds
            )
            
            # Update best move if better score found
            if score > best_score:
                best_score = score
                best_move = move
                
        return best_move

if __name__ == '__main__':
    session_id = sys.argv[1]
    player_id = sys.argv[2]
    print('Bienvenido ' + player_id + '!')
    othello_player = OthelloPlayer(player_id)
    if othello_player.connect(session_id):
        othello_player.play()
    print('Hasta pronto!')
