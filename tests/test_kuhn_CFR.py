import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from kuhn.CFR import CFR_agent

#Compute the expected utilities of each players strategies
def test_expected_utilities():

    ITERATIONS = 25000
    PLOT = False

    agent = CFR_agent(ITERATIONS, PLOT)
    agent.train()
    
    agent.calculate_final_strategy()
        
    p2_utility = -agent.calculate_expected_utility()

    assert 0.055 < p2_utility < 0.056
    




