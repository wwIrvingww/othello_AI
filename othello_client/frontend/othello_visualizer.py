import streamlit as st
import requests
import numpy as np
import time

# Server URL
SERVER_URL = "http://localhost:8000"

# Helper function to render the board
def render_board(board):
    """
    Renders the Othello board as an 8x8 HTML table with borders
    """
    html = "<style>td {width: 40px; height: 40px; text-align: center; font-size: 24px; border: 1px solid black;} table {border-collapse: collapse;}</style>"
    html += "<table>"

    for row in board:
        html += "<tr>"
        for cell in row:
            if cell == 1:
                html += "<td>⚪</td>"
            elif cell == -1:
                html += "<td>⚫</td>"
            else:
                html += "<td></td>"  # Empty cell
        html += "</tr>"

    html += "</table>"
    st.markdown(html, unsafe_allow_html=True)

# Streamlit app
st.title("Othello Match Visualizer")

# Input session and player details
session_name = st.text_input("Enter Session Name", value="game1")
player_name = st.text_input("Enter Player Name", value="player1")

# Fetch match info
if st.button("Connect to Match"):
    with st.spinner("Connecting to the server..."):
        # Get match info
        match_info = requests.post(
            f"{SERVER_URL}/player/match_info",
            params={"session_name": session_name, "player_name": player_name}
        ).json()

        if match_info["match_status"] == "active":
            st.success(f"Connected to match: {match_info['match']}")
            match_id = match_info["match"]
            symbol = match_info["symbol"]

            # Display player symbol
            if symbol == 1:
                st.write("You are playing as: ⚪ (White)")
            elif symbol == -1:
                st.write("You are playing as: ⚫ (Black)")

            # Continuously fetch and display the board
            while True:
                turn_info = requests.post(
                    f"{SERVER_URL}/player/turn_to_move",
                    params={"session_name": session_name, "player_name": player_name, "match_id": match_id}
                ).json()

                # Render the board
                render_board(turn_info["board"])

                # Display game status
                if turn_info["game_over"]:
                    st.write(f"### Game Over! Winner: {turn_info['winner']}")
                    break

                # Display current score
                score = turn_info["score"]
                st.write(f"Score: ⚪ {score['white']} - ⚫ {score['black']}")

                # Wait for a short time before refreshing
                time.sleep(2)
        else:
            st.error("Failed to connect to an active match. Please check the session and player name.")