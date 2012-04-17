#-*- coding:utf-8 -*-
"""
author: yangchen <ignoramus365@gmail.com>
module: ai_tutorial
"""
import json, time
import urllib, httplib, logging

import copy

logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s - %(levelname)s - %(message)s")

#SERVER = 'localhost'
#SERVER = "10.10.99.183"
#SERVER = "pythonvsruby.org"
SERVER = "localhost"
PORT = 9999
DIRS = [[-1, 0], [0, -1], [1, 0], [0, 1]]

def print_dict(d):
    for k in d:
        print k, ':', d[k]

class SimpleAI():
    def __init__(self, ai_name, side='python', room=0):
        self.conn = httplib.HTTPConnection(SERVER, PORT)
        self.room = room
        self.d = 0

        #加入房间
        self.cmd_add(ai_name, side)
        #获取地图
        self.cmd_map()
        #更新地图信息
        self.cmd_info()
        #得到当前的回合
        self.round = self.info['round']

        # constants

        self.M = 100

        # weights
        self.DANGER = 8
        self.FLEE = 9
        self.REIN = 10

        # seqs
        self.ME = set([self.me["seq"]])
        self.ALL = set([None, 0, 1, 2, 3])
        self.NOTME = self.ALL - self.ME

        if self.me["seq"] < 3:
            self.PRI = True
        else:
            self.PRI = False

    def cmd(self, cmd, data={}):
        """
        发送命令给服务器
        """
        data['op'] = cmd
        data['room'] = self.room
        # logging.debug('post: %s : %s', cmd, data)
        self.conn.request("POST", '/cmd',
                          urllib.urlencode(data),
                          {'Content-Type': 'application/x-www-form-urlencoded'})
        result = self.conn.getresponse().read()
        return json.loads(result)

    def cmd_add(self, ai_name, side):
        result = self.cmd("add",
                           dict(name=ai_name, side=side))

        if result.has_key('id'):
            self.me = result
            return self.me

    def cmd_map(self):
        self.map = self.cmd("map")

    def cmd_info(self):
        self.info = self.cmd("info")

    def cmd_moves(self, moves):
        return self.cmd("moves",
                        dict(id = self.me["id"],
                             moves = moves))

    def is_next_round(self):
        self.cmd_info()
        current_round = self.info['round']
        next_round = False
        if current_round > self.round:
            self.round = current_round
            next_round = True
        return next_round

    def get_myplanets(self):
        myplanets = {}
        for i, p in enumerate(self.info['holds']):
            if p[0] == self.me["seq"]:
                myplanets[i] = p[1]

        #self.myplanets = myplanets
        return myplanets

    def get_frontiers(self, myplanets = None):
        if myplanets == None:
            myplanets = self.myplanets
        frontiers = {}

        # find frontier planets
        for route in self.map["routes"]:
            if route[0] in myplanets and not route[1] in myplanets:
                fr = route[1]
                defence = self.exp_defence(fr, route[2])
                frontiers[fr] = defence

        #self.frontiers = frontiers
        return frontiers

    def get_positions(self):
        positions = {}
        for planet in self.frontiers:
            positions[planet] = 0

        totalnp = len(self.map["planets"])

        # ugly
        if len(positions) == 0:
            return dict([(i, 0) for i in range(totalnp)])

        #print 'totalnp', totalnp
        np = len(positions)
        dist = 1
        while np < totalnp:
            pos = {}
            for route in self.map["routes"]:
                if route[1] in positions and not route[0] in positions and not route[0] in pos:
                    pos[route[0]] = dist
                    np = np + 1
            dist = dist + 1
            positions = dict(positions.items() + pos.items())

        #self.positons = positions
        return positions

    def get_plweights(self):
        NUMweights = 12

        positions = self.get_positions()
        plweights = [[0] * NUMweights for i in range(len(self.map["planets"]))]
        for i, weight in enumerate(plweights):
            plweights[i][0] = i
            plweights[i][1] = positions[i]
            plweights[i][2] = self.info["holds"][i][1]
            plweights[i][3] = self.map["planets"][i]["def"]
            plweights[i][4] = self.map["planets"][i]["res"]
            plweights[i][5] = self.map["planets"][i]["max"]
            #plweights[i][6] = self.compute_geo(i)
            #plweights[i][7] = self.compute_hub(i)
            plweights[i][8] = False
            plweights[i][9] = False
            plweights[i][10] = False

        #self.plweights = plweights
        return plweights

    def get_emptyfrontiers(self):
        return [frontier for frontier in self.frontiers if self.info["holds"][frontier][1] == 0]

    def get_neighbors(self, planet):
        return [route[1] for route in self.map["routes"] if route[0] == planet]

    def get_dist(self, _from, _to):
        for r in self.map["routes"]:
            if r[0] == _from and r[1] == _to:
                return r[2]
        return self.M

    def get_movein(self, planet, seqs = []):
        movein = []
        for move in self.info["moves"]:
            if move[2] == planet and move[0] in seqs:
                    movein.append(move)

        return movein

    def compute_troopin(self, pl, seqs = [], rounds = None):
        if rounds == None:
            rounds = self.M
        if seqs == []:
            seqs = [self.info["holds"][pl][0]]

        movein = self.get_movein(pl, seqs)
        return sum([move[3] for move in movein if move[4] <= rounds])

    '''
    def compute_armyaround(self, pl, seqs = []):
        if seqs == []:
            seqs = [self.info["holds"][pl][0]]

        armyaround = 0
        for nb in self.get_neighbors(pl):
            if self.info["holds"][nb][0] in seqs:
                armyaround += self.info["holds"][nb][1]
        return armyaround
    '''

    def exp_env(self, pl, seqs = []):
    # weighted armyaround
        if seqs == []:
            seqs = [self.info["holds"][pl][0]]

        env = 0
        for nb in [i for i in self.get_neighbors(pl) if self.info["holds"][i][0] in seqs]:
            env += self.info["holds"][nb][1] / self.get_dist(nb, pl) ** 2
        return env

    def compute_defence(self, fr, rounds, acc = 0):
        dec = self.map["planets"][fr]["def"] 
        res = self.map["planets"][fr]["res"]
        cos = self.map["planets"][fr]["cos"]
        mam = self.map["planets"][fr]["max"]
        hold = self.info["holds"][fr][1]

        if hold > mam:
            return hold

        if acc == 0:
            acc = hold
        acc = min(mam, acc * res + cos)
        if rounds > 1:
            defence = self.compute_defence(fr, rounds - 1, acc)
        else:
            defence = dec * acc
        return defence

    def exp_doomday(self, pl):
        deff = self.exp_defence(pl, 1)
        moves = self.get_movein(pl, self.NOTME)
        moves = sorted(moves, key = lambda x: x[4])
        for move in moves:
            deff -= move[3]
            if deff < 0:
                return move[4], move[0]
        return self.M, self.me["seq"]

    def exp_defence(self, pl, rounds = None):
        dec = self.map["planets"][pl]["def"] 
        troopin = self.compute_troopin(pl, [self.info["holds"][pl][0]], rounds)
        return dec * troopin + self.compute_defence(pl, rounds)

    def exp_hold(self, pl, rounds = None):
        if rounds == None:
            rounds = self.M

        hold = self.info["holds"][pl][1]
        for move in self.info["moves"]:
            if move[2] == pl and move[0] == self.info["holds"][pl][0] and move[4] <= rounds:
                hold += move[3]
        return hold

    def compute_hub(self, planet):
        geo = 0
        for route in self.map["routes"]:
            if route[0] == planet and route[1] in self.myplanets and not self.plweights[route[1]][self.FLEE]:
                geo += 1
        return -geo

    def compute_geo(self, planet):  # 周围有更多我城
        oripl = set([pl for pl in self.myplanets if not self.plweights[pl][self.FLEE]]) - set([planet])
        exppl = oripl or set([planet])
        return len(self.get_frontiers(list(exppl))) - len(self.get_frontiers(list(oripl)))
        
    def compute_ext(self, planet):  # 周围有更多空城
        ext = 0
        for route in self.map["routes"]:
            if route[0] == planet and self.info["holds"][route[1]][0] == None:
                ext += 1
        return -ext


    def whether_transport(self, _from):
        small_hold = 150

        res = self.map["planets"][_from]["res"]
        cos = self.map["planets"][_from]["cos"]
        mam = self.map["planets"][_from]["max"]
        pos = self.plweights[_from][1]
        count = self.myplanets[_from]

        if self.plweights[_from][self.DANGER]:
            return False
        if pos == 1 and count >= mam and len(self.get_movein(_from, self.ME)) == 0 and len(self.get_movein(_from, self.NOTME)) == 0:
        # 前线调度
            return True
        if pos > 1 and res > 1 and count * res + cos >= 0.9 * mam:
            return True
        if pos > 1 and res <= 1 and count > min([small_hold - (pos - 2) * 30, mam * 2 / 3]):  
        # 运输：res 大的晚
            return True
        return False

    def where_transport(self, _from):
        pos = self.plweights[_from][1]

        dests = [self.plweights[i] for i in self.get_neighbors(_from) if i in self.myplanets]
        order = sorted(dests, key = lambda x: (x[1], self.compute_geo(x[0]), self.get_dist(_from, x[0]), -int(x[2]/100), -x[3]))  # 前线, 防高, 人多
        for wt in order:
            _to = wt[0]
            if not self.plweights[_to][self.DANGER] and len([i for i in self.roundmoves if i[2] == _to]) < 3 and len(self.get_movein(_to, self.NOTME)) == 0:
            #if not self.plweights[_to][self.DANGER]:
                return _to
        return None

    def amount_transport(self, _from):
        count = self.myplanets[_from]
        pos = self.plweights[_from][1]
        res = self.map["planets"][_from]["res"]
        cos = self.map["planets"][_from]["cos"]
        return min((res - 1) / res * count + cos + count * pos / 5, count * 9 / 10) # 越远越多

    def whether_dangerous(self, _from):
        atk = self.compute_troopin(_from, self.NOTME)
        if atk > self.exp_defence(_from, 1):
            return True
        return False

    def whether_flee(self, _from):
        ## Why same round 
        dec = self.map["planets"][_from]["def"]
        troopin = self.compute_troopin(_from, self.NOTME, 1)
        if self.exp_defence(_from, 2) < troopin:
            return True
        #if dec < 1 and self.exp_defence(_from, 2) < troopin / (dec + 0.1):  # def 越小越跑
        #    return True
        # ugly
        nbseqs = [self.info["holds"][i][0] for i in self.get_neighbors(_from)]
        if not None in nbseqs and not self.me["seq"] in nbseqs and len(self.get_movein(_from, self.ME)) == 0:
            return True
        return False

    def where_flee(self, _from):
        send = self.info["holds"][_from][1]

        _to = self.where_transport(_from)
        if _to != None:
            return _to

        _to = self.where_seize(_from, send)
        if _to != None and self.compute_hub(_to) <= -2:
            return _to

        _to = self.where_attack(_from, send)
        if _to != None and self.compute_hub(_to) <= -2:
            return _to

        return sorted([self.plweights[i] for i in self.get_neighbors(_from)], key = lambda x: (self.compute_hub(x[0]), x[2]))[0][0]

    def amount_attack(self, _from):
        dec = self.map["planets"][_from]["def"]

        maxhold = self.exp_hold(_from)
        atk = self.compute_troopin(_from, self.NOTME)
        hold = self.info["holds"][_from][1]

        # the less the def, the more out
        count = self.exp_defence(_from, 1) - atk - hold * dec * 0.4 + self.exp_env(_from, self.ME) - self.exp_env(_from, self.NOTME)
        return min(count, hold * 4 / 5)

    def where_seize(self, _from, send = 0):
        weights = [self.plweights[i] for i in self.get_neighbors(_from) if self.plweights[i][self.DANGER]]
        weakorder = sorted(weights, key = lambda x : (self.compute_geo(x[0]), self.compute_hub(x[0]), -x[4]))  # 地利，资高

        for wt in weakorder:
            _to = wt[0]
            if self.whether_seize(_from, _to, send):
                return _to
        return None

    def where_attack(self, _from, send = 0):
        neighbors = self.get_neighbors(_from)
        frweights = [self.plweights[i] for i in self.frontiers if i in neighbors]

        weakorder = sorted(frweights, key=lambda x : (self.compute_geo(x[0]), self.compute_hub(x[0]), int(self.frontiers[x[0]]/10), -x[4]))  # 地利，弱，资高

        for wt in weakorder:
            _to = wt[0]
            if self.whether_attack(_from, _to, send):
                return _to
        return None

    def is_enough(self, _to):
        already = len(self.get_movein(_to, self.ME))
        cround = len([i for i in self.roundmoves if i[2] == _to])
        if already >= 3:
            return True
        if cround >= 2:
            return True
        return False

    def whether_seize(self, _from, _to, send = 0):
        rounds, xseq = self.exp_doomday(_to)
        defc = self.map["planets"][_to]["def"]

        movein = self.get_movein(_to, self.NOTME)

        atk = self.compute_troopin(_to, self.NOTME) * 1.1 + self.exp_env(_to, self.NOTME)
        if atk < send and not self.is_enough(_to):
            if defc > 1 and self.get_dist(_from, _to) < rounds:
                self.plweights[_to][self.REIN] = True
                return True
            if defc < 1 and self.get_dist(_from, _to) > rounds + 1 and len(set([move[0] for move in movein])) == 1:
                return True
        return False

    def whether_attack(self, _from, _to, send = 0):
        defc = self.map["planets"][_to]["def"]

        moves = self.get_movein(_to, self.NOTME)
        moves = sorted(moves, key = lambda x: x[4])

        if len(moves) > 0:
            move = moves[0]
            move2 = moves[-1]
            #if (defc < 1 and self.get_dist(_from, _to) > move[4] and self.me["seq"] > move[0]) or (defc >= 1 and self.get_dist(_from, _to) < move[4] and self.me["seq"] > move[1]):
            if (defc < 1 and self.get_dist(_from, _to) > move2[4]) or (defc >= 1 and self.get_dist(_from, _to) < move[4]):
                pass
            else:
                return False

        deff = self.exp_defence(_to, self.get_dist(_from, _to)) * 1.1 + self.exp_env(_to) / 2
        if deff < send and not self.is_enough(_to):
            return True
        return False

    def update_moves(self, move):
        self.info["moves"] += [[self.me["seq"], move[1], move[2], move[0], self.get_dist(move[1], move[2])]]
        self.roundmoves.append(move)

    def race(self):
        racemoves = []

        for _from in self.myplanets:
            empty = [self.plweights[i] for i in self.get_neighbors(_from) if self.info["holds"][i][0] == None]
            count = self.myplanets[_from]
         
            for wt in sorted(empty, key=lambda x : (self.compute_ext(x[0]))):
                _to = wt[0]
                '''
                if len(self.get_movein(_to, self.NOTME)) > 0:
                    self.plweights[_to][self.DANGER] = True
                    continue
                '''
                if len(self.get_movein(_to, self.ME)) <= 2 and count > 1:
                    send = count * 2 / 3
                    count = count - send
                    racemoves.append([send, _from, _to])
                    self.update_moves([send, _from, _to])
                    
            self.myplanets[_from] = count

        #print 'race: ', moves
        return racemoves

    def attack(self):

        attackmoves = []

        for _from in self.myplanets:

            # dangerous planet should not attack
            if self.plweights[_from][self.DANGER]:
                continue

            send = self.amount_attack(_from)

            # seize
            _to = self.where_seize(_from, send)
            if _to != None:
                attackmoves.append([send, _from, _to])
                self.update_moves([send, _from, _to])
                self.myplanets[_from] -= send

            # invade
            _to = self.where_attack(_from, send)
            if _to != None:
                attackmoves.append([send, _from, _to])
                self.update_moves([send, _from, _to])
                self.myplanets[_from] -= send
                
        print 'attack', attackmoves
        return attackmoves

    def flee(self):
        fleemoves = []

        # find dangerous
        dangerous = []
        for _from in self.myplanets:
            if self.whether_dangerous(_from):
                self.plweights[_from][self.DANGER] = True
                dangerous.append(_from)

        # flee from
        flee = []
        for _from in self.myplanets:
            if self.whether_flee(_from):
                self.plweights[_from][self.FLEE] = True
                flee.append(_from)

        for _from in flee:
            _to = self.where_flee(_from)
            if _to != None:
                send = self.info["holds"][_from][1]
                fleemoves.append([send, _from, _to])
                self.update_moves([send, _from, _to])
                self.myplanets[_from] -= send

        print 'flee', fleemoves
        return fleemoves

    def deploy(self):

        deploymoves = []

        for _from in self.myplanets:
            if self.whether_transport(_from):
                _to = self.where_transport(_from)
                if _to != None:
                    send = self.amount_transport(_from)
                    deploymoves.append([send, _from, _to])
                    self.update_moves([send, _from, _to])
                    self.myplanets[_from] -= send

        deploymoves = sorted(deploymoves, key = lambda x: x[0], reverse = True)

        print 'deploy', deploymoves
        return deploymoves

    def init_round(self):
        self.roundmoves = []
        self.myplanets = self.get_myplanets()
        self.frontiers = self.get_frontiers()
        self.plweights = self.get_plweights()

    def step(self):

        self.init_round()

        moves = []
        moves = moves + self.flee()
        moves = moves + self.race()
        moves = moves + self.attack()
        moves = moves + self.deploy()

        print 'myplanets', self.myplanets
        print 'frontiers', self.frontiers
        print 'plweights', self.plweights

        print 'holds', self.info["holds"]
        print 'routes', self.map["routes"]
        print 'moves: ', self.info["moves"]


        print 'round moves: ', moves
        print 'total round moves: ', len(moves)
        return moves

    def is_restart(self):
        current_round = self.info['round']
        return True if current_round < 0 else False

def main(room = 0):
    player_nickname = 'yangchen'
    language = 'python' #ruby or python
    rs = SimpleAI(player_nickname, language, room)

    while True:
        #服务器每三秒执行一次，所以没必要重复发送消息
        time.sleep(1)
        #rs = SimpleAI(player_nickname, language)
        if rs.is_next_round():
            print 'round', ':', rs.round
            #计算自己要执行的操作
            result = rs.step()
            #把操作发给服务器
            rs.cmd_moves(result)
        '''
        try:
            #服务器每三秒执行一次，所以没必要重复发送消息
            time.sleep(1)
            #rs = SimpleAI(player_nickname, language)
            if rs.is_next_round():
                print 'round', ':', rs.round
                #计算自己要执行的操作
                result = rs.step()
                #把操作发给服务器
                rs.cmd_moves(result)
        except:
            continue
        '''

if __name__=="__main__":
    main()

