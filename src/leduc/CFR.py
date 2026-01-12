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
            
        end = time.time()

        duration = round((end-start),2)

        print(f"Training complete in {duration} seconds!")
    

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

            return cf_value

        player_to_act = self.game.player_to_act(history)

        #infostate must contain the new card once the second round starts
        public_card = ""
        if len(self.cards) > 2: 

            public_card == self.cards[2]

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

    #Recursive function to calculate expected utility
    def expected_utility(self, history, pi_i, pi_i_c):  
        
        player = self.game.player_to_act(history=history)

        if self.game.terminal(history):

            payout = self.game.payout(history, self.cards)

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
