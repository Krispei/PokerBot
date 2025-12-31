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

    

test_expected_utilities()




