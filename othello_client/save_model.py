import torch
from board_evaluator import BoardEvaluator

def save_model():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = BoardEvaluator().to(device)
    
    # Guardar pesos iniciales compatibles con BoardEvaluator
    torch.save(model.state_dict(), 'model.pt')
    print("✅ Modelo guardado como model.pt (compatible con BoardEvaluator)")

if __name__ == '__main__':
    save_model()
