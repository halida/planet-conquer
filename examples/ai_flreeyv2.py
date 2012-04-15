#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
module: ai_flreeyv2
"""
import json, time
import urllib, httplib, logging

logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s - %(levelname)s - %(message)s")

SERVER = "localhost"
PORT = 9999
DIRS = [[-1, 0], [0, -1], [1, 0], [0, 1]]

class SimpleAI():
    def __init__(self, ai_name, side='python', room=0):
        self.conn = httplib.HTTPConnection(SERVER, PORT)
        self.room = room
        self.d = 0
        self.name = ai_name
        self.side = side
        self.me = None
        self.round = None

    def init(self):
        #获取地图
        self.cmd_map()
        #更新地图信息
        self.cmd_info()

        #得到当前的回合
        self.round = self.info['round']
        self.init_weight()

    def is_next_round(self):
        self.cmd_info()
        if not self.me and self.info['status'] == 'waitforplayer':
            self.cmd_add()
            self.init()

        # if not self.round: return
        current_round = self.info['round']
        next_round = False
        if current_round > self.round:
            self.round = current_round
            next_round = True
        return next_round

    def is_restart(self):
        current_round = self.info['round']
        return True if current_round < 0 else False


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
        # logging.debug(result)
        return json.loads(result)

    def cmd_add(self):
        result = self.cmd("add",
                          dict(name = self.name, side=self.side))
        if result.has_key('id'):
            self.me = result
            return self.me
    
    def cmd_map(self):
        self.map = self.cmd("map")

    def cmd_info(self):
        self.info = self.cmd("info")

    def cmd_moves(self, moves):
        #print self.me, moves
        return self.cmd("moves",
                        dict(id = self.me["id"],
                             moves = moves))

    def init_weight(self):
        all_res = 0
        all_cos = 0
        all_def = 0
        all_max = 0
        for planet in self.map['planets']:
            all_res += planet['res'] * 1.0
            all_cos += planet['cos'] * 1.0
            all_def += planet['def'] * 1.0
            all_max += planet['max'] * 1.0
        self.planets = [p.copy() for p in self.map['planets']]
        for planet in self.planets:
            planet['res'] /= all_res
            planet['cos'] /= all_cos
            planet['def'] /= all_def
            planet['max'] /= all_max

    def cal_weight(self):
        planets = [p.copy() for p in self.planets]

        for planet in planets:
            planet['weight'] = (planet['res'] * 0.5 + planet['cos'] * 0.1 +
                    planet['def'] * 0.2 + planet['max'] * 0.2)

        for n, hold in enumerate(self.info['holds']):
            if hold[0] is None:
                planets[n]['weight'] *= 1.1

        #TODO: if planets near by high resources, acc it's weight
        return sorted(
                [(n, p['weight']) for n, p in enumerate(planets)],
                key=lambda x:x[1])

    def get_adjacency_planets(self, planet_ids):
        adjacency_planets = {}
        [adjacency_planets.setdefault(p, [])  for p in planet_ids]

        for r in self.map['routes']:
            if r[0] in planet_ids and r[0] != r[1]:
                adjacency_planets[r[0]].append([r[1], r[2]])
        return adjacency_planets

    def get_round(self, start, end):
        for r in self.map['routes']:
            if r[0] == start and r[1] == start:
                return r[3]

    def get_best_planets(self, planets, weight):
        """
        return planets pairs, [(1, 2, 2)] means
        would move armies from planet 1 to 2 and round is 2
        """
        adjacency_planets = self.get_adjacency_planets(planets)
        adjacency_planets_copy = adjacency_planets.copy()
        pairs = []
        slow_down_conquer = False

        if len(self.get_myplanets()) >= len(self.info['holds']):
            slow_down_conquer = True

        dangerous = self.would_be_attacked()
        fighting_armies = []

        #conquer planet
        for colony_planet_id, planet_weight in weight:
            keys = adjacency_planets.keys()
            for k in keys:
                pid = k
                if pid in dangerous:
                    fighting_armies.insert(0, pid)
                    #continue
                ad_info = adjacency_planets[k]
                adjacency_pids = [p[0] for p in ad_info]
                if (colony_planet_id in adjacency_pids and colony_planet_id not
                in planets):
                    pairs.append([
                        pid, colony_planet_id,
                        ad_info[adjacency_pids.index(colony_planet_id)][1]
                        ])
                    #only get once in this step
                    #if slow_down_conquer:
                        #adjacency_planets.pop(pid)

        #random to reinforece armies
        fighting_armies.extend([p[0] for p in pairs])
        idle_armies = set(planets).difference(fighting_armies)

        for idle in idle_armies:
            ad_info = adjacency_planets_copy[idle]
            adjacency_pids = [p[0] for p in ad_info]
            planet_needed_help = set(fighting_armies).intersection(adjacency_pids)
            if planet_needed_help:
                pairs.append([idle, planet_needed_help.pop(), -1])
            else:
                #get_nearest_planet(idle, fighting_armies)
                #dijkstra(idle, fighting_armies
                #TODO: get the paths to nearelest planet 
                pairs.append([idle, sorted(adjacency_pids, reverse=True)[0], -1])

        return pairs

    def cal_new_acount(self, current, planet, round):
        if round <= 0:
            current if current < planet['max'] else planet['max']
            current = current * planet['def']
            return current
        return self.cal_new_acount(
                int(current * planet['res'] + planet['cos']),
                planet, round -1)

    def move(self, pairs):
        holds = self.info['holds']
        planets = self.map['planets']
        moves = []
        for me, anemy, round in pairs:
            my_armies = holds[me][1]

            #reinforece my planets
            if round == -1:
                send = int(my_armies * 2.0 / 3)
                holds[me][1] -= send
                moves.append([send, me, anemy])
            #conquer planets
            else:
                send_armies = 0
                if holds[anemy][0] is None:
                    #not conquer empty planets until enemy planets which is
                    #near empyt planet less than 2
                    enemy_planets_nearby_my_planet = self.get_nearby_anemies(me)
                    armies_less_than_my_planets = filter(lambda
                            x:self.cal_new_acount(holds[x][1], planets[x],
                                self.get_round(me, x)) >
                            holds[x][1], enemy_planets_nearby_my_planet)
                    if enemy_planets_nearby_my_planet:
                        #print 'enemy_planets_nearby_my_planet', enemy_planets_nearby_my_planet, armies_less_than_my_planets
                        if armies_less_than_my_planets:
                            anemy = armies_less_than_my_planets[0]
                            send_armies = int(holds[anemy][1] + (my_armies -
                                holds[anemy][1]) / 2.0)
                    else:
                        send_armies = int(my_armies * 2.0 / 3)
                else:
                    enemy_armies = self.cal_new_acount(holds[anemy][1], planets[anemy],
                            round)
                    if my_armies > enemy_armies:
                        send_armies = int(enemy_armies + (my_armies - enemy_armies) / 2.0)

                moves.append([send_armies, me, anemy])
                holds[me][1] -= send_armies

        return moves

    def would_be_attacked(self):
        moves = self.info['moves']
        my_planets = self.get_myplanets()
        dangerous = filter(lambda x:x[0] is not self.me['seq'] and x[2] in
                my_planets, moves)
        #if planet weight is hight and has anemy nearby 
        #assert it would be attacked
        #only need top 4 planet
        #top4 = [w[0] for w in self.cal_weight()[0:4]]
        #warning_planets = filter(lambda x:x in my_planets, top4)
        #s = set()
        #[s.update(self.get_nearby_anemies(p)) for p in warning_planets]
        #dangerous.extend(list(s))
        return dangerous



        return [d[2] for d in dangerous]

    def get_nearby_anemies(self, planet):
        ps = self.get_adjacency_planets([planet])
        holds = self.info['holds']
        return filter(lambda x:holds[x][0] is not self.me['seq'] and holds[x][0]
                is not None,
                [adinfo[0] for adinfo in ps[planet]])

    def get_myplanets(self):
        return [n for n, h in enumerate(self.info['holds']) if h[0] ==
                self.me['seq']]
    def step(self):
        if self.info['status'] == 'finished' or self.info['status'] == 'waitforplayer':
            self.me = None
            return
        weight = self.cal_weight()
        my_planets = self.get_myplanets()
        plants_pair = self.get_best_planets(my_planets, weight)
        return self.move(plants_pair)

def main(room=0):
    rs = SimpleAI('flreeyv2', 'python', room)

    while True:
        #服务器每三秒执行一次，所以没必要重复发送消息
        #time.sleep(0.1)
        #rs = SimpleAI('flreeyv2', 'python')
        #start = time.time()
        ##计算自己要执行的操作
        ##print timeit.timeit(rs.step)
        #result = rs.step()
        #print time.time() - start, rs.info['round'], result
        ##把操作发给服务器
        #rs.cmd_moves(result)
        time.sleep(1.4)
        
        if rs.is_next_round():
            start = time.time()
            #计算自己要执行的操作
            #print timeit.timeit(rs.step)
            result = rs.step()
            if not result: continue

            print time.time() - start, rs.info['round'], result
            #把操作发给服务器
            rs.cmd_moves(result)

if __name__=="__main__":
    main()



