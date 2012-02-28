#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
module: player_game
"""
from lib import *
from map.map import Map
import db

# 游戏状态
WAITFORPLAYER='waitforplayer'
RUNNING='running'
FINISHED='finished'

DEFAULT_MAP = 'srcs/map/test.yml'

class Player():
    def __init__(self, game, name=""):
        """设置player
        """
        self.game = game
        self.name = name
        self.id = uuid.uuid4().hex
        self.alive = True

class Game():
    """游戏场景"""
    # 记录分数
    def __init__(self,
                 enable_no_resp_die=True,
                 map=None):
        self.enable_no_resp_die = enable_no_resp_die

        if not map:
            map = Map.loadfile(DEFAULT_MAP)
        self.set_map(map)
        
        self.start()

    def log(self, msg):
        self.logs.append(msg)

    def user_set_map(self, data):
        if self.status != WAITFORPLAYER:
            return "only can set map when the game state is waitforplayer"

        try:
            m = Map.loaddata(data)
            self.set_map(m)
            self.start()
            return 'ok'
        except Exception as e:
            # if error, fall back to default map
            self.set_map(Map.loadfile(DEFAULT_MAP))
            self.start()
            return 'setmap error: ', str(e)
        
    def set_map(self, map):
        self.map = map
        self.planets = self.map.planets
        self.routes = self.map.routes
        self.max_round = self.map.max_round

    def start(self):
        self.logs = []
        self.info = None

        self.round = 0
        self.moves = []
        self.players = []
        self.loop_count = 0
        self.player_ops = []
        self.status = WAITFORPLAYER

        self.holds = [(None, 0) for i in range(len(self.map.planets))]
        
    def add_player(self, name="unknown"):
        # 生成玩家
        player = Player(self, name)
        self.players.append(player)
        # 强制更新info
        self.info = None
        # 玩家加入地图
        player_id = len(self.players)-1
        planet_id = self.map.starts[player_id]
        self.holds[planet_id] = [player_id, self.map.meta['start_unit']]
        # 返回玩家的顺序, 以及玩家的id(用来验证控制权限)
        return dict(seq=len(self.players) - 1, id=player.id)

    def get_seq(self, id):
        """根据玩家的id获取seq"""
        for i, s in enumerate(self.players):
            if s.id == id:
                return i

    def set_player_op(self, id, kw):
        # 获取玩家的seq
        n = self.get_seq(id)
        if n == None:
            return "noid"
        
        if kw['op'] == 'moves':
            for count, _from, to in kw['moves']:
                # 检查moves合法性
                # todo
                step = self.routes[(_from, to)]
                self.moves.append([n, _from, to, count, step])
            return 'ok'
        else:
            return 'wrong op: ' + kw['op']

    def check_winner(self):
        """
        胜利判断按照: 星球总数, 单位数量, 玩家顺序 依个判断数值哪个玩家最高来算. (不会出现平局)
        同时计算最高分, 保存到历史中
        """
        scores = [[0, 0, i] for i in range(len(self.players))]
        for side, count in self.holds:
            if side != None:
                scores[side][0] += 1
                scores[side][1] += count

        maxid = max(scores)[2]
        winner = self.players[maxid]
        self.log('game finished, winner: ' + winner.name)
        # 再加到最高分里面去
        db.cursor.execute('insert into scores values(?, ?)', (datetime.datetime.now(), winner.name))
        db.db.commit()
        return maxid

    def scores(self):
        """
        获取游戏历史分数
        """
        d = date.today()
        today = datetime.datetime(d.year, d.month, d.day)
        dailys =  list(db.cursor.execute('select * from (select name, count(*) as count from scores where time > ? group by name) order by count desc limit 10', (today, )))
        weeklys = list(db.cursor.execute('select * from (select name, count(*) as count from scores where time > ? group by name) order by count desc limit 10', (today - datetime.timedelta(days=7), )))
        monthlys = list(db.cursor.execute('select * from (select name, count(*) as count from scores where time > ? group by name) order by count desc limit 10', (today - datetime.timedelta(days=30), )))
        return dict(dailys=dailys, weeklys=weeklys, monthlys=monthlys)

    def get_map(self):
        return dict(routes=self.map.seq_routes,
                    planets=self.planets,
                    max_round=self.max_round,
                    desc=self.map.desc,
                    name=self.map.name,
                    author=self.map.author,
                    map_size = self.map.map_size,
                    )

    def get_info(self):
        if self.info:
            return self.info
        self.info = dict(round=self.round,
                         status=self.status,
                         players=[dict(name=p.name) for p in self.players],
                         moves=self.moves,
                         holds=self.holds,
                         logs=self.logs)
        return self.info

    def check_finished(self):
        """
        检查游戏是否结束
        当回合限制到达或者只有一个玩家剩下的时候, 游戏结束.
        """
        if self.round > self.max_round:
            return True

        players = set()
        for side, count in self.holds:
            if side != None:
                players.add(side)
        if len(players) == 1: 
            return True

    def step(self):
        """
        游戏进行一步
        返回值代表游戏是否有更新
        """
        self.logs = []
        self.info = None
        # 如果游戏结束, 等待一会继续开始
        if self.loop_count <= 50 and self.status in [FINISHED]:
            self.loop_count += 1
            return

        if self.status == FINISHED:
            self.loop_count = 0
            self.start()
            return True

        # 游戏开始的时候, 需要有2个以上的玩家加入.
        if self.status == WAITFORPLAYER:
            if len(self.players) < 2: return
            self.status = RUNNING
            self.log('game running.')

        if self.check_finished():
            self.status = FINISHED
            self.loop_count = 0
            self.check_winner()
            return True

        # 生产回合
        for i, data in enumerate(self.holds):
            side, count = data
            if side == None: continue
            next = self.count_growth(count, self.planets[i])
            if next <= 0: side = None
            self.holds[i] = [side, next]

        # 玩家移动回合
        for i, d in enumerate(self.player_ops):
            player = self.players[i]
            if not player.alive: continue

            # 如果连续没有响应超过10次, 让玩家死掉
            if d == None and self.enable_no_resp_die:
                self.no_response_player_die(player, self.round)

            player.op(d)

        # 到达回合
        for move in self.moves:
            move[-1] -= 1
        arrives = filter(lambda move: move[-1]<=0,  self.moves)
        self.moves = filter(lambda move: move[-1]>0,  self.moves)
        
        # 战斗回合
        for move in arrives:
            self.battle(move)
            
        # next round
        self.round += 1
        self.player_op = [None, ] * len(self.players)
        return True

    def battle(self, move):
        """
        战斗阶段
        首先进行def加权, 星球的单位Xdef 当作星球的战斗力量.
        双方数量一样, 同时全灭, A>B的时候, B全灭, A-B/(A/B) (B/(A/B)按照浮点计算, 最后去掉小数部分到整数)
        如果驻守方胜利, 除回def系数, 去掉小数部分到整数作为剩下的数量.
        """
        side, _from, to, count, _round = move
        planet_side, planet_count = self.holds[to]
        _def = self.planets[to]['def']

        if planet_side == None:
            # 如果星球没有驻军, 就占领
            planet_side = side
            planet_count = count
        elif side == planet_side:
            # 如果是己方, 就加入
            planet_count += count
        else:
            # 敌方战斗
            # 防守方加权
            planet_count *= _def
            if planet_count == count:
                # 数量一样的话, 同时全灭
                planet_side, planet_count = None, 0
            elif planet_count < count:
                # 进攻方胜利
                planet_side = side
                planet_count = count - int(planet_count**2/float(count))
            else:
                # 防守方胜利                
                planet_count -= int(count**2/float(planet_count))
                planet_count = int(planet_count / _def)
                
        self.holds[to] = [planet_side, planet_count]

    def count_growth(self, planet_count, planet):
        max = planet['max']
        res = planet['res']
        cos = planet['cos']
        if planet_count <= max or res < 1:
            return planet_count * res + cos
        else:
            return planet_count

    def get_portal_next(self, p):
        seq = self.portals.index(p)
        return self.portals[(seq / 2)*2 + ((seq%2)+1)%2 ]
    
    def create_bean(self):
        """生成豆子
        """
        if not self.enable_bean: return

        pos = self.get_empty_place()
        # 随机掉落豆子的种类
        if random.randint(0, 1):
            # 有豆子数量限制
            if len(self.gems) > 10: return
            self.gems.append(pos)
        else:
            if len(self.eggs) > 10: return
            self.eggs.append(pos)

    def check_hit(self, p):
        """检查p和什么碰撞了, 返回具体碰撞的对象"""
        if p in self.walls:
            return WALL
        if p in self.eggs:
            return EGG
        if p in self.gems:
            return GEM
        if p in self.portals:
            return PORTAL
        return self.check_hit_player(p)

    def check_hit_player(self, p):
        for player in self.players:
            if p in player.body:
                return player

    def get_empty_place(self):
        """
        随机获取一个空的位置
        可能是性能陷阱?
        """
        while True:
            p = [random.randint(0, self.w-1),
                 random.randint(0, self.h-1)]
            # 不要和其他东西碰撞
            if self.check_hit(p):
                continue
            return p

    def alloped(self):
        """
        判断是否所有玩家都做过操作了
        """
        oped = [
            (not s.alive or op != None)
            for op, s in zip(self.player_op,
                             self.players)]
        return all(oped)

    def no_response_player_die(self, player, round):
        """
        如果连续没有响应超过3次, 让玩家死掉
        round是没有响应的轮数(用来检查是否连续没有响应)
        
        """
        # 初始化缓存
        if (not hasattr(player, 'no_resp_time') or
            player.no_resp_round != round - 1):
            player.no_resp_time = 1
            player.no_resp_round = round
            return
        # 次数更新
        player.no_resp_time += 1
        player.no_resp_round = round            
        # 判断是否没有响应时间过长
        if player.no_resp_time >= 5:
            player.alive = False
            logging.debug('kill no response player: %d' % \
                         self.players.index(player))
            self.log('kill player for no response: '+player.name)


def test():
    """
    # 初始化游戏
    >>> g = Game(enable_no_resp_die=False)

    # 玩家加入
    >>> player1 = g.add_player('player1')
    >>> player1['seq'] == 0
    True
    >>> player2 = g.add_player('player2')
    >>> player2['seq'] == 1
    True
    >>> g.holds
    [[0, 100], [1, 100], (None, 0), (None, 0), (None, 0)]
    
    # 游戏可以开始了
    >>> g.status == WAITFORPLAYER
    True
    >>> g.round == 0
    True
    >>> g.step()
    True
    >>> g.round == 1
    True
    
    # 一个回合之后, 玩家的单位开始增长了
    >>> g.holds
    [[0, 110], [1, 110], (None, 0), (None, 0), (None, 0)]


    # 玩家开始出兵
    >>> g.set_player_op(player1['id'], {'op': 'moves', 'moves': [[100, 0, 4], ]})
    'ok'
    >>> g.set_player_op(player2['id'], {'op': 'moves', 'moves': [[10, 1, 4], ]})
    'ok'

    # 出兵到达目标星球
    >>> g.step()
    True
    >>> g.moves
    [[0, 0, 4, 100, 1], [1, 1, 4, 10, 1]]

    # 能够获取API
    >>> g.get_map()
    {'planets': [{'res': 1, 'cos': 10, 'pos': (0, 0), 'def': 2, 'max': 1000}, {'res': 1, 'cos': 10, 'pos': (4, 0), 'def': 2, 'max': 1000}, {'res': 1, 'cos': 10, 'pos': (0, 4), 'def': 2, 'max': 1000}, {'res': 1, 'cos': 10, 'pos': (4, 4), 'def': 2, 'max': 1000}, {'res': 1.5, 'cos': 0, 'pos': (2, 2), 'def': 0.5, 'max': 300}], 'name': 'test', 'map_size': (5, 5), 'author': 'halida', 'routes': [(0, 1, 4), (3, 2, 4), (1, 3, 4), (3, 4, 2), (3, 1, 4), (1, 4, 2), (2, 4, 2), (2, 0, 4), (2, 3, 4), (4, 3, 2), (0, 4, 2), (4, 2, 2), (1, 0, 4), (4, 1, 2), (0, 2, 4), (4, 0, 2)], 'max_round': 8000, 'desc': 'this the the standard test map.'}
    >>> g.get_info()
    {'status': 'running', 'holds': [[0, 120], [1, 120], (None, 0), (None, 0), (None, 0)], 'moves': [[0, 0, 4, 100, 1], [1, 1, 4, 10, 1]], 'logs': [], 'round': 2}
    
    # 战斗计算
    >>> g.step()
    True
    >>> g.holds[4]
    [0, 96]

    # 结束逻辑测试
    >>> import copy

    # 只有一个玩家剩下的时候, 游戏结束
    >>> gend = copy.deepcopy(g)
    >>> gend.holds[1] = [None, 0]
    >>> gend.step()
    True
    >>> gend.status == FINISHED
    True
    >>> gend.check_winner()
    0
    
    # 回合数到的时候, 星球多的玩家胜利
    >>> gend = copy.deepcopy(g)
    >>> gend.round = 10000
    >>> gend.step()
    True
    >>> gend.status == FINISHED
    True
    >>> gend.check_winner()
    0
    
    # 回合数到的时候, 星球一样, 单位多的玩家胜利
    >>> gend = copy.deepcopy(g)
    >>> gend.round = 10000
    >>> gend.holds[4] = [None, 0]
    >>> gend.step()
    True
    >>> gend.status == FINISHED
    True
    >>> gend.check_winner()
    1
    
    # 回合数到的时候, 星球一样, 单位一样, 序号后面的玩家胜利
    >>> gend = copy.deepcopy(g)
    >>> gend.round = 10000
    >>> gend.holds[4] = [None, 0]
    >>> gend.holds[0] = [0, 100]
    >>> gend.holds[1] = [1, 100]
    >>> gend.step()
    True
    >>> gend.status == FINISHED
    True
    >>> gend.check_winner()
    1
    """
    import doctest
    doctest.testmod()
    
if __name__=="__main__":
    test()
