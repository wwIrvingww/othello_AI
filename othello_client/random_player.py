# random_player.py
import sys
import time
import requests
import random

host_name = 'http://localhost:8000'

class RandomPlayer:
    def __init__(self, username):
        self.username = username
        self.session_name = None
        self.current_symbol = None

    def connect(self, session_name) -> bool:
        resp = requests.post(
            f"{host_name}/player/new_player",
            params={'session_name': session_name, 'player_name': self.username}
        ).json()
        print(resp.get('message'))
        self.session_name = session_name
        return resp.get('status') == 200

    def play(self):
        # 1) Información de la sesión
        session_info = requests.post(
            f"{host_name}/game/game_info",
            params={'session_name': self.session_name}
        ).json()

        while session_info.get('session_status') == 'active':
            try:
                if session_info.get('round_status') == 'ready':
                    # 2) Información del match
                    match_info = requests.post(
                        f"{host_name}/player/match_info",
                        params={
                            'session_name': self.session_name,
                            'player_name':  self.username
                        }
                    ).json()

                    # 3) Si estás en bench, espera hasta que te asignen partida
                    while match_info.get('match_status') == 'bench':
                        print('You are benched this round. Take a rest while you wait.')
                        time.sleep(5)
                        match_info = requests.post(
                            f"{host_name}/player/match_info",
                            params={
                                'session_name': self.session_name,
                                'player_name':  self.username
                            }
                        ).json()

                    # 4) Ya inició la partida: guardamos tu símbolo
                    self.current_symbol = match_info.get('symbol')
                    print(f"Let's play! You are {'white' if self.current_symbol == 1 else 'black'}.")

                    # 5) Bucle de turnos
                    while match_info.get('match_status') == 'active':
                        turn_info = requests.post(
                            f"{host_name}/player/turn_to_move",
                            params={
                                'session_name': self.session_name,
                                'player_name':  self.username,
                                'match_id':     match_info.get('match')
                            }
                        ).json()

                        # 5.1) Si el juego terminó, salimos
                        if turn_info.get('game_over'):
                            print('Game Over. Winner:', turn_info.get('winner'))
                            break

                        # 5.2) Si es tu turno
                        if turn_info.get('turn'):
                            board = turn_info.get('board')
                            move = self.AI_MOVE(board)
                            if move is None:
                                # No hay jugadas legales, pasamos turno
                                print("No valid moves available — passing turn.")
                            else:
                                print(f"Playing move {move}")
                                requests.post(
                                    f"{host_name}/player/move",
                                    params={
                                        'session_name': self.session_name,
                                        'player_name':  self.username,
                                        'match_id':     match_info.get('match'),
                                        'row':          move[0],
                                        'col':          move[1]
                                    }
                                )
                        else:
                            # No es tu turno: espera un momento
                            time.sleep(1)

                        # 5.3) Actualiza estado del match
                        match_info = requests.post(
                            f"{host_name}/player/match_info",
                            params={
                                'session_name': self.session_name,
                                'player_name':  self.username
                            }
                        ).json()

                else:
                    # Ronda no lista todavía
                    print('Waiting for match lottery...')
                    time.sleep(5)

            except requests.exceptions.ConnectionError:
                continue

            # 6) Refresca estado de la sesión
            session_info = requests.post(
                f"{host_name}/game/game_info",
                params={'session_name': self.session_name}
            ).json()

    def AI_MOVE(self, board):
        """
        Devuelve un movimiento legal al azar, o None si no hay ninguno.
        """
        valid_moves = []
        directions = [
            (0, 1), (1, 1), (1, 0), (1, -1),
            (0, -1), (-1, -1), (-1, 0), (-1, 1)
        ]
        sym = self.current_symbol

        # 1) Busca todos los movimientos válidos
        for row in range(8):
            for col in range(8):
                if board[row][col] != 0:
                    continue
                for dr, dc in directions:
                    r, c = row + dr, col + dc
                    found_opponent = False
                    while 0 <= r < 8 and 0 <= c < 8:
                        if board[r][c] == -sym:
                            found_opponent = True
                        elif board[r][c] == sym and found_opponent:
                            valid_moves.append((row, col))
                            break
                        else:
                            break
                        r += dr; c += dc
                    if (row, col) in valid_moves:
                        break

        # 2) Si hay válidos, devuelve uno al azar
        if valid_moves:
            return random.choice(valid_moves)

        # 3) Si no hay, devuelve None para pasar turno
        return None


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Uso: python random_player.py <session_id> <player_id>")
        sys.exit(1)

    session_id, player_id = sys.argv[1], sys.argv[2]
    rp = RandomPlayer(player_id)
    if not rp.connect(session_id):
        print("No pude registrarme en la sesión", session_id)
        sys.exit(1)

    print(f"Jugador random '{player_id}' en sesión {session_id}. ¡A jugar!")
    rp.play()
