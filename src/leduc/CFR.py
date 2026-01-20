from .leduc import leduc
from .nodes import Node
import matplotlib.pyplot as plt
import random
import time


class CFR_agent:

    def __init__(self, iterations, plot_strategy_sum, plot_exploitability):

        self.game = leduc()
        self.iterations = iterations
        self.plot_strategy_sum = plot_strategy_sum
        self.plot_exploitability = plot_exploitability
        
        self.infostate_map = dict()
        self.utility_map = dict()
        
        self.deck = [0,0,1,1,2,2]
        self.cards = []
        self.exploitability = []

    def plot_exploitability_func(self, data):
        '''
        Helper function to plot exploitabilility of the current final strategy over iterations.
    
        :param self:
        :param data: exploitability calculated every 50 iterations
        '''

        step = 50
        x = [i * step for i in range(len(data))]

        plt.plot(x, data)
        plt.xlabel("Iterations")
        plt.ylabel("Exploitability")
        plt.title("Exploitability over iterations")
        plt.show()


    def train(self):
        
        print(f"Beginning CFR training with {self.iterations} iterations...")

        start = time.time()

        ten_percent = self.iterations // 10

        for i in range(self.iterations):
            
            if i % ten_percent == 0:

                print(f"Training {(i // ten_percent)*10}% Done at iteration {i}")

            #Each game requires new cards shuffle
            random.shuffle(self.deck)
            
            self.cards = [self.deck[0], self.deck[1]]

            #One traversal of the game tree
            self.CFR("", 1, 1, 1)
            
            if i % 100 == 0:

                self.calculate_final_strategy()
                self.exploitability.append(self.calculate_exploitability())

        end = time.time()

        duration = round((end-start),2)

        print(f"Training complete in {duration} seconds!")

        self.plot_exploitability_func(self.exploitability)


    def CFR(self, history, pi_i, pi_i_c, pi_c):
        
        #Visiting a terminal node
        if self.game.terminal(history):
            
            payout = self.game.payout(history, self.cards)

            if self.game.player_to_act(history) == 0:
                return payout
            else:
                return -payout

        #Visiting a chance node
        if self.game.r1_over(history):
            
            cf_value = 0

            for i in range(2, len(self.deck)):
                
                self.cards.append(self.deck[i])
                cf_value += (1/4) * self.CFR(history=history + ":", pi_i=pi_i, pi_i_c=pi_i_c, pi_c= pi_c*(1/4))
                self.cards.pop()

            return cf_value

        player_to_act = self.game.player_to_act(history)

        #infostate must contain the new card once the second round starts
        public_card = ""
        if len(self.cards) > 2: 

            public_card = self.cards[2]

        infostate = str(player_to_act) + str(self.cards[player_to_act]) + str(public_card) + history

        if infostate not in self.infostate_map:
            self.infostate_map[infostate] = Node(self.game.actions(history=history))
            
        actions = self.game.actions(history=history)

        #strategy normalization constant
        regret_sum_sum = 0

        #Calculate strategy normalization constant
        for i, action in enumerate(actions):
            #Calculate the normalization constant 
            #sum of R+(I,a)
            R_I_a = self.infostate_map[infostate].regret_sum.get(action, 0)

            regret_sum_sum += max(R_I_a, 0)
             
        if regret_sum_sum > 0:

            #Calculate probability of taking action a
            for i, action in enumerate(actions):
                
                #calculate sig(I,a):
                R_I_a = self.infostate_map[infostate].regret_sum.get(action,0)

                R_plus_I_a = max(R_I_a, 0)

                self.infostate_map[infostate].strategy[action] = R_plus_I_a / regret_sum_sum

        else:

            for i, action in enumerate(actions):

                self.infostate_map[infostate].strategy[action] = 1 / len(actions)

        #calculate node value: essentially current expected value with current strategy
        #v_sig_I
        node_expected_value = 0

        for i, action in enumerate(actions):
            
            strategy_a = self.infostate_map[infostate].strategy.get(action, 0)

            # We always swap the probabilities because the turn always changes in Kuhn Poker
            # Arg 1 (Next Self) = Current Opponent (pi_i_c)
            # Arg 2 (Next Opp)  = Current Self * Strategy (pi_i * strategy_a)
            
            value_a = -self.CFR(history + action, pi_i_c, pi_i * strategy_a, pi_c)

            self.infostate_map[infostate].value[action] = value_a
            node_expected_value += strategy_a * value_a

        #now reassign the regrets
        for i, action in enumerate(actions):

            #compare v(I,a) against v_sig_i
            value_a = self.infostate_map[infostate].value.get(action, 0)
            strategy_a = self.infostate_map[infostate].strategy.get(action,0)

            #r(I,a) = v(I,a) - v_sig_i
            instantaneous_regret_a = value_a - node_expected_value
            self.infostate_map[infostate].regret_sum[action] = self.infostate_map[infostate].regret_sum.get(action,0) +  pi_c * pi_i_c * instantaneous_regret_a

            #update strategy sum
            #sig(a) = sig(a) + (pi_i * sig(a))
            self.infostate_map[infostate].strategy_sum[action] = self.infostate_map[infostate].strategy_sum.get(action,0) + strategy_a * pi_i

        return node_expected_value

    def calculate_final_strategy(self):

        for infostate in self.infostate_map:
            
            actions = self.infostate_map[infostate].actions

            #normalization constnat for final strategies
            final_strategy_sum = 0

            for i, action in enumerate(actions):

                final_strategy_sum += self.infostate_map[infostate].strategy_sum.get(action, 0)

            if final_strategy_sum > 0:

                for i, action in enumerate(actions):

                    strategy_sum_a = self.infostate_map[infostate].strategy_sum.get(action,0)

                    self.infostate_map[infostate].final_strategy[action] = strategy_sum_a / final_strategy_sum
            
            else:

                for i, action in enumerate(actions):

                    self.infostate_map[infostate].final_strategy[action] = 1 / len(actions)
    
    def calculate_exploitability(self):
        """
        Calculates the exploitability of the final strategy by computing the 
        best response value for each player position.
        """
        
        # 1. Calculate Best Response Value for Player 0 (when P1 plays fixed strategy)
        # We iterate over all possible initial deals to get the exact Game Value.
        br_value_p0 = 0
        br_value_p1 = 0
        
        # We need a fresh sorted deck to iterate all permutations
        full_deck = [0, 0, 1, 1, 2, 2]
        import itertools
        
        # Total permutations of 2 cards from 6
        n_deals = 30 # 6 * 5
        
        # --- Calculate BR for Player 0 (P1 is fixed to final_strategy) ---
        for card_p0, card_p1 in itertools.permutations(full_deck, 2):
            # Form the initial cards state. 
            # Note: We pass the specific deck minus these cards to the helper
            remaining_deck = list(full_deck)
            remaining_deck.remove(card_p0)
            remaining_deck.remove(card_p1)
            
            # Recursively calculate value. History is empty.
            # br_player is 0. 
            val = self._get_best_response_value(
                history="", 
                cards=[card_p0, card_p1], 
                remaining_deck=remaining_deck, 
                br_player=0
            )
            br_value_p0 += val
            
        br_value_p0 /= n_deals

        # --- Calculate BR for Player 1 (P0 is fixed to final_strategy) ---
        for card_p0, card_p1 in itertools.permutations(full_deck, 2):
            remaining_deck = list(full_deck)
            remaining_deck.remove(card_p0)
            remaining_deck.remove(card_p1)
            
            # br_player is 1.
            val = self._get_best_response_value(
                history="", 
                cards=[card_p0, card_p1], 
                remaining_deck=remaining_deck, 
                br_player=1
            )
            br_value_p1 += val

        br_value_p1 /= n_deals
        
        # Exploitability is the average of how much the BR wins in each position.
        # Since it's zero sum:
        # If P0 is fixed, P1 (BR) wins X. (br_value_p1)
        # If P1 is fixed, P0 (BR) wins Y. (br_value_p0)
        # Total Exploitability = X + Y. Average = (X+Y)/2
        return (br_value_p0 + br_value_p1) / 2

    def _get_best_response_value(self, history, cards, remaining_deck, br_player):
        """
        Helper to traverse the game tree for Best Response calculation.
        br_player: The player who is playing optimally (Best Response).
        The other player plays according to self.infostate_map['final_strategy'].
        """
        
        # 1. Terminal Node
        if self.game.terminal(history):
            payout = self.game.payout(history, cards)
            # Payout is usually for Player 0.
            # If we want value for br_player:
            if br_player == 0:
                return payout
            else:
                return -payout

        # 2. Chance Node (End of Round 1)
        if self.game.r1_over(history):
            expected_value = 0
            # Chance node logic: average over all remaining cards
            # In BR calculation, we are exact, so we iterate all remaining cards
            # distinct values only? No, standard probability weight implies iterating list.
            count = 0
            for card in remaining_deck:
                # Add public card to cards list temporarily
                new_cards = cards + [card]
                # Pass a copy of deck without this card (optional optimization, 
                # but technically round 2 has no more dealing so list doesn't matter much)
                
                # Recursive call
                # Note: history changes usually by appending ":" or handling state transition
                # Assuming ":" as per your CFR code
                expected_value += self._get_best_response_value(
                    history + ":", 
                    new_cards, 
                    remaining_deck, # Deck state doesn't change further in Leduc
                    br_player
                )
                count += 1
            
            return expected_value / count

        # 3. Decision Node
        player_to_act = self.game.player_to_act(history)
        actions = self.game.actions(history)
        
        # Determine Infostate Key
        public_card = ""
        if len(cards) > 2:
            public_card = cards[2]
        
        # Key must match the CFR training key generation
        infostate = str(player_to_act) + str(cards[player_to_act]) + str(public_card) + history

        # CASE A: It is the Best Responder's turn. They maximize EV.
        if player_to_act == br_player:
            best_value = -float('inf')
            for action in actions:
                val = self._get_best_response_value(history + action, cards, remaining_deck, br_player)
                if val > best_value:
                    best_value = val
            return best_value

        # CASE B: It is the Opponent's turn. They play Fixed Strategy.
        else:
            node_value = 0
            
            # Retrieve strategy from map. If missing, default to uniform (or random).
            if infostate in self.infostate_map:
                strategy = self.infostate_map[infostate].final_strategy
            else:
                # Should not happen often if training covered tree, but safe fallback
                strategy = {a: 1.0/len(actions) for a in actions}
            
            for action in actions:
                prob = strategy.get(action, 0)
                if prob > 0:
                    val = self._get_best_response_value(history + action, cards, remaining_deck, br_player)
                    node_value += prob * val
            
            return node_value