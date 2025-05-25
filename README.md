# OthelloClient

Codigo para conectarse al servidor de Othello para la competencia del curso CC3085 2024

## Instalación

Para  el correcto funcionamiento del codigo, asegurese de tener instaladas las librerias _requests_, _random_, _sys_, _time_

En (muy raro) caso que aun no tenga instaladas estas librarias, puede instalarlas con el siguiente comando: 

```bash
pip install requests random sys time 
```

## Uso

Al momento de querer que el cliente se subscriba una sesión de juego y compita, corra el siguiente comando en el directorio donde se encuente el script. 

```bash
python othello_player.py <session_id> <player_id>  
```

Donde <session_id> es el nombre de la sesioón a la que se desea registrar y <player_id> será su nombre de usuario del servidor. 

## Modificación

SOLAMENTE MODIFIQUE EL METODO **AI_MOVE** dentro de la clase OthelloClient(): 

En la versión inicial, el método se ve de la siguiente manera.  

```python
def AI_MOVE(self, board):
    row = random.randint(0, 7)
    col = random.randint(0, 7)
    return (row, col)
```

Board es un array de arrays definido de la siguiente manera en su estado inicial: 

```python
board = [[0] * 8 for _ in range(8)]
board[3][3] = 1
board[3][4] = -1
board[4][3] = -1
board[4][4] = 1
```

Donde 1 representan las posiciones ocupadas por piezas blancas, y -1 las posiciones ocupadas por piezas negras. 

Para saber en la partida actual que color de pieza tiene asignada, esta informacioón se encuentra almacenada en la siguiente variable del código: 

```python
self.current_symbol
```

## 🧪 Instrucciones para correr el servidor de pruebas, frontend y jugador IA

### 🔧 1. Instalar dependencias

Asegúrate de tener instaladas las bibliotecas necesarias:

```bash
pip install fastapi uvicorn streamlit requests torch
```

## 🚀 2. Correr el servidor de pruebas

```python
python server/othello_server.py
```

## 🧠 3. Iniciar un jugador IA

```bash
python othello_player.py <session_id> <player_id>
```


## 🎨 4. Correr el visualizador frontend con Streamlit

```python
streamlit run frontend/othello_visualizer.py
```
Usa el mismo session_id en el frontend para visualizar correctamente la partida.

## License

[MIT](https://choosealicense.com/licenses/mit/)
