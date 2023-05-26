import random

RANKS = ["3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A", "2", "BJ", "RJ"]
SUITS = ["C", "D", "H", "S"]


class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank

    def __repr__(self):
        return f"{self.rank}{self.suit}"


class CardGame:
    def __init__(self, number_of_players):

        if isinstance(number_of_players, int):
            self.deck = self.create_deck()
            self.players = [[] for _ in range(number_of_players)]
            self.current_player = 0
            self.cards_in_play = []
            self.game_round = 1

            self.last_player_played = None
            self.finished_players = []
        else:
            self.deck = []
            self.players = number_of_players
            self.current_player = 1
            self.cards_in_play = [Card("D", "7")]
            self.game_round = 1

        self.game_status = "playing"

    def create_deck(self):
        deck = [Card(suit=suit, rank=rank) for rank in RANKS[:-2] for suit in SUITS]
        deck.append(Card(suit="B", rank="BJ"))  # Black Joker
        deck.append(Card(suit="R", rank="RJ"))  # Red Joker
        # deck = [Card(suit, rank) for rank in RANKS[:-2] for suit in SUITS]
        # deck.append(Card("B", "BJ"))  # Black Joker
        # deck.append(Card("R", "RJ"))  # Red Joker
        return self.shuffle_deck(deck)

    def shuffle_deck(self, deck):
        random.shuffle(deck)
        return deck

    def initialize_game(self):
        self.deal_cards()
        self.determine_first_player()

    def deal_cards(self):
        i = 0
        while self.deck:
            self.players[i % len(self.players)].append(self.deck.pop())
            i += 1

    def determine_first_player(self, player=None):
        last_player = player if player is not None else self.next_player()

        if self.game_round == 1:
            for i, player_cards in enumerate(self.players):
                if any(card.rank == "3" and card.suit == "S" for card in player_cards):
                    self.current_player = i
                    break
        elif {"BJB", "RJR"}.issubset({str(c) for c in self.players[last_player]}):
            # If last player has Black and Red Joker, then there is no card exchange and
            #   player who finished first, gets to start.
            self.current_player = self.finished_players[0]
        else:
            self.current_player = last_player

    # Completed additional game functions

    def take_turn(self, player_index, selected_cards):
        if self.game_status not in {"playing", "on_hold"}:
            return False

        if player_index != self.current_player:
            return False

        if not selected_cards and self.players[player_index]:  # Player passes their turn.
            self.current_player = self.next_player()

            if (self.current_player - 1) % len(self.players) == self.last_player_played and self.game_status == "on_hold":
                self.last_player_played = self.current_player

            return True
        elif self.is_valid_play(selected_cards):
            self.cards_in_play = selected_cards
            self.players[player_index] = [card for card in self.players[player_index] if card not in selected_cards]

            if not self.players[player_index]:
                self.finished_players.append(player_index)
                self.game_status = "on_hold"
            else:
                self.game_status = "playing"

            if self.is_game_over():
                # self.game_status = "card_exchange"
                self.start_new_round()

                # self.finished_players.append(player_index)
                # self.handle_card_exchange()
            else:
                self.last_player_played = self.current_player
                self.current_player = self.next_player()

            return True
        else:
            return False

    def _compare_color(self, selected_ranks):
        # Adjust rank values for A and 2 considering their position in the sequence
        def adjust_value(rank, in_sequence):
            if rank in ["A", "2"] and in_sequence:
                return RANKS.index(rank) - 13
            return RANKS.index(rank)

        # a = selected_ranks[0] == "3" and ((rank in {"A", "2"} and sesleted_ranks.count("2") == 2) or "K" not in selected_ranks)

        adjusted_values = [
            adjust_value(rank, selected_ranks[0] == "3" and ((rank in {"A", "2"} and selected_ranks.count(rank) == 2) or "K" not in selected_ranks)) for
            i, rank
            in enumerate(selected_ranks)]
        sorted_adjusted_values = sorted(adjusted_values)

        # Check consecutive sequence with updated rank values
        if all(sorted_adjusted_values[i] + 1 == sorted_adjusted_values[i + 1] for i in
               range(len(sorted_adjusted_values) - 1)):

            if not self.cards_in_play or self.last_player_played == self.current_player:  # Initial Color play
                return True

            play_values = sorted(
                [adjust_value(card.rank, "3" in {self.cards_in_play[1].rank, self.cards_in_play[2].rank}) for i, card in
                 enumerate(self.cards_in_play)])
            return max(play_values) < max(adjusted_values)  # New higher Color

    def is_valid_play(self, cards):
        # Check if the played card or set of cards is valid according to the rules
        if not cards:  # No cards selected
            return False

        selected_ranks = sorted([card.rank for card in cards], key=lambda rank: RANKS.index(rank))
        selected_values = [RANKS.index(rank) for rank in selected_ranks]

        # In the first game 3S should be thrown
        if self.game_round == 1 and "3S" not in {str(c) for c in cards} and len(self.cards_in_play) == 0:
            return False

        # Check for quadruples (Bembs)
        if len(selected_values) == 4 and len(set(selected_values)) == 1:
            if not self.cards_in_play:  # Initial Bemb play
                return True

            if len(selected_values) != self.cards_in_play:
                return True

            return RANKS.index(self.cards_in_play[0].rank) < RANKS.index(cards[0].rank)  # New higher Bemb

        if len(cards) != len(
                self.cards_in_play) and self.cards_in_play and self.last_player_played != self.current_player:
            return False

        # Check for consecutive cards (Color)
        if len(cards) >= 5:
            return self._compare_color(selected_ranks)

        if len(set(selected_values)) > 1:
            return False

        # Individual cards
        if self.cards_in_play and self.last_player_played != self.current_player:
            if selected_values[0] > RANKS.index(self.cards_in_play[0].rank):
                return True
        else:  # No cards in play yet
            return True

        return False

    def is_game_over(self):
        return len(self.finished_players) == len(self.players) - 1

    def handle_card_exchange(self):
        self.start_new_round()

        # Handle the card exchange between the winner and loser
        # Assumes players array has a length of 3 or 4 and players[0] is considered the winner

        winner_cards = self.players[0]
        loser_cards = self.players[-1]
        # Exchange one unnecessary card and one strongest card between winner and loser

        # Start a new round
        self.start_new_round()

    def start_new_round(self):
        last_player = self.next_player()

        self.game_round += 1
        self.players = [[] for _ in self.players]
        self.deck = self.create_deck()
        self.cards_in_play = []

        self.deal_cards()

        # Determine first player
        self.determine_first_player(player=last_player)

        if self.current_player == self.finished_players[0]:
            self.game_status = "playing"
        else:
            self.game_status = "card_exchange"

        # self.finished_players = []

    def next_player(self):

        self.current_player = (self.current_player + 1) % len(self.players)
        if self.players[self.current_player]:
            return self.current_player
        return self.next_player()

    def exchange_card(self, idx):
        if self.game_status != "exchange_card":
            return False

        for_first = self.players[self.current_player].pop(0)
        for_last = self.players[self.finished_players[0]].pop(int(idx))

        self.players[self.current_player].append(for_last)
        self.players[self.finished_players[0]].append(for_first)

        self.finished_players = []
        self.game_status = "playing"

        return True


# class CardGameSession(CardGame):
#     def __init__(self, number_of_players, session_id=None):
#         super().__init__(number_of_players)
#         self.session_id = f"session_{session_id}" or f"session_{random.randint(1000, 9999)}"
#
#     def save_game(self):
#         with open(f"./{self.session_id}.pickle", "wb") as f:
#             pickle.dump(self, f)
#
#     @classmethod
#     def load_game(cls, session_id):
#         if os.path.exists(f"./{session_id}.pickle"):
#             with open(f"./{session_id}.pickle", "rb") as f:
#                 return pickle.load(f)
#         return None
#
#
# if __name__ == "__main__":
#     c = CardGameSession(3, session_id="TEST")
#     c.initialize_game()
#
#     c.cards_in_play = [Card("S", "2")]
#
#     c.players[1] = [Card("C", "4")]
#     c.players[2] = [Card("C", "3")]
#
#     c.current_player = 2
#     c.last_player_played = 2
#
#     r = c.take_turn(player_index=2, selected_cards=[c.players[2][0]])
#     r = c.take_turn(player_index=0, selected_cards=[])
#     r = c.take_turn(player_index=1, selected_cards=[c.players[1][0]])
#
#     c.exchange_card(-1)
#
#     r = c.take_turn(player_index=0, selected_cards=[c.players[0][-1], c.players[0][-2]])
#
#     b = 0
# [16, 15, 14, 13, 11, 10, 9, 7, 6, 5, 3, 2, 1] - [2, 1, 16, 15, 14, 13] - [16, 14, 13, 12, 10, 9, 8, 6, 5, 4, 2, 1, 0]

"""
[16, 15, 14, 13, 11, 10, 9, 7, 6, 5, 3, 2, 1]
pass
[16, 14, 13, 12, 10, 9, 8, 6, 5, 4, 2, 1, 0]
pass
pass
[4]
[3]
pass
[2]
[2]
pass
[1]
[1]
pass
[0]
[0]
pass
pass
[0]
"""

"""
[16, 15, 14, 13, 11, 10, 9, 7, 6, 5, 3, 2, 1]
pass
[16, 14, 13, 12, 10, 9, 8, 6, 5, 4, 2, 1, 0]
pass
pass
[4]
[3]
[12]
[1]
[1]
[4]
pass
pass
[15, 14, 13, 11, 1]
pass
pass
[8, 9]
pass
pass
[8]
[0]
[0]
[0]
pass
pass
[6]
pass
pass


-----

[16, 15, 14, 13, 1, 2]
[17, 16, 14, 13, 12, 11]
"""
