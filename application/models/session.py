import typing as T
from dataclasses import dataclass

from application.game import CardGameSession


@dataclass()
class LogData:
    message: T.AnyStr


@dataclass()
class Session:
    name: T.AnyStr
    room_id: T.AnyStr
    private_room_id: T.AnyStr
    id: int = 0
    # player_id: int


@dataclass()
class Player:
    id: int
    name: T.AnyStr
    state: T.Literal["finished", "playing"]


@dataclass()
class Room:
    room_id: T.AnyStr
    logs: T.List[LogData]
    game_state: T.Literal["waiting", "in_session", "ended"]
    players: T.List[Player]
    players_limit: int
    is_public: bool
    card_game: T.Optional[CardGameSession]
