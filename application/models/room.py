import typing as T
from dataclasses import dataclass
from application.game import CardGameSession


class Room:
    def __init__(self, room_id, is_public, players_limit):
        self.game_state = "waiting"
        self.room_id = room_id
        self.players = []
        self.card_game = CardGameSession(players_limit)
        self.players_limit = players_limit
        self.is_public = is_public
        self.url = None  # To store the URL for private rooms
