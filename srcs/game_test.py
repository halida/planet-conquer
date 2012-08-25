# test_code for games

import game
import map.map
from map.map import Map
from game import Game, Player
from nose.tools import *

map.map.random_starts = False

def player_test():
    player = Player(game="game_instance", name="player_name")
    eq_(player.game, "game_instance")
    eq_(player.name, "player_name")
    assert player.alive

def game_init_test():
    g = Game()
    yield check_game_empty, g, game.WAITFORPLAYER

def check_game_empty(game, game_status):
    eq_(game.status, game_status)
    eq_(game.round, 0)
    eq_(game.moves, [])
    eq_(game.players, [])
    eq_(game.loop_count, 0)
    eq_(game.player_ops, [])

def count_growth_test():
    g = Game(enable_no_resp_die = False)
    # not growth:
    eq_( g.count_growth(12, dict(max=10, res=1, cos=5)), 12 )
    eq_( g.count_growth(12, dict(max=12, res=1, cos=5)), 12 )
    # normal growth: result = int(12 * 1.1 + 5) = 18
    eq_( g.count_growth(12, dict(max=100, res=1.1, cos=5)), 18)
    # dec
    eq_( g.count_growth(12, dict(max=100, res=0.5, cos=3)), 9)
    # dec even more than max
    eq_( g.count_growth(12, dict(max=5, res=0.5, cos=3)), 9 )
    # grownth should not beyond max
    eq_( g.count_growth(12, dict(max=15, res=2, cos=10)), 15)


def move_test():
    g = Game(enable_no_resp_die = False, map = "srcs/map/ut_test.yml")
    
    # add_player
    player1 = g.add_player('player1')
    eq_(player1['seq'], 0)
    player2 = g.add_player('player2')
    eq_(player2['seq'], 1)
    
    # add two action
    eq_(g.set_player_op(player1['id'], dict(op='moves', moves=[[50, 0, 4],[50, 0, 2],])), "ok")
    g.step()
    eq_(g.holds, [[None, 0], [1, 110], [None, 0], [None, 0], [0, 75]])
    

def move_zero_test():
    g = Game(enable_no_resp_die = False, map = "srcs/map/ut_test.yml")
    # add_player
    player1 = g.add_player('player1')
    eq_(player1['seq'], 0)
    player2 = g.add_player('player2')
    eq_(player2['seq'], 1)
    # add a empty move
    g.set_player_op(player1['id'], dict(op='moves', moves=[[0, 0, 4]]))
    g.move_stage()
    g.battle_stage(g.arrive_stage())
    eq_(g.holds, [[0, 100], [1, 100], [None, 0], [None, 0], [None, 0]])
    g.next_round()
    eq_(g.holds, [[0, 120], [1, 110], [None, 0], [None, 0], [None, 0]])
   
def multi_battle_case_test():
    g = Game(enable_no_resp_die = False, map = "srcs/map/ut_test.yml")
    yield check_game_empty, g, game.WAITFORPLAYER

    player1 = g.add_player('player1')
    eq_(player1['seq'], 0)
    player2 = g.add_player('player2')
    eq_(player2['seq'], 1)
    player3 = g.add_player('player3')
    eq_(player3['seq'], 2)
    
    #round 0:
    eq_(g.holds, [[0, 100],[1, 100], [2, 100], [None, 0], [None, 0]])
    eq_(g.status, game.WAITFORPLAYER)
    eq_(g.round, 0)
    #round 1:
    ok_(g.step())
    eq_(g.holds, [[0, 120], [1, 110], [2, 110], [None, 0], [None, 0]])
    #round 2:
    g.set_player_op(player1['id'], dict(op='moves', moves=[[50, 0, 4],]))
    #g.set_player_op(player1['id'], dict(op='moves', moves=[[100, 0, 4], ]))
    g.step()
    eq_(g.holds, [[0, 87], [1, 120], [2, 120], [None, 0], [0, 75]])
    #round 3:
    g.set_player_op(player1['id'], dict(op='moves', moves=[[50, 0, 4], ]))
    g.set_player_op(player2['id'], dict(op='moves', moves=[[100, 1, 4], ]))
    g.set_player_op(player3['id'], dict(op='moves', moves=[[110, 2, 4], ]))
    g.step()
    eq_(g.holds, [[0, 50], [1, 30], [2, 20], [None, 0], [2, 43]])
    #round 4:
    g.set_player_op(player1['id'], dict(op='moves', moves=[[21, 0, 4], ]))
    g.set_player_op(player2['id'], dict(op='moves', moves=[[10, 1, 4], ]))
    g.set_player_op(player3['id'], dict(op='moves', moves=[[1, 4, 2], ]))
    g.step()
    eq_(g.holds, [[0, 41], [1, 30], [2, 30], [None, 0], [None, 0]])
 
def play_game_case_test():
    # init game
    g = Game(enable_no_resp_die = False, map = "srcs/map/ut_test.yml")
    yield check_game_empty, g, game.WAITFORPLAYER
    
    # add_player
    player1 = g.add_player('player1')
    eq_(player1['seq'], 0)
    player2 = g.add_player('player2')
    eq_(player2['seq'], 1)
    # round 0:
    eq_(g.holds, [[0, 100], [1, 100], [None, 0], [None, 0], [None, 0]])
    eq_(g.status, game.WAITFORPLAYER)
    eq_(g.round, 0)
    # round 1:
    ok_(g.step())
    eq_(g.round, 1)
    eq_(g.holds, [[0, 120], [1, 110], [None, 0], [None, 0], [None, 0]])
    # round 2:
    ok_(g.step())
    eq_(g.holds, [[0, 142], [1, 120], [None, 0], [None, 0], [None, 0]])
    # round 3: test move & arrive
    g.set_player_op(player1['id'], dict(op='moves', moves=[[100, 0, 4], ]))
    g.step()
    eq_(g.holds, [[0, 56], [1, 130], [None, 0], [None, 0], [0, 150]])
    # round4: move all
    eq_(g.set_player_op(player1['id'], dict(op='moves', moves=[[56, 0, 4], ])), "ok")
    g.step()
    eq_(g.holds, [[None, 0], [1, 140], [None, 0], [None, 0], [0, 300]])
    # what for a long time:
    for i in range(100):
        g.step()
    eq_(g.holds, [[None, 0], [1, 1000], [None, 0], [None, 0], [0, 300]])
    # let's fight
    g.set_player_op(player2['id'], dict(op='moves', moves=[[100, 1, 4],]))
    g.step()
    # Attack: 100 Defence 150 => 150 - 100 * 100 / 150 = 84 ~ 168
    # growth: 168 * 1.5 = 252
    eq_(g.holds, [[None, 0], [1, 910], [None, 0], [None, 0], [0, 249]])
    g.step()
    eq_(g.holds, [[None, 0], [1, 920], [None, 0], [None, 0], [0, 300]])
    # get a new planet
    g.set_player_op(player1['id'], dict(op='moves', moves=[[1, 4, 0], ]))
    g.step()
    eq_(g.holds,[[0, 11], [1, 930], [None, 0], [None, 0], [0, 300]])
    g.step()
    eq_(g.holds,[[0, 22], [1, 940], [None, 0], [None, 0], [0, 300]])
    print g.moves
    
    

