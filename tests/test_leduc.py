import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from leduc.leduc import leduc

def test_showdown_payouts():

    agent = leduc()

    cards = [2,1,0] # P1 has king, p2 has queen, community board is jack, p1 will always win
    history_map = {'pp:pp': 1,
                   'prc:pp': 2,
                   'rc:pp': 2, 
                   'pp:rc': 3,
                   'rrc:pp': 3,
                   'prrc:pp': 3,
                   'rc:rc': 4,
                   'prc:rc': 4,
                   'rc:prc': 4,
                   'prc:prc': 4,
                   'pp:rrc': 5,
                   'pp:prrc': 5,
                   'rrc:rrc': 7,
                   'rrc:prrc': 7,
                   'prrc:rrc': 7,
                   'prrc:prrc': 7,     
                   }
    
    for history in history_map:
        
        assert agent.payout(history, cards) == history_map[history]

def test_fold_payouts():

    agent = leduc()

    cards = [2,1,0]
    history_map = {'rf': 1,
                   'prf': -1,
                   'rrf': -2,
                   'prrf': 2,
                   'pp:rf': 1,
                   'pp:rrf': -3,
                   'pp:prrf': 3,
                   'rrc:prrf': 5,
                   'rrc:rrf': -5
                    }

    for history in history_map:

        assert agent.payout(history, cards) == history_map[history]

def test_winner():

    agent = leduc()

    history = 'pp:pp'

    p1_winners = [[1,2,1], [2,1,0], [1,0,2], [2,1,2]]
    p2_winners = [[2,1,1], [1,2,0], [0,1,2], [1,2,2]]  
    ties = [[2,2,1], [1,1,0]]

    for cards in p1_winners:
        
        assert agent.payout(history, cards) == 1

    for cards in p2_winners:
        
        assert agent.payout(history, cards) == -1

    for cards in ties:
        
        assert agent.payout(history, cards) == 0
