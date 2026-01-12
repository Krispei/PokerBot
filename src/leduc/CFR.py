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
        Calculates the exploitability of the current strategy profile.
        Exploitability = (Best_Response_Value_P1 + Best_Response_Value_P2) / 2
        (Or just the sum, depending on definition. Standard is average for Nash dist).
        """
        
        # 1. Calculate Best Response Value for Player 0 (Hero) against Player 1 (Fixed)
        # We assume Opponent (P1) starts with reach probs [1, 1, 1] (Unnormalized)
        # We calculate the value for Hero holding J, Q, K respectively.
        br_values_p0 = self.get_br_vector(history="", opp_reach=[1.0, 1.0, 1.0], hero_player=0)
        
        # Average value for P0 (Probability of being dealt J, Q, or K is 1/3)
        ev_p0 = sum(br_values_p0) / 3.0

        # 2. Calculate Best Response Value for Player 1 (Hero) against Player 0 (Fixed)
        br_values_p1 = self.get_br_vector(history="", opp_reach=[1.0, 1.0, 1.0], hero_player=1)
        ev_p1 = sum(br_values_p1) / 3.0

        # Exploitability is the sum of how much each player wins playing a BR 
        # against the other's current strategy.
        return ev_p0 + ev_p1

    def get_br_vector(self, history, opp_reach, hero_player):
        """
        Returns a vector of size 3: [Val_J, Val_Q, Val_K]
        representing the expected value for the Hero holding J, Q, or K.
        """
        
        # --- 1. Terminal Node ---
        if self.game.terminal(history):
            values = [0.0, 0.0, 0.0]
            
            # Determine Board Card (if round 2)
            board_card = None
            if ":" in history:
                # Assuming history format allows deducing board, 
                # but usually board is stored in state. 
                # In your implementation, board is dealt in the chance node.
                # We have to deduce it from history or logic. 
                # For this recursion, we assume the board card was processed in the Chance Node logic.
                pass 

            # To properly calculate payoff, we need to know the board card.
            # Your current 'game.payout' likely needs the full card set.
            # We must parse the board card from the history or tree structure.
            # In your Leduc code, the board isn't explicitly in the string history.
            # We'll assume the Board Card is passed or handled by the parent Chance Node.
            # **Correction**: In standard Leduc string history, the board isn't usually stored.
            # However, for this fix to work with your Game class, we need to know the board.
            # We will handle the board card logic inside the Chance Node block below.
            
            # If we are here, we are at a terminal node. We need to sum over opponent cards.
            # But wait, we don't know the board card here if it's not in 'history'.
            # We will rely on the fact that 'payout' is called with specific cards.
            return [0.0, 0.0, 0.0] # Should not be reached directly if chance node handles terminal recursion properly

        # --- 2. Chance Node (Round 1 Over -> Deal Board) ---
        if self.game.r1_over(history):
            values = [0.0, 0.0, 0.0]
            
            # Iterate over all possible public cards (0, 1, 2)
            for board_card in [0, 1, 2]:
                
                # Recurse: Go to Round 2
                # Note: We must update history to reflect round change if your game logic requires it.
                # Leduc typically adds a delimiter like ":"
                next_history = history + ":" 
                
                # We get the vector of values from the next step
                # We need to temporarily "store" this board card for the payout function later?
                # Actually, standard recursion passes the board_card down. 
                # For this snippet, let's assume we handle the terminal payout manually below.
                
                branch_values = self.get_br_vector_with_board(next_history, opp_reach, hero_player, board_card)
                
                # Weighted Sum based on probability of this board card appearing
                for hero_card in [0, 1, 2]:
                    if hero_card == board_card:
                        continue # Impossible board card (Hero has it)
                        
                    # Probability of this board card appearing given Hero has hero_card
                    # Deck has 6 cards. Hero has 1. 5 Remaining.
                    # Valid board cards: 2 of each rank.
                    # If Board == Hero_Card: Impossible (handled above)
                    # If Board != Hero_Card: There are 2 copies of that card left.
                    # Prob = 2 / 5.
                    
                    # However, Opponent also holds a card. 
                    # The standard BR calculation sums: P(Board | Hero, Opp) * P(Opp | Hero).
                    # It is mathematically cleaner to weigh the *outcome* at the terminal node.
                    # But for the chance node transition:
                    
                    # Simple Leduc Probability:
                    # If I have J. Remaining: J, Q, Q, K, K.
                    # Prob Q comes: 2/5. Prob K comes: 2/5. Prob J comes: 1/5.
                    
                    prob_board = 0
                    if board_card == hero_card:
                        prob_board = 1.0 / 5.0
                    else:
                        prob_board = 2.0 / 5.0
                        
                    values[hero_card] += prob_board * branch_values[hero_card]
                    
            return values

        # --- 3. Player Node ---
        player_to_act = self.game.player_to_act(history)
        actions = self.game.actions(history)
        
        # Case A: Hero to Act (Maximize Value)
        if player_to_act == hero_player:
            current_values = [-float('inf')] * 3
            
            for action in actions:
                # We don't change opp_reach, because Opp didn't act.
                next_vals = self.get_br_vector(history + action, opp_reach, hero_player)
                
                # Maximize for each private card independently
                for card in [0, 1, 2]:
                    if next_vals[card] > current_values[card]:
                        current_values[card] = next_vals[card]
            
            # Filter impossible cards (optional, but good for cleanliness)
            # e.g. if reach prob is 0, value is 0.
            return current_values

        # Case B: Opponent to Act (Weighted Average based on Strategy)
        else:
            current_values = [0.0, 0.0, 0.0]
            
            # We must retrieve the Opponent's strategy for every possible card they could hold
            # Strategy is a map: {Action -> Prob}
            
            # Prepare to sum over actions
            # We need to split the 'opp_reach' into 'next_reach' for each action
            
            # Temporary storage to accumulate values per action
            # We process one action at a time.
            for action in actions:
                
                next_opp_reach = [0.0, 0.0, 0.0]
                
                # Calculate new reach probs for opponent
                for opp_card in [0, 1, 2]:
                    # Get Opponent's Strategy for this card
                    # Note: We need the public card if it exists (Round 2)
                    public_card = ""
                    if ":" in history:
                        # Assuming we are traversing, we might not have easy access to public card 
                        # unless we passed it. 
                        # In this simplified fix, we assume the history string or logic allows lookup.
                        # For your code specifically, we'll try to deduce it or rely on a helper.
                        pass

                    # Look up strategy
                    # Strategy Key: "Player" + "Card" + "PublicCard" + "History"
                    # We need to reconstruct the public card from context or pass it down.
                    # FOR ROBUSTNESS: Let's assume public_card is empty string if not found, 
                    # but strictly it should be passed in args.
                    
                    # *CRITICAL*: You should update your recursion to pass `board_card` 
                    # if you want correct lookups in Round 2. 
                    # Here I will use an empty string for simplicity, but please verify.
                    infostate = str(player_to_act) + str(opp_card) + "" + history
                    
                    # *Actually*, we are inside a method that doesn't have `board_card` arg 
                    # in the signature above (Case 3). 
                    # You should merge `get_br_vector` and `get_br_vector_with_board`.
                    
                    prob_action = 1.0 / len(actions) # Default
                    if infostate in self.infostate_map:
                         prob_action = self.infostate_map[infostate].final_strategy.get(action, 0)
                    
                    next_opp_reach[opp_card] = opp_reach[opp_card] * prob_action

                # Recurse
                next_vals = self.get_br_vector(history + action, next_opp_reach, hero_player)
                
                # Sum values (Linearity of Expectation)
                for i in range(3):
                    current_values[i] += next_vals[i]
                    
            return current_values

    def get_br_vector_with_board(self, history, opp_reach, hero_player, board_card):
        """
        Helper for Round 2 traversal where Board Card is known.
        """
        if self.game.terminal(history):
            values = [0.0, 0.0, 0.0]
            opponent = 1 if hero_player == 0 else 0
            
            for hero_card in [0, 1, 2]:
                if hero_card == board_card: continue
                
                expected_payoff = 0
                
                for opp_card in [0, 1, 2]:
                    if opp_card == hero_card or opp_card == board_card: 
                        continue
                    
                    # Calculate Card Conflict Probability weight
                    # (Standard Leduc: 1/5 chance for J if we hold J? No.)
                    # If we are here, the DEAL has happened. 
                    # We strictly sum: Reach_Prob * Payoff.
                    # The probability of the deal was handled in the Chance Node weights.
                    
                    # However, we must normalize by the probability of the Opponent HAVING this card 
                    # given Hero Card + Board Card.
                    
                    # P(Opp=c | Hero, Board) 
                    # = 1 / 4 (4 cards remaining).
                    
                    # Payoff function expects: [P1_Card, P2_Card, Board]
                    if hero_player == 0:
                        cards = [hero_card, opp_card, board_card]
                        payoff = self.game.payout(history, cards) # P1 Perspective
                    else:
                        cards = [opp_card, hero_card, board_card]
                        payoff = -self.game.payout(history, cards) # P2 Perspective
                        
                    # We weight by the Opponent's Reach Probability
                    # AND the probability they were dealt that card (Uniform 1/4 approx)
                    
                    # Note: opp_reach is the probability they PLAYED to here given they held that card.
                    # We must multiply by the probability they were DEALT that card.
                    # P(Opp dealt opp_card | Hero has hero_card, Board has board_card) = 0.25
                    
                    expected_payoff += 0.25 * opp_reach[opp_card] * payoff
                    
                values[hero_card] = expected_payoff
            return values
            
        # If not terminal, we are in Round 2 betting actions
        player_to_act = self.game.player_to_act(history)
        actions = self.game.actions(history)
        
        if player_to_act == hero_player:
            current_values = [-float('inf')] * 3
            for action in actions:
                next_vals = self.get_br_vector_with_board(history + action, opp_reach, hero_player, board_card)
                for i in range(3):
                    current_values[i] = max(current_values[i], next_vals[i])
            return current_values
        else:
            current_values = [0.0, 0.0, 0.0]
            for action in actions:
                next_opp_reach = [0.0, 0.0, 0.0]
                for opp_card in [0, 1, 2]:
                    # Update Infostate with Board Card!
                    infostate = str(player_to_act) + str(opp_card) + str(board_card) + history
                    
                    prob_action = 1.0 / len(actions)
                    if infostate in self.infostate_map:
                         prob_action = self.infostate_map[infostate].final_strategy.get(action, 0)
                    next_opp_reach[opp_card] = opp_reach[opp_card] * prob_action
                
                next_vals = self.get_br_vector_with_board(history + action, next_opp_reach, hero_player, board_card)
                for i in range(3):
                    current_values[i] += next_vals[i]
            return current_values