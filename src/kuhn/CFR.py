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
        self.p2_J_root_strategy = [[],[]]


    def plot_p2_strategy(self, data):

        plt.plot(data[0], label="Jack pass probability")
        plt.plot(data[1], label="Jack bet probability")    
        plt.legend()
        plt.xlabel("Iterations")
        plt.ylabel("Probability")
        plt.title("Strategy of P2 Jack after a P1 pass over iterations")
        plt.show()

    def plot_exploitability_func(self, data):

        plt.plot(data, label="Exploitability")
        plt.xlabel("Iterations")
        plt.ylabel("Exploitability")
        plt.title("Exploitability over iterations")
        plt.show()


    def train(self):
        
        print(f"Beginning CFR training with {self.iterations} iterations...")

        start = time.time()

        ten_percent = self.iterations//10

        for i in range(self.iterations):
            
            if i % ten_percent == 0:

                print(f"Training {(i // ten_percent)*10}% Done at iteration {i}")

            #Each game requires new cards shuffle
            self.cards = random.sample(self.game.cards, 2)
            
            #One traversal of the game tree
            self.CFR("", 1, 1)
            
            self.calculate_final_strategy()

            if (self.plot_strategy_sum):
                
                #Calculate the probability of a player 2 pass with a jack after player 1 passes, and the probability of a plyer 2 bet (as a bluff) after a 
                #player 1 pass
                p2_J_p = self.infostate_map["10p"].final_strategy[0] if "10p" in self.infostate_map else 0.5
                p2_J_b = self.infostate_map["10p"].final_strategy[1] if "10p" in self.infostate_map else 0.5

                self.p2_J_root_strategy[0].append(p2_J_p)
                self.p2_J_root_strategy[1].append(p2_J_b)
            
            #calculate exploitability
            if (self.plot_exploitability & (i % 100 == 0)):

                self.exploitability.append(self.calculate_exploitability())

        end = time.time()

        duration = round((end-start),2)

        print(f"Training complete in {duration} seconds!")
        
        if (self.plot_strategy_sum):

            self.plot_p2_strategy(self.p2_J_root_strategy)

        if (self.plot_exploitability):

            self.plot_exploitability_func(self.exploitability)

    def CFR(self, history, pi_i, pi_i_c):

        #Visiting a terminal node
        if self.game.isGameFinished(history):
            
            payout = self.game.getPayouts(history, self.cards)

            if self.game.getPlayerToAct(history) == 0:

                return payout
        
            else:

                return -payout


        player_to_act = self.game.getPlayerToAct(history)
        infostate = str(player_to_act) + str(self.cards[player_to_act]) + history
        # example, player 1 with a king to act after checking and player 2 betting:
        # 02pb

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
    
    def get_br_value(self, history, player_cards, prob_opp_cards):
        """
        Recursive helper to calculate the value of the Best Response.
        
        Args:
            history: string game history
            player_cards: tuple (p0_card, p1_card)
                          Note: One is the fixed 'exploiter' card, 
                          the other is a placeholder or used for payout index.
            prob_opp_cards: list of probabilities of the opponent holding cards 0, 1, 2.
                            (The probability for the exploiter's own card will be 0)
        """
         
        # 1. Terminal Node
        if self.game.isGameFinished(history):
            # Calculate Expected Payoff over the distribution of opponent cards
            expected_payoff = 0
            exploiter = 0 if self.game.getPlayerToAct(history) == 1 else 1 # Previous player acted
            exploiter_card = player_cards[exploiter]
            
            # Iterate over all possible opponent cards
            for opp_card in range(3):
                if prob_opp_cards[opp_card] > 0:
                    # Construct the specific deal to get the payout
                    current_cards = [0, 0]
                    current_cards[exploiter] = exploiter_card
                    current_cards[1-exploiter] = opp_card
                    
                    payout = self.game.getPayouts(history, current_cards)
                    
                    # Payouts are always defined for P0. 
                    # If exploiter is P1, we flip sign.
                    if exploiter == 1:
                        payout = -payout
                        
                    expected_payoff += prob_opp_cards[opp_card] * payout
            
            return expected_payoff

        player_to_act = self.game.getPlayerToAct(history)
        
        # 2. Chance Node (Strategy Node for the Fixed Opponent)
        # We split the execution paths and update opponent card probabilities
        if player_to_act != player_cards[3]: # player_cards[3] stores who is the Exploiter
            
            value_accum = 0
            
            # We need to recurse on both actions (p and b), but the probability 
            # of the opponent being here depends on their card and strategy.
            
            # Prepare probability distributions for next states
            prob_pass = [0.0] * 3
            prob_bet = [0.0] * 3
            
            for card in range(3):
                if prob_opp_cards[card] > 0:
                    # Retrieve Fixed Opponent's Strategy for this card + history
                    infostate = str(player_to_act) + str(card) + history
                    if infostate in self.infostate_map:
                        strat = self.infostate_map[infostate].final_strategy
                    else:
                        strat = [0.5, 0.5] # Default uniform
                    
                    prob_pass[card] = prob_opp_cards[card] * strat[0]
                    prob_bet[card]  = prob_opp_cards[card] * strat[1]
            
            # Recurse and sum up the weighted values
            # Note: We don't multiply by strategy here because the probability 
            # mass was pushed into the prob_pass/prob_bet arrays.
            value_accum += self.get_br_value(history + 'p', player_cards, prob_pass)
            value_accum += self.get_br_value(history + 'b', player_cards, prob_bet)
            
            return value_accum

        # 3. Decision Node (Choice for the Best Responder)
        else:
            # The Exploiter sees their own card (player_cards[exploiter]) and history.
            # They choose the action that maximizes EV against the current prob_opp_cards.
            
            # We pass the current probability distribution down unchanged
            val_pass = self.get_br_value(history + 'p', player_cards, prob_opp_cards)
            val_bet  = self.get_br_value(history + 'b', player_cards, prob_opp_cards)
            
            return max(val_pass, val_bet)


    def calculate_exploitability(self):
        # Calculate Best Response Value for P0 (Exploiting Fixed P1)
        br_val_p0 = 0
        for card in range(3):
            # P0 has 'card', P1 has others. 
            # We pass a tuple where index 3 indicates WHO is the exploiter (0)
            # Tuple: (P0_Card, P1_Placeholder, Unused, Exploiter_ID)
            prob_opp = [1.0 if c != card else 0.0 for c in range(3)]
            br_val_p0 += self.get_br_value("", (card, -1, -1, 0), prob_opp)

        # Calculate Best Response Value for P1 (Exploiting Fixed P0)
        br_val_p1 = 0
        for card in range(3):
            prob_opp = [1.0 if c != card else 0.0 for c in range(3)]
            br_val_p1 += self.get_br_value("", (-1, card, -1, 1), prob_opp)

        # Average over the 6 possible deals (each card loop does 3, total 6)
        # However, our probability injection was 1.0 per card. 
        # Total combinations = 6. 
        # br_val_p0 sums up 3 scenarios (P0=J, P0=Q, P0=K). Each scenario implicitly sums over 2 opponent cards.
        # So we just divide by 6.
        
        return (br_val_p0 + br_val_p1) / 6 / 2 # The extra /2 is for NashConv -> Exploitability
