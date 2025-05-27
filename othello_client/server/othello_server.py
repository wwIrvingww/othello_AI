from fastapi import FastAPI, Query
from pydantic import BaseModel
import random
import uvicorn
import copy

def apply_othello_move(board, row, col, symbol):
    directions = [(0, 1), (1, 1), (1, 0), (1, -1),
                  (0, -1), (-1, -1), (-1, 0), (-1, 1)]

    flipped = []
    board[row][col] = symbol  # Place the piece

    for dr, dc in directions:
        r, c = row + dr, col + dc
        pieces = []

        while 0 <= r < 8 and 0 <= c < 8 and board[r][c] == -symbol:
            pieces.append((r, c))
            r += dr
            c += dc

        if 0 <= r < 8 and 0 <= c < 8 and board[r][c] == symbol and pieces:
            for pr, pc in pieces:
                board[pr][pc] = symbol
            flipped.extend(pieces)

    return len(flipped) > 0  # True if at least one piece was flipped


app = FastAPI()
sessions = {}

@app.post("/player/new_player")
async def new_player(session_name: str, player_name: str):
    if session_name not in sessions:
        sessions[session_name] = {
            "players": {}, 
            "session_status": "active", 
            "round_status": "ready",
            "matches": {}
        }
    
    # Assign a symbol to the player (1 for white, -1 for black)
    sessions[session_name]["players"][player_name] = {"symbol": random.choice([1, -1])}
    
    # Create a match if we have two players
    players = list(sessions[session_name]["players"].keys())
    if len(players) >= 2 and player_name in players:
        match_id = f"match_{len(sessions[session_name]['matches']) + 1}"
        sessions[session_name]["matches"][match_id] = {
            "board": [[0 for _ in range(8)] for _ in range(8)],
            "status": "active",
            "players": players[:2],
            "current_turn": players[0],
            "game_over": False,
            "winner": ""
        }
        
        # Initialize center pieces for Othello
        board = sessions[session_name]["matches"][match_id]["board"]
        board[3][3] = board[4][4] = 1  # White
        board[3][4] = board[4][3] = -1  # Black
        
        # Assign player symbols for this match
        sessions[session_name]["players"][players[0]]["match"] = match_id
        sessions[session_name]["players"][players[1]]["match"] = match_id
        
    return {"status": 200, "message": f"Welcome {player_name} to session {session_name}!"}

@app.post("/game/game_info")
async def game_info(session_name: str):
    if session_name not in sessions:
        return {"session_status": "closed"}
    return {"session_status": sessions[session_name]["session_status"], 
            "round_status": sessions[session_name]["round_status"]}

@app.post("/player/match_info")
async def match_info(session_name: str, player_name: str):
    if session_name not in sessions or player_name not in sessions[session_name]["players"]:
        return {"match_status": "inactive"}
    
    player_data = sessions[session_name]["players"][player_name]
    if "match" not in player_data:
        return {"match_status": "bench"}
    
    match_id = player_data["match"]
    return {
        "match_status": "active",
        "match": match_id,
        "symbol": player_data["symbol"]
    }

@app.post("/player/turn_to_move")
async def turn_to_move(session_name: str, player_name: str, match_id: str):
    if (session_name not in sessions or 
        match_id not in sessions[session_name]["matches"]):
        return {"game_over": True}
    
    match = sessions[session_name]["matches"][match_id]
    
    # Count pieces for score
    board = match["board"]
    white_count = sum(row.count(1) for row in board)
    black_count = sum(row.count(-1) for row in board)
    
    # Check if game is over (board full or no valid moves)
    empty_count = sum(row.count(0) for row in board)
    if empty_count == 0:
        match["game_over"] = True
        if white_count > black_count:
            match["winner"] = "White"
        elif black_count > white_count:
            match["winner"] = "Black"
        else:
            match["winner"] = "Tie"
            
    print(f"Current turn: {match['current_turn']}, checking for: {player_name}")
    return {
        "turn": match["current_turn"] == player_name,
        "board": match["board"],
        "game_over": match["game_over"],
        "winner": match["winner"],
        "score": {"white": white_count, "black": black_count}
    }

@app.post("/player/move")
async def make_move(session_name: str, player_name: str, match_id: str, row: int, col: int):
    try:
        if session_name not in sessions:
            return {"status": 400, "message": "Invalid session"}
        
        if match_id not in sessions[session_name]["matches"]:
            return {"status": 400, "message": "Invalid match ID"}
        
        match = sessions[session_name]["matches"][match_id]

        if match["current_turn"] != player_name:
            return {"status": 400, "message": "Not your turn"}

        board = match["board"]
        if row < 0 or row > 7 or col < 0 or col > 7:
            return {"status": 400, "message": "Invalid position"}

        if board[row][col] != 0:
            return {"status": 400, "message": "Cell is already occupied"}

        symbol = sessions[session_name]["players"][player_name]["symbol"]
        valid = apply_othello_move(board, row, col, symbol)
        if not valid:
            return {"status": 400, "message": "Invalid move: no pieces flipped"}

        next_player = [p for p in match["players"] if p != player_name][0]
        print(f"Turn changed to: {next_player}")
        match["current_turn"] = next_player
        return {"status": 200, "message": f"Move made at ({row},{col})"}

    except Exception as e:
        return {"status": 500, "message": f"Internal server error: {str(e)}"}

@app.get("/")
async def root():
    return {"message": "Othello Game Server Running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)