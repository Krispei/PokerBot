import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../src"))

from kuhn.CFR import CFR_agent

ITERATIONS = 1000000 #Iterations used in training
PLOT = False #Plot the final (best) strategy over iterations

def print_infostate(infostate):

    cards = ['Jack', 'Queen', 'King']

    player = int(infostate[0]) + 1
    card = cards[int(infostate[1])]

    print(f"{card}:  Action is: {infostate[2:] if infostate[2:] != "" else "(ROOT)"}")

def print_strategy(infostate, agent):

    prob_p = round(agent.infostate_map[infostate].final_strategy[0],2)
    prob_b = round(agent.infostate_map[infostate].final_strategy[1],2)

    print(f"Probabilities: Pass: {prob_p}, Bet: {prob_b}")

def print_EV(agent):

    p1_ev = agent.calculate_expected_utility()
    p2_ev = -p1_ev #zero sum game

    print(f"Player 1 expected value : {round(p1_ev,4)}")
    print(f"Player 2 expected value : {round(p2_ev,4)}")

def main():
    
    # Initializing Kuhn Poker CFR agent

    agent = CFR_agent(ITERATIONS, PLOT)

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
    print_EV(agent)


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



    