import random
import os
import pickle
from string import ascii_uppercase

from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO, rooms, emit

from application.models import Room, Session, LogData, Player
from application.game import CardGameSession, CardGame, Card

app = Flask(__name__)
app.config["SECRET_KEY"] = "hjhjsdahhds"
socketio = SocketIO(app, cors_allowed_origins='*')


def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)

        if not os.path.exists(f"./session_{code}.pickle"):
            break

    return code


def get_room(room_id):
    if os.path.exists(f"./{room_id}.pickle"):
        with open(f"./{room_id}.pickle", "rb") as f:
            return pickle.load(f)


def upsert_room(room_id, r=None):
    with open(f"./{room_id}.pickle", "wb") as f:
        pickle.dump(r, f)


@app.route("/", methods=["POST", "GET"])
def home():
    session.clear()
    if request.method == "POST":
        room_id = request.form.get("room_id")
        name = request.form.get("name")

        if not room_id:
            return render_template("home.html", error="Please enter a room id.", name=name, room_id=room_id)

        if not name:
            return render_template("home.html", error="Please enter a room id.", name=name, room_id=room_id)

        r: Room = get_room(room_id)

        if len(r.players) == r.players_limit:
            return render_template("home.html", error="Player limit reached.", name=name, room_id=room_id)

        session["s"] = Session(name=name, room_id=room_id, private_room_id=f"{name}_{room_id}", id=len(r.players))
        player = Player(id=len(r.players), name=name, state="playing")

        log_data = LogData(message=f"{name} joined")

        r.players.append(player)
        r.logs.append(log_data)

        if len(r.players) == r.players_limit:
            r.game_state = "playing"

        upsert_room(room_id, r=r)
        return redirect(url_for("room"))

    return render_template("home.html")


@app.route("/host", methods=["POST", "GET"])
def host():
    if request.method == "POST":
        name = request.form.get("name")
        players_limit = request.form.get("players_limit")

        if not name:
            return render_template(
                "host.html",
                error="Please enter a name.",
                players_limit=players_limit,
                is_public=True
            )

        if not players_limit:
            return render_template(
                "host.html",
                error="Choose Player Limit.",
                players_limit=players_limit,
                is_public=True
            )

        room_id = generate_unique_code(4)

        session["s"] = Session(name=name, room_id=room_id, private_room_id=f"{name}_{room_id}")
        player = Player(id=0, name=name, state="playing")

        r = Room(
            room_id=room_id,
            game_state="waiting",
            players=[player],
            players_limit=int(players_limit),
            is_public=False,
            logs=[],
            card_game=None
        )

        upsert_room(room_id=room_id, r=r)

        return redirect(url_for("room"))

    return render_template("host.html", players_limit=3)


@app.route("/room")
def room():
    s = session.get("s")
    if s is None:
        return redirect(url_for("home"))

    # a = s.room_id
    return render_template("room.html", room_id=s["room_id"], name=s["name"])


@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return

    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    send(content, to=room)
    # rooms[room]["messages"].append(content)
    print(f"{session.get('name')} said: {data['data']}")


@socketio.on("connect")
def connect(auth):
    s = session.get("s")
    room_id = s["room_id"]
    private_room_id = s["private_room_id"]

    r: Room = get_room(room_id=room_id)
    if not r:
        return

    join_room(room_id)
    join_room(private_room_id)

    if len(r.players) == r.players_limit:

        # r.game_state = "playing"
        # upsert_room(room_id=room_id, r=r)

        c = CardGameSession.load_game(session_id=f"session_{room_id}")
        if c:
            game: CardGame = c
        else:
            game: CardGameSession = CardGameSession(number_of_players=r.players_limit, session_id=room_id)
            game.initialize_game()
            game.save_game()

        data = {
            "cards_in_play": [{"card": f"{c.rank}{c.suit}"} for c in game.cards_in_play],
            "current_turn": game.current_player
        }

        priv_data = []

        for p in r.players:
            d = {
                "my_deck": [{"card": f"{c.rank}{c.suit}"} for c in game.players[p.id]],
                "opponent_cards": [],
                "name": p.name,
                "id": p.id,
                "current_turn": game.current_player
            }

            i = (p.id + 1) % len(game.players)
            while i != p.id:
                d["opponent_cards"].append(len(game.players[i]))
                i = (i + 1) % len(game.players)

            priv_data.append(d)

        if game.game_status == "card_exchange":
            # data["current_turn"] = None
            last: Card = game.players[game.current_player][0]

            first_player_id = game.finished_players[0]

            data["card_exchange"] = {
                "first": {
                    "id": r.players[first_player_id].id,
                    "name": r.players[first_player_id].name,
                },
                "last": {
                    "id": r.players[game.current_player].id,
                    "name": r.players[game.current_player].name,
                    "card": f"{last.rank}{last.suit}"
                }
            }

        for x in priv_data:
            send({"name": s["name"], "message": "PRIV DATA", "priv_play": x}, to=f"{x['name']}_{room_id}")
        send({"name": s["name"], "message": "DATA", "play": data}, to=room_id)

        b = 0

    # send({"name": s["name"], "message": "has entered the room"}, to=room_id)
    # send({"name": s["name"], "message": "TEST"}, to=private_room_id)
    # rooms[room]["members"] += 1
    # print(f"{name} joined room {room}")


@socketio.on("disconnect")
def disconnect():
    s = session.get("s")
    # room_id = s["room_id"]
    # private_room_id = s["private_room_id"]
    # name = s["name"]
    #
    # leave_room(room_id)
    # leave_room(private_room_id)
    #
    # r: Room = get_room(room_id)
    # if not r:
    #     return
    #
    # log_data = LogData(message=f"{name} left")
    # r.logs.append(log_data)
    #
    # r.players -= 1
    #
    # if r.players != r.players_limit:
    #     r.game_state = "waiting"

    # room = session.get("room")
    # name = session.get("name")
    # leave_room(room)
    #
    # if room in rooms:
    #     rooms[room]["members"] -= 1
    #     if rooms[room]["members"] <= 0:
    #         del rooms[room]

    # send({"name": name, "message": "has left the room"}, to=room_id)
    # print(f"{name} has left the room {room}")


@socketio.on("exchange_card")
def exchange(c: dict):
    d = c.get("data", [])
    if not d:
        return

    idx = d[-1]

    s = session.get("s")
    room_id = s["room_id"]

    game: CardGameSession = CardGameSession.load_game(session_id=f"session_{room_id}")
    for_first = game.players[game.current_player].pop(0)
    for_last = game.players[game.finished_players[0]].pop(int(idx))

    game.players[game.current_player].append(for_last)
    game.players[game.finished_players[0]].append(for_first)

    game.finished_players = []
    game.game_status = "playing"
    game.save_game()

    r: Room = get_room(room_id=room_id)

    data = {
        "cards_in_play": [{"card": f"{c.rank}{c.suit}"} for c in game.cards_in_play],
        "current_turn": game.current_player
    }

    priv_data = []
    for p in r.players:
        d = {
            "my_deck": [{"card": f"{c.rank}{c.suit}"} for c in game.players[p.id]],
            "opponent_cards": [],
            "name": p.name,
            "id": p.id,
            "current_turn": game.current_player
        }

        i = (p.id + 1) % len(game.players)
        while i != p.id:
            d["opponent_cards"].append(len(game.players[i]))
            i = (i + 1) % len(game.players)

        priv_data.append(d)

    for x in priv_data:
        send({"name": s["name"], "message": "PRIV DATA", "priv_play": x}, to=f"{x['name']}_{room_id}")
    send({"name": s["name"], "message": "DATA", "play": data}, to=room_id)


@socketio.on("drop")
def drop(b):
    s = session.get("s")
    room_id = s["room_id"]
    _id = int(s["id"])

    game: CardGameSession = CardGameSession.load_game(session_id=f"session_{room_id}")
    # cards = [int(v) for v in b["data"]]
    cards = [game.players[_id][int(v)] for v in b["data"]]
    turn = game.take_turn(player_index=_id, selected_cards=cards)

    if not turn:
        return

    game.save_game()

    r: Room = get_room(room_id=room_id)

    data = {
        "cards_in_play": [{"card": f"{c.rank}{c.suit}"} for c in game.cards_in_play],
        "current_turn": game.current_player
    }

    priv_data = []
    for p in r.players:
        d = {
            "my_deck": [{"card": f"{c.rank}{c.suit}"} for c in game.players[p.id]],
            "opponent_cards": [],
            "name": p.name,
            "id": p.id,
            "current_turn": game.current_player
        }

        i = (p.id + 1) % len(game.players)
        while i != p.id:
            d["opponent_cards"].append(len(game.players[i]))
            i = (i + 1) % len(game.players)

        priv_data.append(d)

    if game.game_status == "card_exchange":
        # data["current_turn"] = None
        last: Card = game.players[game.current_player][0]

        first_player_id = game.finished_players[0]

        data["card_exchange"] = {
            "first": {
                "id": r.players[first_player_id].id,
                "name": r.players[first_player_id].name,
            },
            "last": {
                "id": r.players[game.current_player].id,
                "name": r.players[game.current_player].name,
                "card": f"{last.rank}{last.suit}"
            }
        }

    for x in priv_data:
        send({"name": s["name"], "message": "PRIV DATA", "priv_play": x}, to=f"{x['name']}_{room_id}")
    send({"name": s["name"], "message": "DATA", "play": data}, to=room_id)


if __name__ == "__main__":
    socketio.run(app, debug=True)
