from .kuhn import KuhnPoker
from .nodes import Node
import matplotlib.pyplot as plt
import random
import time


class CFR_agent:

    def __init__(self, iterations, plot_strategy_sum):

        self.game = KuhnPoker()
        self.iterations = iterations
        self.plot_strategy_sum = plot_strategy_sum
        self.infostate_map = dict()
        self.cards = []
        self.utility_map = dict()

    def plot(self, data):

        plt.plot(data[0], label="Jack pass probability")
        plt.plot(data[1], label="Jack bet probability")    
        plt.legend()
        plt.xlabel("Iterations")
        plt.ylabel("Probability")
        plt.title("Strategy of P2 Jack after a P1 pass over iterations")
        plt.show()

    def train(self):
        
        print(f"Beginning CFR training with {self.iterations} iterations...")

        start = time.time()

        ten_percent = self.iterations//10
        
        p2_J_root = [[],[]] #p, b

        for i in range(self.iterations):
            
            if i % ten_percent == 0:

                print(f"Training {(i // ten_percent)*10}% Done at iteration {i}")

            self.cards = random.sample(self.game.cards, 2)
            
            self.CFR("", 1, 1)
            
            if (self.plot_strategy_sum):

                self.calculate_final_strategy()

                p2_J_p = self.infostate_map["10p"].final_strategy[0] if "10p" in self.infostate_map else 0.5
                p2_J_b = self.infostate_map["10p"].final_strategy[1] if "10p" in self.infostate_map else 0.5

                p2_J_root[0].append(p2_J_p)
                p2_J_root[1].append(p2_J_b)

        end = time.time()

        duration = round((end-start),2)

        print(f"Training complete in {duration} seconds!")
        
        if (self.plot_strategy_sum):

            self.plot(p2_J_root)

    def CFR(self, history, pi_i, pi_i_c):

        if self.game.isGameFinished(history):
            
            if self.game.getPlayerToAct(history) == 0:

                return self.game.getPayouts(history, self.cards)
        
            else:

                return -self.game.getPayouts(history, self.cards)


        player_to_act = self.game.getPlayerToAct(history)


        infostate = str(player_to_act) + str(self.cards[player_to_act]) + history
        # example, player 1 with a king to act after checking and player 2 betting:
        # 02pb

        if infostate not in self.infostate_map:

            self.infostate_map[infostate] = Node(['p', 'b'])


        actions = self.game.getActions()


        regret_sum_sum = 0
        #strategy normalization constant

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

            if player_to_act == 0: 

                value_a = -self.CFR(history + action, pi_i * strategy_a, pi_i_c)

            else:

                value_a = -self.CFR(history + action, pi_i, pi_i_c * strategy_a)


            self.infostate_map[infostate].value[i] = value_a

            node_expected_value += strategy_a * value_a 

        #now reassign the regrets
        for i, action in enumerate(actions):

            #compare v(I,a) against v_sig_i

            value_a = self.infostate_map[infostate].value[i]
            strategy_a = self.infostate_map[infostate].strategy[i]


            #r(I,a) = v(I,a) - v_sig_i
            instantaneous_regret_a = value_a - node_expected_value

            #if v(I,a) > v_sig_i, we have positive regret and we regret not chosing a more often

            #update cumulative regret (regretsum)
            #R(a) = R(a) + (pi_i_c * r(I,a))

            pi_c = pi_i_c if player_to_act == 0 else pi_i

            self.infostate_map[infostate].regret_sum[i] += pi_c * instantaneous_regret_a

            #update strategy sum
            #sig(a) = sig(a) + (pi_i * sig(a))

            pi = pi_i if player_to_act == 0 else pi_i_c

            self.infostate_map[infostate].strategy_sum[i] += strategy_a * pi

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
        
        if self.game.isGameFinished(history):

            sign = 1 if self.game.getPlayerToAct(history) == 0 else -1
        
            return sign * self.game.getPayouts(history, self.cards) 

        #expected utility = P(b) * v(I,b) + P(p) * v(I,p)

        player = self.game.getPlayerToAct(history)

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

        all_root_states = [[0,1], [0,2],
                           [1,0], [1,2],
                           [2,0], [2,1]]

        p1_expected_utility = 0
        p2_expected_utility = 0
        
        for root in all_root_states:

            self.cards = root

            self.expected_utility("", 1, 1)

            p1_root = "0" + str(root[0])
            p2_root = "1" + str(root[1])

            p1_expected_utility += (1/len(all_root_states)) * self.utility_map[p1_root]
            #p2_expected_utility += (1/len(all_root_states)) * self.expected_utility[p2_root]

        return p1_expected_utility
        


        
        
