#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
module: ai_halida
"""
import json, time
import urllib, httplib, logging

logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s - %(levelname)s - %(message)s")

SERVER = "localhost"
PORT = 9999
DIRS = [[-1, 0], [0, -1], [1, 0], [0, 1]]

class SimpleAI():
    def __init__(self):
        self.conn = httplib.HTTPConnection(SERVER, PORT)
        self.room = 0
        self.d = 0

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

    def cmd_add(self):
        self.me = self.cmd("add",
                           dict(name = "Flreey", script='python'))
        return self.me
    
    def cmd_map(self):
        self.map = self.cmd("map")

    def cmd_info(self):
        self.info = self.cmd("info")

    def cmd_moves(self, moves):
        print self.me, moves
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
            planet['weight'] = (planet['res'] * 0.3 + planet['cos'] * 0.2 +
                    planet['def'] * 0.3 + planet['max'] * 0.2)

        for n, hold in enumerate(self.info['holds']):
            if not hold[0]:
                planets[n]['weight'] *= 2

        return sorted(
                [(n, p['weight']) for n, p in enumerate(planets)],
                key=lambda x:x[1])

    def get_best_planets(self, planets, weight):
        """
        return planets pairs, [(1, 2, 2)] means
        would move armies from planet 1 to 2 and round is 2
        """
        adjacency_planets = {}
        [adjacency_planets.setdefault(p, [])  for p in planets]

        for r in self.map['routes']:
            if r[0] in planets:
                adjacency_planets[r[0]].append([r[1], r[2]])

        pairs = []
        #fight with enemy
        for planet_id, planet_weight in weight:
            for pid, ad_pids in adjacency_planets.iteritems():
                pids = [p[0] for p in ad_pids]
                if planet_id in pids:
                    pairs.append([
                        pid, planet_id,
                        ad_pids[pids.index(planet_id)][1]
                        ])

        #random to reinforece armies
        fight_armies = [p[0] for p in pairs]
        idle_armies = set(planets).difference(fight_armies)
        import random
        for idle in idle_armies:
            pairs.append(idle,
                    fight_armies[random.randint(0, len(fight_armies)-1)], -1)

        return pairs

    def cal_new_acount(self, current, planet, round):
        if round <= 0:
            return current if current < planet['max'] else planet['max']
        return self.cal_new_acount(
                int(current * planet['res'] + planet['cos']),
                planet, round -1)

    def move(self, pairs):
        holds = self.info['holds']
        planets = self.map['planets']
        moves = []
        for me, anemy, round in pairs:
            my_armies = holds[me][1]
            if round == -1:
                moves.append([int(holds[me][1] * 2.0 / 3), me, anemy])
                print 'reinforece', moves
                continue

            enemy_armies = self.cal_new_acount(holds[anemy][1], planets[anemy],
                    round)
            if my_armies > enemy_armies:
                send_armies = int(enemy_armies + (my_armies - enemy_armies) / 2.0)
                moves.append([send_armies, me, anemy])
                holds[me][1] -= send_armies

        return moves

    def step(self):
        weight = self.cal_weight()
        my_planets = [n for n, h in enumerate(self.info['holds']) if h[0] ==
                self.me['seq']]
        plants_pair = self.get_best_planets(my_planets, weight)
        return self.move(plants_pair)

def main():
    rs = SimpleAI()
    rs.cmd_map()
    logging.debug(rs.cmd_add())
    rs.init_weight()

    while True:
        time.sleep(1.0)
        rs.cmd_info()
        result = rs.step()
        print result
        rs.cmd_moves(result)

if __name__=="__main__":
    main()



