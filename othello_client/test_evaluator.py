from evaluator_utils import load_model, evaluate

# Cargar modelo
model, device = load_model("model.pt")

# Tablero base (posición inicial de Othello)
board = [[0]*8 for _ in range(8)]
board[3][3], board[3][4] =  1, -1
board[4][3], board[4][4] = -1,  1

# Evalúa para el jugador blanco (symbol = 1)
score = evaluate(board, model, device, symbol=1)
print("Score tablero inicial (blanco):", score)
