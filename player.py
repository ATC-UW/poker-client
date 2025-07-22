
from typing import List
from bot import Bot
from type.poker_action import PokerAction
from type.round_state import RoundStateClient
from treys import Card, Evaluator, Deck
import random
import logging

# Use logging for cleaner, controllable debug output
logging.basicConfig(level=logging.INFO, format='[%(name)s] %(message)s')

class SimplePlayer(Bot):
    # --- Strategy Constants ---
    HIGH_EQUITY_THRESHOLD = 0.7
    VALUE_BET_THRESHOLD = 0.55
    SEMI_BLUFF_CHANCE = 0.4
    PREFLOP_RAISE_MULTIPLIER = 3
    VALUE_BET_SIZE_POT_FRACTION = 0.7
    BLUFF_BET_SIZE_POT_FRACTION = 0.5
    NUM_SIMULATIONS = 200

    # --- Full GTO Preflop Chart for Heads-Up (expanded, simplified for demo) ---
    GTO_PREFLOP_CHART = {
        # Pairs
        'AA': 'RAISE', 'KK': 'RAISE', 'QQ': 'RAISE', 'JJ': 'RAISE', 'TT': 'RAISE', '99': 'RAISE', '88': 'RAISE', '77': 'RAISE', '66': 'RAISE', '55': 'RAISE', '44': 'RAISE', '33': 'RAISE', '22': 'RAISE',
        # Suited Broadways
        'AKs': 'RAISE', 'AQs': 'RAISE', 'AJs': 'RAISE', 'ATs': 'RAISE', 'KQs': 'RAISE', 'KJs': 'RAISE', 'QJs': 'RAISE', 'JTs': 'RAISE', 'QTs': 'RAISE', 'J9s': 'RAISE', 'T9s': 'RAISE',
        # Offsuit Broadways
        'AKo': 'RAISE', 'AQo': 'RAISE', 'AJo': 'RAISE', 'KQo': 'RAISE', 'KJo': 'CALL', 'QJo': 'CALL',
        # Suited connectors
        '98s': 'RAISE', '87s': 'RAISE', '76s': 'RAISE', '65s': 'CALL', '54s': 'CALL',
        # Suited Aces
        'A9s': 'RAISE', 'A8s': 'RAISE', 'A7s': 'RAISE', 'A6s': 'RAISE', 'A5s': 'RAISE', 'A4s': 'RAISE', 'A3s': 'RAISE', 'A2s': 'RAISE',
        # Suited Kings
        'KTs': 'RAISE', 'K9s': 'CALL', 'K8s': 'CALL',
        # Suited Queens
        'Q9s': 'CALL', 'Q8s': 'CALL',
        # Suited Jacks
        'J8s': 'CALL', 'T8s': 'CALL',
        # Suited connectors (more)
        '64s': 'CALL', '53s': 'CALL', '43s': 'CALL',
        # Offsuit Aces
        'A9o': 'CALL', 'A8o': 'CALL', 'A7o': 'CALL', 'A6o': 'CALL', 'A5o': 'CALL', 'A4o': 'CALL', 'A3o': 'CALL', 'A2o': 'CALL',
        # Offsuit Kings
        'KTo': 'CALL', 'K9o': 'FOLD',
        # Offsuit Queens
        'QTo': 'FOLD', 'Q9o': 'FOLD',
        # Offsuit Jacks
        'JTo': 'FOLD', 'J9o': 'FOLD',
        # Offsuit connectors
        'T9o': 'FOLD', '98o': 'FOLD', '87o': 'FOLD',
        # Trash hands
        '72o': 'FOLD', '82o': 'FOLD', '32o': 'FOLD', '42o': 'FOLD', '52o': 'FOLD', '62o': 'FOLD', '92o': 'FOLD', 'T2o': 'FOLD', 'J2o': 'FOLD', 'Q2o': 'FOLD', 'K2o': 'FOLD', 'A2o': 'FOLD',
    }

    # --- 6-max GTO Preflop Charts (simplified for demo) ---
    GTO_PREFLOP_6MAX = {
        'UTG': {
            'AA': 'RAISE', 'KK': 'RAISE', 'QQ': 'RAISE', 'JJ': 'RAISE', 'TT': 'RAISE', 'AKs': 'RAISE', 'AQs': 'RAISE', 'AJs': 'RAISE', 'KQs': 'RAISE', 'AKo': 'RAISE', '99': 'CALL', 'ATs': 'CALL', 'KJs': 'CALL', 'QJs': 'CALL', 'AQo': 'CALL',
        },
        'MP': {
            'AA': 'RAISE', 'KK': 'RAISE', 'QQ': 'RAISE', 'JJ': 'RAISE', 'TT': 'RAISE', '99': 'RAISE', '88': 'RAISE', 'AKs': 'RAISE', 'AQs': 'RAISE', 'AJs': 'RAISE', 'KQs': 'RAISE', 'AKo': 'RAISE', 'AQo': 'RAISE', 'ATs': 'CALL', 'KJs': 'CALL', 'QJs': 'CALL',
        },
        'CO': {
            'AA': 'RAISE', 'KK': 'RAISE', 'QQ': 'RAISE', 'JJ': 'RAISE', 'TT': 'RAISE', '99': 'RAISE', '88': 'RAISE', '77': 'RAISE', 'AKs': 'RAISE', 'AQs': 'RAISE', 'AJs': 'RAISE', 'ATs': 'RAISE', 'KQs': 'RAISE', 'KJs': 'RAISE', 'QJs': 'RAISE', 'JTs': 'RAISE', 'AKo': 'RAISE', 'AQo': 'RAISE', 'AJo': 'CALL', 'KQo': 'CALL',
        },
        'BTN': {
            'AA': 'RAISE', 'KK': 'RAISE', 'QQ': 'RAISE', 'JJ': 'RAISE', 'TT': 'RAISE', '99': 'RAISE', '88': 'RAISE', '77': 'RAISE', '66': 'RAISE', '55': 'RAISE', '44': 'RAISE', '33': 'RAISE', '22': 'RAISE', 'AKs': 'RAISE', 'AQs': 'RAISE', 'AJs': 'RAISE', 'ATs': 'RAISE', 'KQs': 'RAISE', 'KJs': 'RAISE', 'QJs': 'RAISE', 'JTs': 'RAISE', 'T9s': 'RAISE', '98s': 'RAISE', '87s': 'RAISE', '76s': 'RAISE', '65s': 'RAISE', '54s': 'RAISE', 'AKo': 'RAISE', 'AQo': 'RAISE', 'AJo': 'RAISE', 'KQo': 'RAISE', 'KJo': 'CALL', 'QJo': 'CALL', 'JTo': 'CALL',
        },
        'SB': {
            'AA': 'RAISE', 'KK': 'RAISE', 'QQ': 'RAISE', 'JJ': 'RAISE', 'TT': 'RAISE', '99': 'RAISE', '88': 'RAISE', '77': 'RAISE', '66': 'RAISE', '55': 'RAISE', '44': 'RAISE', '33': 'RAISE', '22': 'RAISE', 'AKs': 'RAISE', 'AQs': 'RAISE', 'AJs': 'RAISE', 'ATs': 'RAISE', 'KQs': 'RAISE', 'KJs': 'RAISE', 'QJs': 'RAISE', 'JTs': 'RAISE', 'T9s': 'RAISE', '98s': 'RAISE', '87s': 'RAISE', '76s': 'RAISE', '65s': 'RAISE', '54s': 'RAISE', 'AKo': 'RAISE', 'AQo': 'RAISE', 'AJo': 'RAISE', 'KQo': 'RAISE', 'KJo': 'CALL', 'QJo': 'CALL', 'JTo': 'CALL',
        },
        'BB': {
            'AA': 'RAISE', 'KK': 'RAISE', 'QQ': 'RAISE', 'JJ': 'RAISE', 'TT': 'RAISE', '99': 'RAISE', '88': 'RAISE', '77': 'RAISE', '66': 'RAISE', '55': 'RAISE', '44': 'RAISE', '33': 'RAISE', '22': 'RAISE', 'AKs': 'RAISE', 'AQs': 'RAISE', 'AJs': 'RAISE', 'ATs': 'RAISE', 'KQs': 'RAISE', 'KJs': 'RAISE', 'QJs': 'RAISE', 'JTs': 'RAISE', 'T9s': 'RAISE', '98s': 'RAISE', '87s': 'RAISE', '76s': 'RAISE', '65s': 'RAISE', '54s': 'RAISE', 'AKo': 'RAISE', 'AQo': 'RAISE', 'AJo': 'RAISE', 'KQo': 'RAISE', 'KJo': 'CALL', 'QJo': 'CALL', 'JTo': 'CALL',
        },
    }

    def __init__(self):
        super().__init__()
        self.log = logging.getLogger(f"Bot-{getattr(self, 'id', 'NA')}")
        self.evaluator = Evaluator()
        self.player_hands = []

    def on_start(self, starting_chips: int, player_hands: List[str], blind_amount: int, big_blind_player_id: int, small_blind_player_id: int, all_players: List[int]):
        print("[DEBUG] SimplePlayer.on_start called")
        print("Player called on game start")
        print("Player hands: ", player_hands)
        print("Blind: ", blind_amount)
        print("Big blind player id: ", big_blind_player_id)
        print("Small blind player id: ", small_blind_player_id)
        print("All players in game: ", all_players)
        print("My id", self.id)
        self.player_hands = player_hands
        self.all_players = all_players
        self.dealer_id = small_blind_player_id  # In 6-max, dealer is usually small blind
        self.log.info(f"Game starting. My hand: {self.player_hands}")

    def on_round_start(self, round_state: RoundStateClient, remaining_chips: int):
        print("[DEBUG] SimplePlayer.on_round_start called")
        print("Player called on round start")
        print("Round state: ", round_state)
        # No additional logic for now

    def get_action(self, round_state: RoundStateClient, remaining_chips: int):
        state = self._parse_game_state(round_state, remaining_chips)
        if len(state["community"]) == 0:
            return self._get_preflop_action(state)
        else:
            return self._get_postflop_action(state)

    def _parse_game_state(self, round_state: RoundStateClient, remaining_chips: int) -> dict:
        my_bet = round_state.player_bets.get(str(getattr(self, 'id', 0)), 0)
        to_call = round_state.current_bet - my_bet
        pot_odds = to_call / (round_state.pot + to_call) if (round_state.pot + to_call) > 0 else 0
        min_raise = round_state.min_raise
        if min_raise <= 0 or min_raise > remaining_chips:
            min_raise = remaining_chips
        return {
            "hand": self.player_hands,
            "community": round_state.community_cards,
            "to_call": to_call,
            "pot": round_state.pot,
            "pot_odds": pot_odds,
            "stack": remaining_chips,
            "min_raise": min_raise,
            "can_raise": min_raise > 0 and remaining_chips > to_call,
        }

    def _get_position(self, all_players, my_id, dealer_id):
        n = len(all_players)
        # --- NEW: Handle heads-up (2 players) specifically ---
        if n == 2:
            # The dealer_id is the Small Blind/Button in heads-up
            return 'SB' if my_id == dealer_id else 'BB'
        # --- Existing logic for 3-6 players ---
        idx = all_players.index(my_id)
        btn_idx = all_players.index(dealer_id)
        rel = (idx - btn_idx) % n
        pos_map = {0: 'BTN', 1: 'SB', 2: 'BB', 3: 'UTG', 4: 'MP', 5: 'CO'}
        return pos_map.get(rel, 'BTN') # Fallback to BTN for safety

    def _get_preflop_action(self, state: dict):
        hand = state["hand"]
        if len(hand) < 2:
            print("[ERROR] Not enough cards in hand for preflop action.")
            return PokerAction.FOLD, 0
        r1, s1 = self._parse_card(hand[0])
        r2, s2 = self._parse_card(hand[1])
        v1 = self._rank_value(r1)
        v2 = self._rank_value(r2)
        # Build hand key for chart
        if v1 == v2:
            hand_key = r1 + r2  # e.g., 'AA', 'TT'
        else:
            ranks = sorted([r1, r2], key=lambda x: self._rank_value(x), reverse=True)
            suited = 's' if s1 == s2 else 'o'
            hand_key = ranks[0] + ranks[1] + suited  # e.g., 'AKs', 'QJo'
        # Position detection
        all_players = getattr(self, 'all_players', [0])
        dealer_id = getattr(self, 'dealer_id', all_players[0])
        my_id = getattr(self, 'id', 0)
        pos = self._get_position(all_players, my_id, dealer_id)
        chart = self.GTO_PREFLOP_6MAX.get(pos, self.GTO_PREFLOP_6MAX['BTN'])
        action = chart.get(hand_key, 'FOLD')
        print(f"[GTO 6MAX PREFLOP] Position: {pos}, Hand: {hand_key}, Action: {action}")
        to_call = state["to_call"]
        min_raise = state["min_raise"]
        stack = state["stack"]
        # Action randomization for borderline hands (as before)
        if action == 'CALL' and to_call > 0 and to_call < stack * 0.05 and stack > min_raise:
            if random.random() < 0.2:
                print(f"[RANDOMIZE] Borderline hand {hand_key}: randomly raising instead of calling.")
                return PokerAction.RAISE, min_raise
        if action == 'RAISE' and to_call > 0 and to_call < stack * 0.1:
            if random.random() < 0.15:
                print(f"[RANDOMIZE] Borderline hand {hand_key}: randomly calling instead of raising.")
                return PokerAction.CALL, to_call
        if action == 'RAISE' and stack > min_raise:
            return PokerAction.RAISE, min_raise
        elif action == 'CALL' and to_call > 0 and stack >= to_call:
            return PokerAction.CALL, to_call
        elif action == 'FOLD' and to_call > 0:
            return PokerAction.FOLD, 0
        if to_call == 0:
            return PokerAction.CHECK, 0
        return PokerAction.FOLD, 0

    def _calculate_equity(self, hand: List[str], board: List[str], num_opponents: int = 1) -> float:
        my_hand_treys = [Card.new(c) for c in hand]
        board_treys = [Card.new(c) for c in board]
        deck = Deck()
        for card in my_hand_treys + board_treys:
            deck.cards.remove(card)
        wins = 0
        ties = 0
        num_sims = self.NUM_SIMULATIONS
        for _ in range(num_sims):
            deck_copy = list(deck.cards)
            random.shuffle(deck_copy)
            num_remaining_board = 5 - len(board_treys)
            sim_board = board_treys + deck_copy[:num_remaining_board]
            card_offset = num_remaining_board
            opponent_hands = []
            for i in range(num_opponents):
                start = card_offset + (i * 2)
                end = start + 2
                opponent_hands.append(deck_copy[start:end])
            my_score = self.evaluator.evaluate(sim_board, my_hand_treys)
            best_score = my_score
            num_best = 1
            for opp_hand in opponent_hands:
                opp_score = self.evaluator.evaluate(sim_board, opp_hand)
                if opp_score < best_score:
                    best_score = opp_score
                    num_best = 1
                elif opp_score == best_score:
                    num_best += 1
            if best_score == my_score:
                if num_best == 1:
                    wins += 1
                else:
                    ties += 1 / num_best  # split pot
        return (wins + ties) / num_sims if num_sims > 0 else 0

    def _is_strong_draw(self, hand: List[str], board: List[str]) -> bool:
        all_cards = hand + board
        suits = [self._parse_card(c)[1] for c in all_cards]
        ranks = sorted(list(set(self._rank_value(self._parse_card(c)[0]) for c in all_cards)))
        for s in "shdc":
            if suits.count(s) == 4:
                return True
        if len(ranks) >= 4:
            for i in range(len(ranks) - 3):
                if ranks[i+3] - ranks[i] == 3 and len(set(ranks[i:i+4])) == 4:
                    return True
        return False

    def _parse_card(self, card: str):
        return card[:-1], card[-1]

    def _rank_value(self, rank: str) -> int:
        if rank.isdigit():
            return int(rank)
        return {'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}[rank]

    def _clamp_bet(self, amount: float, state: dict) -> int:
        amount = int(amount)
        min_bet = state["min_raise"]
        max_bet = state["stack"]
        return max(min_bet, min(amount, max_bet))

    def _get_postflop_action(self, state: dict):
        hand = state["hand"]
        board = state["community"]
        # --- Multiway adjustment: tighten up if 3+ players ---
        n_players = len([p for p, amt in state.get('player_bets', {}).items() if amt is not None and amt >= 0])
        equity_buffer = 0.0
        if n_players >= 3:
            equity_buffer = 0.08  # require 8% more equity to bet/call
        # --- Use correct number of opponents for equity calculation ---
        num_opponents = max(1, n_players - 1)
        equity = self._calculate_equity(hand, board, num_opponents=num_opponents)
        pot = state["pot"]
        to_call = state["to_call"]
        stack = state["stack"]
        min_raise = state["min_raise"]
        can_raise = state["can_raise"]
        pot_odds = state["pot_odds"]
        # --- Tier 1: Randomize Bet Sizing ---
        value_bet_multiplier = random.uniform(0.6, 0.9)
        bluff_bet_multiplier = random.uniform(0.4, 0.6)
        value_bet = int(pot * value_bet_multiplier)
        bluff_bet = int(pot * bluff_bet_multiplier)
        # --- Tier 1: Range Balancing ---
        if equity > 0.9 and random.random() < 0.2:
            print("[RANGE BALANCE] Slow-playing monster hand (trap check)")
            return PokerAction.CHECK, 0
        if equity < 0.2 and can_raise and random.random() < 0.1:
            print(f"[RANGE BALANCE] Pure bluff with air! Bluff bet: {bluff_bet}")
            return PokerAction.RAISE, self._clamp_bet(bluff_bet, state)
        equity_gap = abs(equity - (self.VALUE_BET_THRESHOLD + equity_buffer))
        if can_raise and 0 < equity_gap < 0.05:
            if random.random() < 0.3:
                if equity > self.VALUE_BET_THRESHOLD + equity_buffer:
                    print(f"[RANDOMIZE] Borderline value bet: randomly checking instead of betting (equity={equity:.2f})")
                    return PokerAction.CHECK, 0
                else:
                    print(f"[RANDOMIZE] Borderline non-value: randomly betting instead of checking (equity={equity:.2f})")
                    return PokerAction.RAISE, self._clamp_bet(bluff_bet, state)
        if equity > self.VALUE_BET_THRESHOLD + equity_buffer and can_raise:
            print(f"[BET SIZING] Value betting with randomized size: {value_bet}")
            return PokerAction.RAISE, self._clamp_bet(value_bet, state)
        if self._is_strong_draw(hand, board) and can_raise and random.random() < self.SEMI_BLUFF_CHANCE:
            print(f"[BET SIZING] Semi-bluffing with draw, randomized size: {bluff_bet}")
            return PokerAction.RAISE, self._clamp_bet(bluff_bet, state)
        if to_call > 0 and equity > pot_odds + equity_buffer:
            print(f"[POSTFLOP] Calling with equity {equity:.2f} > pot odds {pot_odds:.2f} (buffer={equity_buffer:.2f})")
            return PokerAction.CALL, to_call
        if to_call == 0:
            print("[POSTFLOP] Checking as default action.")
            return PokerAction.CHECK, 0
        print("[POSTFLOP] Folding as default action.")
        return PokerAction.FOLD, 0

    def on_end_round(self, round_state: RoundStateClient, remaining_chips: int):
        print("[DEBUG] SimplePlayer.on_end_round called")
        print("Player called on end round")
        # No additional logic for now

    def on_end_game(self, round_state: RoundStateClient, player_score: float, all_scores: dict, active_players_hands: dict):
        print("[DEBUG] SimplePlayer.on_end_game called")
        print("Player called on end game, with player score: ", player_score)
        print("All final scores: ", all_scores)
        print("Active players hands: ", active_players_hands)
        # No additional logic for now