# train.py (colócalo en la raíz de othello_client/)
import os
import pickle

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

# Importa tu modelo CNN
from board_evaluator import BoardEvaluator

class OthelloDataset(Dataset):
    def __init__(self, data):
        """
        data: lista de tuplas (board, label),
              board = lista 8x8 de 'B','W','.'
              label = +1 o -1
        """
        self.data = data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        board, label = self.data[idx]

        # Creamos tres canales 8x8
        black = [[1.0 if cell=='B' else 0.0 for cell in row] for row in board]
        white = [[1.0 if cell=='W' else 0.0 for cell in row] for row in board]
        empty = [[1.0 if cell=='.' else 0.0 for cell in row] for row in board]

        x = torch.tensor([black, white, empty], dtype=torch.float32)  # [3,8,8]
        y = torch.tensor([label], dtype=torch.float32)                # [1]

        return x, y

def main():
    # Rutas
    base_dir = os.path.dirname(__file__)
    data_fp  = os.path.join(base_dir, 'data', 'othello_training_data.pkl')
    save_fp  = os.path.join(base_dir, 'AI_MOVE', 'model_trained.pt')

    # 1) Cargar datos
    print(f"Cargando datos de {data_fp} …")
    with open(data_fp, 'rb') as f:
        all_data = pickle.load(f)

    # 2) Crear Dataset y DataLoader
    dataset   = OthelloDataset(all_data)
    dataloader = DataLoader(dataset, batch_size=64, shuffle=True, num_workers=2)

    # 3) Inicializar modelo, optimizador y pérdida
    device    = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model     = BoardEvaluator().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn   = nn.MSELoss()

    # 4) Entrenamiento
    epochs = 10
    for epoch in range(1, epochs+1):
        model.train()
        running_loss = 0.0
        for x_batch, y_batch in dataloader:
            # x_batch: [B,3,8,8], y_batch: [B,1]
            x_batch = x_batch.to(device)
            y_batch = y_batch.to(device)

            optimizer.zero_grad()
            preds = model(x_batch)       # ahora recibe 4D -> OK
            loss  = loss_fn(preds, y_batch)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * x_batch.size(0)

        avg_loss = running_loss / len(dataset)
        print(f"Epoch {epoch}/{epochs} — Loss: {avg_loss:.4f}")

    # 5) Guardar modelo
    torch.save(model.state_dict(), save_fp)
    print(f"\n✅ Modelo entrenado guardado en {save_fp}")

if __name__ == '__main__':
    main()
