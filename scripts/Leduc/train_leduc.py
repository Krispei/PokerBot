import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../src"))

from leduc.CFR import CFR_agent

ITERATIONS = 100000#Iterations used in training
PLOT_STRATEGY = False #Plot the final (best) strategy over iterations
PLOT_EXPLOITABILITY = True

def print_infostate(infostate):

    cards = ['Jack', 'Queen', 'King']

    player = int(infostate[0]) + 1
    card = cards[int(infostate[1])]
    public_card = ''

    if len(infostate) == 2:
        print(f"{card}:  Action is: (ROOT)")
    elif infostate[2] not in ['f','p', 'c', 'r']:
        public_card = cards[int(infostate[2])]
        print(f"{card}:  Public card: {public_card}, Action is: {infostate[3:] if infostate[3:] != '' else '(ROOT)'}")
    else:
        print(f"{card}:  Action is: {infostate[2:] if infostate[2:] != '' else '(ROOT)'}")

def print_strategy(infostate, agent):

    probabilities = "Probabilities: "

    for action in agent.infostate_map[infostate].actions:
        
        probabilities += f"{action} : {round(agent.infostate_map[infostate].final_strategy[action], 2)}, " 
        
    print(probabilities)

def main():
    
    # Initializing Kuhn Poker CFR agent

    agent = CFR_agent(ITERATIONS, PLOT_STRATEGY, PLOT_EXPLOITABILITY)

    # Train agent

    agent.train()
    agent.calculate_final_strategy()

    p1_infostates = []
    p2_infostates = []

    for infostate in agent.infostate_map:

        if infostate[0] == '0':

            p1_infostates.append(infostate)
        
        else:

            p2_infostates.append(infostate)
   
    print("-----------  GENERAL STATISTICS -----------")
    print(f"Final Exploitability: {agent.exploitability[-1]}")
    print("----------- PLAYER 1 STRATEGIES -----------")
    p1_infostates.sort()
    for infostate in p1_infostates: 
        print_infostate(infostate)
        print_strategy(infostate,agent)
    
    print("----------- PLAYER 2 STRATEGIES -----------")
    p2_infostates.sort()
    for infostate in p2_infostates: 
        print_infostate(infostate)
        print_strategy(infostate,agent)

if __name__ == "__main__":
    main()



    