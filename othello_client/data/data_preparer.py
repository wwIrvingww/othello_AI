# data_preparer.py
import sys
import os
import numpy as np
import copy
import pandas as pd
from tqdm import tqdm
import pickle

def create_initial_board():
    """Crea el tablero inicial de Othello"""
    board = [['.' for _ in range(8)] for _ in range(8)]
    board[3][3] = board[4][4] = 'W'
    board[3][4] = board[4][3] = 'B'
    return board

def get_valid_moves(board, symbol):
    """Devuelve los movimientos válidos para el jugador actual"""
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
    """Simula un movimiento en el tablero"""
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

def parse_transcript(transcript, rotation=0):
    """Convierte el string de movimientos a coordenadas (fila, columna)"""
    moves = []
    for i in range(0, len(transcript), 2):
        if i+1 >= len(transcript):
            break
            
        col = ord(transcript[i]) - ord('a')
        row = int(transcript[i+1]) - 1
        
        if rotation == 180:
            row = 7 - row
            col = 7 - col
        
        # Validar coordenadas
        if 0 <= row < 8 and 0 <= col < 8:
            moves.append((row, col))
        else:
            return None  # Movimiento inválido
    
    return moves

def extract_board_states_from_game(transcript, winner):
    """Extrae los estados del tablero probando diferentes rotaciones"""
    # Probar sin rotación primero
    for rotation in [0, 180]:
        board = create_initial_board()
        turn = 'B'
        moves = parse_transcript(transcript, rotation)
        
        if not moves:
            continue
            
        winner_simple = winner[0].upper() if isinstance(winner, str) and len(winner) > 0 else 'B'
        label = 1 if winner_simple == 'B' else -1
        boards_and_labels = []
        valid_game = True
        
        for i, move in enumerate(moves):
            valid = get_valid_moves(board, turn)
            if move not in valid:
                valid_game = False
                break
                
            board = simulate_move(board, move, turn)
            boards_and_labels.append((copy.deepcopy(board), label if turn == winner_simple else -label))
            turn = 'W' if turn == 'B' else 'B'
        
        if valid_game:
            return boards_and_labels
    
    return []

def main():
    data_dir = os.path.dirname(__file__)
    parquet_fp = os.path.join(data_dir, 'train-00000-of-00001.parquet')
    output_fp = os.path.join(data_dir, 'othello_training_data.pkl')

    print(f"Cargando partidas desde '{parquet_fp}'...")
    df = pd.read_parquet(parquet_fp)

    # Preparar datos
    df['winner'] = df['outcome'].apply(lambda x: x[0].upper() if isinstance(x, str) and len(x) > 0 else None)
    valid_games = df[
        (df['winner'].isin(['B', 'W'])) & 
        (df['transcript_rot180'].notna()) & 
        (df['transcript_rot180'].str.len() >= 4)
    ].copy()
    
    print(f"\nPartidas válidas encontradas: {len(valid_games)}")
    
    # Procesar solo una muestra de 1000 partidas para depuración
    sample_size = min(1000, len(valid_games))
    valid_games = valid_games.sample(sample_size, random_state=42)
    
    all_data = []
    skipped = 0

    print(f"\nProcesando muestra de {len(valid_games)} partidas...")
    
    for idx, row in tqdm(valid_games.iterrows(), total=len(valid_games)):
        transcript = row['transcript_rot180']
        winner = row['winner']
        
        try:
            boards = extract_board_states_from_game(transcript, winner)
            if boards:
                all_data.extend(boards)
            else:
                skipped += 1
        except Exception as e:
            print(f"\nError en partida {idx}: {str(e)}")
            skipped += 1

    print(f"\nResultados finales:")
    print(f"- Partidas procesadas: {len(valid_games)}")
    print(f"- Instancias válidas: {len(all_data)}")
    print(f"- Partidas saltadas: {skipped}")

    if all_data:
        with open(output_fp, 'wb') as f:
            pickle.dump(all_data, f)
        print(f"\n✅ Datos guardados en '{output_fp}'")
        print(f"- Total de estados de tablero: {len(all_data)}")
        
        # Mostrar estadísticas de ejemplo
        print("\nEjemplo de datos guardados:")
        for i in range(min(3, len(all_data))):
            board, label = all_data[i]
            print(f"Estado {i+1}: Label = {label}")
            print(np.array(board))
            print()
    else:
        print("\n❌ No se guardaron datos - todas las partidas fueron descartadas")
        print("Posibles soluciones:")
        print("1. Verificar el formato de los transcripts")
        print("2. Revisar la implementación de las reglas del juego")
        print("3. Probar con diferentes rotaciones o versiones de los transcripts")

if __name__ == '__main__':
    main()