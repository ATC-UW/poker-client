import eval7
from bot import Bot
from type.poker_action import PokerAction
from type.round_state import RoundStateClient

class SimplePlayer(Bot):
    def __init__(self):
        super().__init__()

    def on_start(self, starting_chips: int):
        // Save initial count
        self.initialCount = starting_chips

        // Track profit
        self.total_profit = 0

        // Rounds player
        self.rounds_played = 0

        // history
        self.handHistory = []

        print("Starting with {self.initialCoutn} chips")

    def on_round_start(self, round_state: RoundStateClient, remaining_chips: int):
        print("Player called on round start")

    def get_action(self, round_state: RoundStateClient, remaining_chips: int):
        """ Returns the action for the player. """
        print("Player called get action")

        raised = False
        for player_action in round_state.player_actions.values():
            if player_action == "Raise":
                raised = True
                break

        if not raised and round_state.round_num == 1:
            return PokerAction.RAISE, 100
        
        if round_state.current_bet == 0:
            return PokerAction.CHECK, 0
        
        amount_to_call = round_state.current_bet - round_state.player_bets[str(self.id)]
        return PokerAction.CALL, amount_to_call

    def on_end_round(self, round_state: RoundStateClient, remaining_chips: int):
        """ Called at the end of the round. """
        print("Player called on end round")

    def on_end_game(self, round_state: RoundStateClient, score: float):
        print("Player called on end game, with score: ", score)
