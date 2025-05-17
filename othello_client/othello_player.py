import requests
import random
import sys
import time
import torch.nn as nn

### Public IP Server
### Testing Server
host_name = 'http://localhost:8000'

class OthelloPlayer():

    def __init__(self, username):
        ### Player username
        self.username = username
        ### Player symbol in a match
        self.current_symbol = 0


    def connect(self, session_name) -> bool:
        """
        :param session_name:
        :return:
        """
        new_player = requests.post(host_name + '/player/new_player?session_name=' + session_name + '&player_name=' +self.username)
        new_player = new_player.json()
        self.session_name = session_name
        print(new_player['message'])
        return new_player['status'] == 200

    def play(self) -> bool:
        """
        :return:
        """
        session_info = requests.post(host_name + '/game/game_info?session_name=' + self.session_name)
        session_info = session_info.json()

        while session_info['session_status'] == 'active':
            try:
                if (session_info['round_status'] == 'ready'):

                    match_info = requests.post(host_name + '/player/match_info?session_name=' + self.session_name + '&player_name=' + self.username)
                    match_info = match_info.json()

                    while match_info['match_status'] == 'bench':
                        print('You are benched this round. Take a rest while you wait.')
                        time.sleep(15)
                        match_info = requests.post(host_name + '/player/match_info?session_name=' + self.session_name + '&player_name=' + self.username)
                        match_info = match_info.json()

                    if (match_info['match_status'] == 'active'):
                        self.current_symbol = match_info['symbol']
                        if self.current_symbol == 1:
                            print('Lets play! You are the white pieces.')
                        if self.current_symbol == -1:
                            print('Lets play! You are the black pieces.')


                    while (match_info['match_status'] == 'active'):
                        turn_info = requests.post(host_name + '/player/turn_to_move?session_name=' + self.session_name + '&player_name=' + self.username + '&match_id=' +match_info['match'])
                        turn_info = turn_info.json()
                        while not turn_info['game_over']:
                            if turn_info['turn']:
                                print('SCORE ', turn_info['score'])
                                row, col = self.AI_MOVE(turn_info['board'])
                                move = requests.post(
                                    host_name + '/player/move?session_name=' + self.session_name + '&player_name=' + self.username + '&match_id=' +
                                    match_info['match'] + '&row=' + str(row) + '&col=' + str(col))
                                move = move.json()
                                print(move['message'])
                            time.sleep(2)
                            turn_info = requests.post(host_name + '/player/turn_to_move?session_name=' + self.session_name + '&player_name=' + self.username + '&match_id=' +match_info['match'])
                            turn_info = turn_info.json()

                        print('Game Over. Winner : ' + turn_info['winner'])
                        match_info = requests.post(host_name + '/player/match_info?session_name=' + self.session_name + '&player_name=' + self.username)
                        match_info = match_info.json()


                else:
                    print('Waiting for match lottery...')
                    time.sleep(5)

            except requests.exceptions.ConnectionError:
                continue

            session_info = requests.post(host_name + '/game/game_info?session_name=' + self.session_name)
            session_info = session_info.json()



    ### Solo modiquen esta función
    def AI_MOVE(self, board):
        row = random.randint(0, 7)
        col = random.randint(0, 7)

        # === Irving ===
        class BoardEvaluator(nn.Module):
            def __init__(self):
                pass

            def forward(self, x):
                pass

        def evaluate(board, model, symbol):
            pass

        def load_model():
            """
            Cargar el modelo entrenado desde archivo.
            """
            pass

        # === Josue ===
        def get_valid_moves(board, symbol):
            """
            Retorna lista de tuplas (row, col) con movimientos válidos para symbol.
            """
            pass

        def simulate_move(board, move, symbol):
            """
            Devuelve una copia del tablero con el movimiento aplicado.
            """
            pass

        def prioritize_opening_moves(valid_moves):
            """
            Opcional: priorizar esquinas u otras jugadas estratégicas si es el inicio.
            """
            pass

        # === Sebas ===
        def minimax(board, depth, alpha, beta, maximizing_player, model, symbol, start_time, time_limit=2.5):
            """
            Retorna la mejor puntuación estimada desde la perspectiva del símbolo actual.
            Debe usar poda alfa-beta y respetar el límite de tiempo.
            """
            pass

        # === Lógica principal de decisión ===
        """
        1. Cargar modelo.
        2. Obtener movimientos válidos.
        3. Si estamos en apertura, priorizar esquinas.
        4. Ejecutar minimax para cada movimiento.
        5. Retornar el mejor movimiento posible.
        """
        return (row, col)

if __name__ == '__main__':
    script_name = sys.argv[0]
    # The rest of the arguments start from sys.argv[1]
    ### The first argument is the session id you want to join
    session_id = sys.argv[1]
    ### The second argument is the username you want to have
    player_id = sys.argv[2]

    print('Bienvenido ' + player_id + '!')
    othello_player = OthelloPlayer(player_id)
    if othello_player.connect(session_id):
        othello_player.play()
    print('Hasta pronto!')
