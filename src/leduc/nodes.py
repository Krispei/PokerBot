class Node:

    def __init__(self, actions):
        
        self.actions = actions
        self.regret_sum = [0.0] * len(actions) 
        self.strategy = [0.0] * len(actions)
        self.strategy_sum = [0.0] * len(actions)
        self.value = [0.0] * len(actions)
        self.final_strategy = [0.0] * len(actions)

    
