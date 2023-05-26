import random

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room, close_room, rooms, disconnect

from application.game import CardGame

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

open_games = {}  # Stores all open public rooms (no link required to join)
private_games = {}  # Stores all private rooms with sharable links


class Room:
    def __init__(self, room_id, is_public, players_limit):
        self.game_state = "waiting"
        self.room_id = room_id
        self.players = []
        self.card_game = CardGame(players_limit)
        self.players_limit = players_limit
        self.is_public = is_public
        self.url = None  # To store the URL for private rooms


@app.route("/")
def index():
    return render_template("index.html")


@app.route('/createroom', methods=["POST"])
def create_room():
    room_id = generate_unique_id()
    is_public = request.form.get("is_public") == "public"
    players_limit = int(request.form.get('players_limit'))
    new_room = Room(room_id, is_public, players_limit)

    if is_public:
        open_games[room_id] = new_room
    else:
        new_room.url = generate_unique_private_url()
        private_games[room_id] = new_room

    # Redirect the user to the room they have created
    data = {
        'room_id': room_id,
        'players_limit': players_limit,
        'is_public': is_public,
        'url': new_room.url
    }

    return jsonify(data)


@app.route('/joinpublic')
def join_public_room(room_id):
    return render_template("game.html", room_id=room_id)


@app.route('/joinprivate/<private_id>', methods=['GET'])
def join_private_room(private_id):
    for room in private_games.values():
        if room.url == private_id:
            return render_template("game.html", room_id=room.room_id)
    return "Room not found", 404


#
#
# @app.route('/joinpublic', methods=['POST'])
# def join_public_room():
#     room_id = request.form.get('room_id')
#
#     if room_id in open_games:
#         # Join the room and set up the game if not full
#         # Render room page
#         pass
#     else:
#         # Render an error message or redirect back to the main page
#         pass
#
#
# @app.route('/joinprivate/<private_id>', methods=['GET'])
# def join_private_room(private_id):
#     # Search and join the private room with a unique link
#     # Render room page or error message
#     pass
#
#
def generate_unique_id():
    room_id = random.randint(1000, 9999)
    while room_id in open_games or room_id in private_games:
        room_id = random.randint(1000, 9999)
    return room_id


def generate_unique_private_url():
    # Your implementation of generating a unique URL for private rooms
    pass


#
#
# @socketio.on('join_room')
# def handle_join_room_event(data):
#     room_id = data['room_id']
#
#     if room_id in open_games:
#         current_room = open_games[room_id]
#     else:
#         current_room = private_games[room_id]
#
#     join_room(room_id)
#     current_room.players.append(request.sid)
#
#     if len(current_room.players) == current_room.players_limit:
#         current_room.game_state = "playing"
#         current_room.card_game.initialize_game()
#
#     emit('player_joined', room=room_id)
#
#
# @socketio.on('play_card')
# def handle_play_card_event(data):
#     room_id = data['room_id']
#
#     if room_id in open_games:
#         current_room = open_games[room_id]
#     else:
#         current_room = private_games[room_id]
#
#     # Update game state based on player's play
#     pass
#
#
# @socketio.on('disconnect')
# def handle_disconnect_event():
#     for game_room in rooms(request.sid):
#         leave_room(game_room)
#         if game_room in open_games:
#             del open_games[game_room]
#         elif game_room in private_games:
#             del private_games[game_room]
#         emit('game_over', room=game_room)


########

# game = CardGame(4)
# game.initialize_game()
#
#
# @app.route("/")
# def index():
#     return render_template("index.html")
#
#
# @socketio.on("connect")
# def on_connect():
#     print("A player connected")
#
#
# @socketio.on("disconnect")
# def on_disconnect():
#     print("A player disconnected")
#
#
# @socketio.on("play_card")
# def handle_play_card(player_index, selected_cards):
#     game.take_turn(player_index, selected_cards)
#     emit("game_updated", game, broadcast=True)


# @socketio.on("connect")
# def connect():
#     print("ok")
#     emit('my_response', {'data': 'Connected'})


# @app.route('/')
# def hello_world():  # put application's code here
#     return render_template('index.html', async_mode=socketio.async_mode)


# if __name__ == '__main__':
#     # app.run()
#     socketio.run(app, host="0.0.0.0", debug=True)
