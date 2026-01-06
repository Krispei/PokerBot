from .kuhn import KuhnPoker
from .nodes import Node
import matplotlib.pyplot as plt
import random
import time


class CFR_agent:

    def __init__(self, iterations, plot_strategy_sum, plot_exploitability):

        self.game = KuhnPoker()
        self.iterations = iterations
        self.plot_strategy_sum = plot_strategy_sum
        self.plot_exploitability = plot_exploitability
        
        self.infostate_map = dict()
        self.utility_map = dict()
        
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


    def train(self, iterations, exploitability_sample=50):
        
        print(f"Beginning CFR training with {self.iterations} iterations...")

        start = time.time()

        ten_percent = iterations

        for i in range(iterations):
            
            if i % ten_percent == 0:

                print(f"Training {(i // ten_percent)*10}% Done at iteration {i}")

            #Each game requires new cards shuffle
            self.cards = random.sample(self.game.cards, 2)
            
            #One traversal of the game tree
            self.CFR("", 1, 1)
            
            self.calculate_final_strategy()

            #calculate exploitability every 50 iterations
            if (self.plot_exploitability & (i % exploitability_sample == 0)):

                self.exploitability.append(self.calculate_exploitability())

        end = time.time()

        duration = round((end-start),2)

        print(f"Training complete in {duration} seconds!")
    
        if (self.plot_exploitability):

            self.plot_exploitability_func(self.exploitability)


    def CFR(self, history, pi_i, pi_i_c):
        
        #Visiting a terminal node
        if self.game.game_finished(history):
            
            payout = self.game.getPayouts(history, self.cards)

            if self.game.getPlayerToAct(history) == 0:
                return payout
            else:
                return -payout


        player_to_act = self.game.getPlayerToAct(history)
        #infostates are as following: player to act, player to act's cards, history
        infostate = str(player_to_act) + str(self.cards[player_to_act]) + history

        if infostate not in self.infostate_map:
            self.infostate_map[infostate] = Node(['p', 'b'])
            
        actions = self.game.getActions()

        #strategy normalization constant
        regret_sum_sum = 0

        #Calculate strategy normalization constant
        for i, action in enumerate(actions):
            #Calculate the normalization constant 
            #sum of R+(I,a)
            R_I_a = self.infostate_map[infostate].regret_sum[i]

            regret_sum_sum += max(R_I_a, 0)
             
        if regret_sum_sum > 0:

            #Calculate probability of taking action a
            for i, action in enumerate(actions):
                
                #calculate sig(I,a):
                R_I_a = self.infostate_map[infostate].regret_sum[i]

                R_plus_I_a = max(R_I_a, 0)

                self.infostate_map[infostate].strategy[i] = R_plus_I_a / regret_sum_sum

        else:

            for i, action in enumerate(actions):

                self.infostate_map[infostate].strategy[i] = 1 / len(actions)

        #calculate node value: essentially current expected value with current strategy
        #v_sig_I
        node_expected_value = 0

        for i, action in enumerate(actions):
            
            strategy_a = self.infostate_map[infostate].strategy[i]

            # We always swap the probabilities because the turn always changes in Kuhn Poker
            # Arg 1 (Next Self) = Current Opponent (pi_i_c)
            # Arg 2 (Next Opp)  = Current Self * Strategy (pi_i * strategy_a)
            
            value_a = -self.CFR(history + action, pi_i_c, pi_i * strategy_a)

            self.infostate_map[infostate].value[i] = value_a
            node_expected_value += strategy_a * value_a

        #now reassign the regrets
        for i, action in enumerate(actions):

            #compare v(I,a) against v_sig_i
            value_a = self.infostate_map[infostate].value[i]
            strategy_a = self.infostate_map[infostate].strategy[i]

            #r(I,a) = v(I,a) - v_sig_i
            instantaneous_regret_a = value_a - node_expected_value
            self.infostate_map[infostate].regret_sum[i] += pi_i_c * instantaneous_regret_a

            #update strategy sum
            #sig(a) = sig(a) + (pi_i * sig(a))
            self.infostate_map[infostate].strategy_sum[i] += strategy_a * pi_i

        return node_expected_value

    def calculate_final_strategy(self):

        for infostate in self.infostate_map:
            
            actions = self.infostate_map[infostate].actions

            #normalization constnat for final strategies
            final_strategy_sum = 0

            for i, action in enumerate(actions):

                final_strategy_sum += self.infostate_map[infostate].strategy_sum[i] 

            if final_strategy_sum > 0:

                for i, action in enumerate(actions):

                    strategy_sum_a = self.infostate_map[infostate].strategy_sum[i] 

                    self.infostate_map[infostate].final_strategy[i] = strategy_sum_a / final_strategy_sum
            
            else:

                for i, action in enumerate(actions):

                    self.infostate_map[infostate].final_strategy[i] = 1 / len(actions)

    #Recursive function to calculate expected utility
    def expected_utility(self, history, pi_i, pi_i_c):  
        
        player = self.game.getPlayerToAct(history=history)

        if self.game.game_finished(history):

            payout = self.game.getPayouts(history, self.cards)

            if player == 0:

                return payout
            
            else:

                return -payout

        #expected utility = P(b) * v(I,b) + P(p) * v(I,p)
        card = self.cards[player]
        infostate = str(player) + str(card) + history

        p_p = self.infostate_map[infostate].final_strategy[0]
        p_b = self.infostate_map[infostate].final_strategy[1]

        if player == 0:

            v_I_p = -self.expected_utility(history + 'p', pi_i * p_p, pi_i_c)
            v_I_b = -self.expected_utility(history + 'b', pi_i, pi_i_c * p_b)

        else: 

            v_I_p = -self.expected_utility(history + 'p', pi_i, pi_i_c * p_p)
            v_I_b = -self.expected_utility(history + 'b', pi_i * p_b, pi_i_c)
        
        expected_utility = (p_p * v_I_p) + (p_b * v_I_b)

        self.utility_map[infostate] = expected_utility

        return expected_utility

    def calculate_expected_utility(self):

        p1_expected_utility = 0
        
        for p1_card in self.game.cards:
            for p2_card in self.game.cards:
                
                if p2_card == p1_card: continue

                self.cards = [p1_card, p2_card]

                self.expected_utility("", 1, 1)

                p1_root = "0" + str(self.cards[0])

                p1_expected_utility += (1/6) * self.utility_map[p1_root]

        return p1_expected_utility

    def get_br_value(self, history, hero_card, opp, p_card):
        # 1. Terminal Node
        if self.game.game_finished(history=history):
            # Determine payoff for P0
            if opp == 0: # Hero is P1
                # Opponent is P0, Hero is P1. 
                card_combos = [[0, hero_card], [1, hero_card], [2, hero_card]]
            else: # Hero is P0
                card_combos = [[hero_card, 0], [hero_card, 1], [hero_card, 2]]

            payout_J = self.game.getPayouts(history, card_combos[0])
            payout_Q = self.game.getPayouts(history, card_combos[1])
            payout_K = self.game.getPayouts(history, card_combos[2])

            # Expected Value = Sum(Payoff * Probability)
            # Note: p_card should be normalized (sum to 1) for this to be an average
            expected_payout = (payout_J * p_card[0]) + (payout_Q * p_card[1]) + (payout_K * p_card[2])

            # If Hero is P0, we want positive P0 payout. 
            # If Hero is P1, we want negative P0 payout (assuming zero-sum).
            if opp == 1: # Hero is P0
                return expected_payout
            else:        # Hero is P1
                return -expected_payout

        # Get active player
        player = self.game.getPlayerToAct(history=history)
        action_map = ['p', 'b']

        # 2. Opponent Node (Chance Node from Hero's perspective)
        if player == opp:
            ev = 0
            for action in [0, 1]: # 0=p, 1=b
                norm = 0
                # Calculate probability of opponent taking this action
                for card in [0, 1, 2]:

                    infostate = str(player) + str(card) + history

                    p_a_given_card = self.infostate_map[infostate].final_strategy[action] if infostate in self.infostate_map else 0.5

                    norm += p_a_given_card * p_card[card]

                # Skip impossible branches to avoid Div/0
                if norm == 0:
                    continue

                # Update opponent beliefs (Bayes)
                new_card_probabilities = [0, 0, 0]
                for card in [0, 1, 2]:

                    infostate = str(player) + str(card) + history

                    p_a_given_card = self.infostate_map[infostate].final_strategy[action] if infostate in self.infostate_map else 0.5

                    new_card_probabilities[card] = (p_a_given_card * p_card[card]) / norm
                
                ev += norm * self.get_br_value(history + action_map[action], hero_card, opp, new_card_probabilities)
            return ev

        # 3. Hero Node (Optimization Node)
        else:
            ev_p = self.get_br_value(history + 'p', hero_card, opp, p_card)
            ev_b = self.get_br_value(history + 'b', hero_card, opp, p_card)
            return max(ev_p, ev_b)

    def calculate_exploitability(self):
        cards = [0, 1, 2]
        p1_ev_br = 0
        p2_ev_br = 0

        for card in cards:
            # PROBABILITY FIX: Use 0.5 so probabilities sum to 1.0
            # This represents that given Hero has Card X, Opponent has Y or Z with 50% prob each.
            p_cards = [0.5, 0.5, 0.5] 
            p_cards[card] = 0

            # We multiply by 1/3 because each Hero card occurs with 1/3 probability
            p1_ev_br += self.get_br_value('', card, 1, p_cards) * (1/3)
            p2_ev_br += self.get_br_value('', card, 0, p_cards) * (1/3)

        return (p1_ev_br + p2_ev_br)