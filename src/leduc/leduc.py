'''
Docstring for leduc.leduc

This file contains the class leduc that acts as the game engine for Leduc Poker.

The Rules of Leduc Poker goes as follows:

2 Players play with a deck of 6 cards (jacks, queens, and kings in two suits)

1. Each player draws a card from the deck
2. The first betting round occurs, player 1 is first to act. each player can bet, check, fold, and raise when appropriate
3. After the first betting round, another card is drawn from the deck and placed faceup in the middle (public card)
4. The second and final betting round occurs, with player 1 first to act.
5. Both players showdown if neither player folded in the previous betting rounds. The pot goes to the winner which is determined in this order:
    Pair > high card, K > Q > J

'''

class leduc():

    def __init__(self):
        
        self.cards = ['0h', '1h', '2h', '0s', '1s', '2s']

        self.actions = ['r','c','f', 'p'] # bet, 'r': raise, 'c': call, 'f': fold, 'p': check/pass

    def terminal(self, history):

        #if any player folds, the game instantly terminates
        if history[-1] == 'f':
            return True

        #if there is a flat call in round 2, the game ends
        if ':' in history and history[-1] == 'c':
            return True
        
        #if both players check round 2, the game ends
        if ':' in history and history[-2:] == 'pp':
            return True

    def r1_over(self, history):

        if ':' in history:
            return True
        
        if history[-1] == 'c':
            return True
        
        if history[-2:] == 'pp':
            return True
        
    def get_round(self, history):

        if ':' in history:
            return 2
        else:
            return 1

    def player_to_act(self, history):
        
        #examples of histories:  'c' - P1 checks, P2 to act
        #                        'br' - P1 bets, P2 raise, P1 to act
        #                        'bc:' - P1 bets, P2 calls, P1 to act

        if self.get_round(history=history) == 2:    

            if len(history) % 2 == 1: 
                return 0 #P1
            else: 
                return 1 #P2
            
        else: 

            if len(history) % 2 == 1: 
                return 1 #P2
            else: 
                return 0 #P2
        
    def payout(self, history, cards):
        
        '''
        THIS FUNCTION RETURNS THE PAYOUT TO PLAYER 1 ALWAYS
        
        POT RULES FOR LEDUC POKER:
    
        - 1 raise limit per betting round.
        - in round 1, a raise is +1 into the pot. ex: a bet and then a raise is +1, +2.
        - in round 2, a raise is +2 into the pot. ex: a bet and then a raise is +2, +4.
        ex) prc:pp -> pot = 2 (antes) + 2 (round 1) + 0(round 2), payout = 1 (ante) + 1(round 1)
        ex) bf -> pot = 2 (antes) + 1 (round 1), payout = 1 (ante), 0 (round 1)
        :param self: 
        :param history: String text that holds the history of the hand so far
        '''

        if not self.terminal(history=history):
            return 0
        
        round_1, separator, round_2 = history.partition(':')

        payout = 0

        # Calulate payout from round_1:
            
        
        player = self.player_to_act(history=history)

        # Fold cases
        if 'f' in history:
            
            if player == 0:

                return payout
            
            else:

                return -payout
        
        # Showdown cases

        
            






        


