import torch
import numpy as np
from board_evaluator import BoardEvaluator

def load_model(path="model.pt"):
    """
    Carga el modelo entrenado desde el archivo y lo devuelve junto con el dispositivo.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model  = BoardEvaluator().to(device)
    model.load_state_dict(torch.load(path, map_location=device))
    model.eval()
    return model, device

def evaluate(board, model, device, symbol):
    """
    Evalúa una posición de Othello usando el modelo.

    Parámetros:
    - board: lista 8x8 con 1 (blanco), -1 (negro), 0 (vacío)
    - model: instancia de BoardEvaluator
    - device: torch.device
    - symbol: 1 si jugador actual es blanco, -1 si negro

    Retorna:
    - score promedio en [-1,1] sobre las 8 simetrías del tablero
    """
    # Convertir a array y generar canales
    arr = np.array(board, dtype=np.float32)
    current  = (arr == symbol).astype(np.float32)
    opponent = (arr == -symbol).astype(np.float32)
    empty    = (arr == 0).astype(np.float32)
    x        = np.stack([current, opponent, empty], axis=0)

    x_tensor = torch.tensor(x).unsqueeze(0).to(device)  # [1,3,8,8]
    scores   = []

    # Promediar sobre 4 rotaciones y sus reflejos horizontales
    for k in range(4):
        xr = torch.rot90(x_tensor, k, [2, 3])
        scores.append(model(xr).item())
        xf = torch.flip(xr, [3])
        scores.append(model(xf).item())

    return float(sum(scores) / len(scores))
