import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from kuhn.kuhn import KuhnPoker
import random

def play_vs_random():

  game = KuhnPoker()

  cards = random.sample(game.cards, 2)

  history = ''

  print('-----------KUHN POKER-----------')
  print(f'Your card is : {cards[0]}')


  while not game.isGameFinished(history):
    
    player_turn = game.getPlayerToAct(history)

    if player_turn == 1:

      print(f'Your available actions : {game.actions}')

      action = ""

      while action not in game.actions:

        action = input(f"what action would you like to take? : ")

      history += action

    else :

      bot_action = random.choice(game.actions)

      print(f"The bot chose {bot_action}!")

      history += bot_action

  print(f"Game finished! you had {cards[0]} while the bot had {cards[1]}. Your payout is {game.getPayouts(history, cards)}")
  print('--------------------------------')

play_vs_random()


