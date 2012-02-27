#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
module: player_game
"""
from lib import *
from simple import *
from map.map import Map
import db

# 游戏状态
WAITFORPLAYER='waitforplayer'
RUNNING='running'
FINISHED='finished'

DEFAULT_MAP = 'srcs/map/test.yml'

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
        self.MAX_ROUND = map.meta['round']

    def start(self):
        '''
        # 因为js没有(), 只好用[]
        self.walls = [[10, i]
                      for i in range(5, 35)]
        '''
        self.logs = []
        self.info = None

        self.round = 0
        self.player_op = []
        self.loop_count = 0
        self.status = WAITFORPLAYER

    def add_player(self,
                  type=PYTHON,
                  direction=DOWN,
                  head=None,
                  name="unknown"):
        length = self.map.meta['player_init']
        # 检查蛇类型
        if type not in (PYTHON, RUBY):
            return dict(status='player type error: %s' % type)
        # 检查蛇数量
        if len(self.players) >= self.map.meta['player_max']:
            return dict(status='no place for new player.')
        if self.status == FINISHED:
            return dict(stauts='cannot add player when game is finished.')
        
        # 随机生成蛇的位置
        d = DIRECT[direction]
        if not head:
            while True:
                # 蛇所在的地点不能有东西存在..
                next = self.get_empty_place()
                for i in range(length + 1):
                    body = [(next[0] - d[0] * i) % self.w,
                            (next[1] - d[1] * i) % self.h]
                    if self.check_hit(body):
                        break
                # 如果检查没有发现任何一点重合, 就用改点了.
                else:
                    head = [(next[0] - d[0]) % self.w,
                            (next[1] - d[1]) % self.h]
                    break

        # 生成蛇
        player = Player(self, type, direction, head, length, name)
        self.players.append(player)
        self.player_op.append(dict(op='turn', direction=direction))
        # 强制更新info
        self.info = None
        # 返回蛇的顺序, 以及蛇的id(用来验证控制权限)
        return dict(seq=len(self.players) - 1, id=player.id)

    def set_player(self, n, player):
        """设置蛇, 调试用"""
        self.players[n] = player
        
    def get_seq(self, id):
        """根据蛇的id获取seq"""
        for i, s in enumerate(self.players):
            if s.id == id:
                return i

    def set_player_op(self, id, round, kw):
        # 获取蛇的seq
        n = self.get_seq(id)
        if n == None:
            return "noid"
        # 检查轮数是否正确
        if round != -1 and self.round != round:
            return "round error, current round: %d" % self.round
        
        if kw['op'] == 'turn':
            kw['direction'] = int(kw['direction'])
            d = kw['direction']
            # 检查direction
            if not 0<=d<=3:
                return "direction error: %d" % d
            # check turn back
            sd = self.players[n].direction
        
            self.player_op[n] = kw
            if (sd != d and sd % 2 == d % 2):
                return "noturnback"
            return 'ok'

        elif kw['op'] == 'sprint':
            self.player_op[n] = kw
            return 'ok'
        else:
            return 'wrong op: ' + kw['op'] 

    def check_score(self):
        """计算最高分, 保存到历史中"""
        # 只统计活下来的蛇
        lives = [s
                 for s in self.players
                 if s.alive]
        if len(lives) <=0: return
        # 计算谁的分数最大
        highest = max(lives, key=lambda s: s.length())
        self.log('game finished, winner: ' + highest.name)
        # 再加到最高分里面去
        db.cursor.execute('insert into scores values(?, ?)', (datetime.datetime.now(), highest.name))
        db.db.commit()

    def scores(self):
        d = date.today()
        today = datetime.datetime(d.year, d.month, d.day)
        dailys =  list(db.cursor.execute('select * from (select name, count(*) as count from scores where time > ? group by name) order by count desc limit 10', (today, )))
        weeklys = list(db.cursor.execute('select * from (select name, count(*) as count from scores where time > ? group by name) order by count desc limit 10', (today - datetime.timedelta(days=7), )))
        monthlys = list(db.cursor.execute('select * from (select name, count(*) as count from scores where time > ? group by name) order by count desc limit 10', (today - datetime.timedelta(days=30), )))
        return dict(dailys=dailys, weeklys=weeklys, monthlys=monthlys)

    def get_map(self):
        return dict(walls=self.walls,
                    portals=self.portals,
                    size=self.size,
                    name=self.map.name,
                    author=self.map.author,
                    )

    def get_info(self):
        if self.info:
            return self.info
        players = [dict(direction=s.direction,
                       body=s.body,
                       name=s.name,
                       type=s.type,
                       sprint=s.sprint,
                       length=len(s.body),
                       alive=s.alive)
                  for s in self.players
                  ]
        self.info = dict(players=players,
                         status=self.status,
                         eggs=self.eggs,
                         gems=self.gems,
                         round=self.round,
                         logs=self.logs)
        return self.info

    def step(self):
        """游戏进行一步..."""
        self.logs = []
        self.info = None
        # 如果游戏结束或者waitforplayer, 等待一会继续开始
        if self.loop_count <= 50 and self.status in [FINISHED, WAITFORPLAYER]:
            self.loop_count += 1
            return

        if self.status == FINISHED:
            self.loop_count = 0
            self.start()
            return True

        # 游戏开始的时候, 需要有2条以上的蛇加入.
        if self.status == WAITFORPLAYER:
            if len(self.players) < 2: return
            self.status = RUNNING
            self.log('game running.')

        # 首先检查获胜条件:
        # 并且只有一个人剩余
        # 或者时间到
        alives = sum([s.alive for s in self.players])
        if alives <= 1 or(self.MAX_ROUND != 0 and self.round > self.MAX_ROUND):
            self.status = FINISHED
            self.loop_count = 0
            self.check_score()
            return True

        # 移动player
        for i, d in enumerate(self.player_op):
            player = self.players[i]
            if not player.alive: continue

            # 如果连续没有响应超过10次, 让蛇死掉
            if d == None and self.enable_no_resp_die:
                self.no_response_player_die(player, self.round)

            player.op(d)
            player.move()

        # 生成豆子
        if self.map.beangen.can(self):
            beans = self.map.beangen.gen(self)
            self.eggs += beans[0]
            self.gems += beans[1]
        
        #if self.round % self.bean_time == 0:
        #    self.create_bean()

        # next round
        self.round += 1
        self.player_op = [None, ] * len(self.players)
        return True

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
        如果连续没有响应超过3次, 让蛇死掉
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
    >>> game = Game(
    ...     start_unit=100, 
    ...     enable_no_resp_die=False)

    # 玩家加入
    >>> player1 = game.add_player('player1')
    >>> player1['seq'] == 0
    True
    >>> player2 = game.add_player('player2')
    >>> player2['seq'] == 1
    True

    # 游戏可以开始了
    >>> game.status == WAITFORPLAYER
    True
    >>> game.round == 0
    True
    >>> game.step()
    >>> game.round == 1
    True
    
    # 一个回合之后, 玩家的单位开始增长了
    >>> game.holds[0] == 110
    >>> game.holds[1] == 100

    # 玩家开始出兵
    >>> game.player_move(0, [[100, 0, 4], ])
    >>> game.player_move(1, [[10, 1, 4], ])
    
    # 出兵到达目标星球
    # 战斗计算

    # 结束逻辑测试
    # 只有一个玩家剩下的时候, 游戏结束
    # 回合数到的时候, 星球多的玩家胜利
    # 回合数到的时候, 星球一样, 单位多的玩家胜利
    # 回合数到的时候, 星球一样, 单位一样, 序号后面的玩家胜利 
    """
    import doctest
    doctest.testmod()

def main():
    test()
    
if __name__=="__main__":
    main()
