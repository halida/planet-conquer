#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
module: game_controller
游戏控制器.. 提供api级别的接口, 方便服务器调用game

"""
from game import *
import scores

class RoomController():
    def __init__(self, games):
        self.games = games
        self.controllers = [Controller(g)
                            for g in self.games]
    def op(self, data):
        """
        分配room
        """
        # 检查room
        if not data.has_key('room'):
            return dict(status = "data has no room param.")
        
        try:
            room = int(data['room'])
        except Exception as e:
            return dict(status="room data (%s) error: %s" % (data['room'], str(e)))
        
        if not 0 <= room < len(self.games):
            return dict(status='room number error: %d'%room)
        # 分配处理
        return self.controllers[room].op(data)

class Controller():
    def __init__(self, game):
        self.game = game

    def op(self, data):
        """
        统一的op接口
        """
        op = data['op']
        if op == 'add':
            return self.game.add_player(data.get('name', 'unknown'), data.get('side', 'unknown'))
        
        elif op in ('moves'):
            if isinstance(data['moves'] , basestring):
                data['moves'] = json.loads(data['moves'])
            return dict(status=self.game.set_player_op(data['id'], data))
        
        elif op == 'map':
            return self.game.get_map()

        elif op == 'setmap':
            return dict(status=self.game.user_set_map(data['data']))
        
        elif op == 'info':
            return self.game.get_info()
        
        elif op == 'history':
            return self.history()
        
        elif op == 'scores':
            return scores.scores()
        
        else:
            return dict(status='op error: %s' % op)

def test():
    """
    # 初始化
    >>> game = Game()
    >>> c = Controller(game)

    # 添加新玩家
    >>> result = c.op(dict(op='add', name='foo'))
    >>> result = c.op(dict(op='add', name='bar'))
    >>> id = result['id']
    >>> result['seq']
    1

    # 发送指令
    >>> result = c.op(dict(op='moves', id=id, moves=[]))

    # 获取地图信息
    >>> m = c.op(dict(op='map'))

    # 获取实时信息
    >>> info = c.op(dict(op='info'))

    # 获取得分
    >>> score = c.op({'op' : 'scores'})
    """
    import doctest
    doctest.testmod()

if __name__=="__main__":
    test()
