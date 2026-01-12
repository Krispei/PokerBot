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
        
        self.cards = [0,0,1,1,2,2]

    def terminal(self, history):
        '''
        Returns whether or not the game has finished based on the history
                
        :param self: self
        :param history: string history
        :return: True for if the game is over, False for if not
        :rtype: Boolean
        '''
        #if any player folds, the game instantly terminates
        if history == '':
            return False
        
        if history[-1] == 'f':
            return True

        #if there is a flat call in round 2, the game ends
        if ':' in history and history[-1] == 'c':
            return True
        
        #if both players check round 2, the game ends
        if ':' in history and history[-2:] == 'pp':
            return True
        
        return False

    def r1_over(self, history):
        '''
        Returns whether or not the game is ready to move on to round 2

        :param self: Self
        :param history: string history
        :return: True for if the game is ready to move onto round 2 / False otherwise
        :rtype: Boolean
        '''
        if history == '':
            return False

        if ':' in history:
            return False
        
        if history[-1] == 'c':
            return True
        
        if history[-2:] == 'pp':
            return True
        
        return False
        
    def get_round(self, history):
        '''
        Returns which round the game is currently on
        
        :param self: self
        :param history: string history
        :return: 1 for round 1, 2 for round 2
        :rtype: Int
        '''
        if ':' in history:
            return 2
        else:
            return 1

    def player_to_act(self, history):
        '''
        GETS THE PLAYER TO ACT NEXT BASED ON HISTORY: Player 1: 0, Player 2: 1
        
        examples of histories:  'c' - P1 checks, P2 to act
                                'br' - P1 bets, P2 raise, P1 to act
                                'bc:' - P1 bets, P2 calls, P1 to act

        :param self: Description
        :param history: string history
        :return: Returns the player next to act (0,1) for (P1, P2)
        :rtype: Int
        '''
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
        :return: Returns the payout for Player 1 always
        :rtype: Int
        '''
        if not self.terminal(history=history):
            return 0
        
        round_1, separator, round_2 = history.partition(':')
        chips_committed = [1,1]
        
        r1_raises = 0


        for i in range(len(round_1)):
            player = (i % 2)
            if round_1[i] == 'c':
                if r1_raises == 1:
                    chips_committed[player] += 1
                else:
                    chips_committed[player] += 1
                break
            elif round_1[i] == 'r':
                if r1_raises == 1:
                    chips_committed[player] += 2
                else:
                    chips_committed[player] += 1
                r1_raises += 1
            elif round_1[i] == 'f':
                if player == 0:
                    return -chips_committed[player]
                else:
                    return chips_committed[player]
            else:
                continue

        r2_raises = 0

        for i in range(len(round_2)):
            player = (i % 2)
            if round_2[i] == 'c':
                if r2_raises == 1:
                    chips_committed[player] += 2
                else:
                    chips_committed[player] += 2
                break
            elif round_2[i] == 'r':
                if r2_raises == 1:
                    chips_committed[player] += 4
                else:
                    chips_committed[player] += 2
                r2_raises += 1
            elif round_2[i] == 'f':
                if player == 0:
                    return -chips_committed[player]
                else:
                    return chips_committed[player]
            else:
                continue

        #showdown cases:
        p1_card = cards[0]
        p2_card = cards[1]
        community_card = cards[2]

        if p1_card == community_card:
            
            return chips_committed[1]
        
        if p2_card == community_card:

            return -chips_committed[0]
        
        if p1_card > p2_card:

            return chips_committed[1]
        
        if p2_card > p1_card:

            return -chips_committed[0]
        
        return 0
    
    def actions(self, history):

        if history == '':

            return ['p', 'r']
        
        if history[-1] == ':':

            return ['p', 'r']

        if history[-1] == 'p':
            
            return ['p', 'r']
        
        if history[-1] == 'r':
            
            num_raises = 0

            if ':' in history:

                r1, sep, r2 = history.partition(':')
                
                num_raises = r2.count('r')
            
            else:

                num_raises = history.count('r')

            if num_raises > 1:

                return ['f', 'c']
            
            else:

                return ['f', 'c', 'r']
        
        return []

 
                
