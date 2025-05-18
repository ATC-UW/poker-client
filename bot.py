from abc import ABC, abstractmethod

from type.round_state import RoundStateClient


class Bot(ABC):
    def __init__(self):
        """ Initializes the player. """
        self.id = None
        pass

    def set_id(self, player_id: int):
        """ Sets the player ID. """
        self.id = player_id

    @abstractmethod
    def on_start(self, starting_chips: int):
        """ Called when the game starts. """
        self.

    @abstractmethod
    def on_round_start(self, round_state: RoundStateClient, remaining_chips: int):
        """ Called at the start of each round. """
        pass

    @abstractmethod
    def get_action(self, round_state: RoundStateClient, remaining_chips: int):
        """ Called when it is the player's turn to act. """
        pass

    @abstractmethod
    def on_end_round(self, round_state: RoundStateClient, remaining_chips: int):
        """ Called at the end of each round. """
        pass

    @abstractmethod
    def on_end_game(self, round_state: RoundStateClient, score: float):
        """ Called at the end of the game. """
        pass