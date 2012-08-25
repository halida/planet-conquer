#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
module: ai_halida
"""
import json, time, random
import urllib, httplib, logging

logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s - %(levelname)s - %(message)s")

SERVER = "localhost"
PORT = 9999
DIRS = [[-1, 0], [0, -1], [1, 0], [0, 1]]

class SimpleAI():
    def __init__(self, room):
        self.conn = httplib.HTTPConnection(SERVER, PORT)
        self.room = room
        self.d = 0

    def cmd(self, cmd, data={}):
        """
        发送命令给服务器
        """
        data['op'] = cmd
        data['room'] = self.room
        # logging.debug('post: %s : %s', cmd, data)
        self.conn.request("POST", '/cmd',
                          urllib.urlencode({'data': json.dumps(data)}),
                          {'Content-Type': 'application/x-www-form-urlencoded'})
        result = self.conn.getresponse().read()
        return json.loads(result)

    def cmd_add(self):
        self.me = self.cmd("add",
                           dict(name = "halida",
                                side='python'))
        if not self.me.has_key('seq'): return
        
        self.user_id = self.me['seq']
        return self.me
    
    def cmd_map(self):
        self.map = self.cmd("map")

    def cmd_info(self):
        self.info = self.cmd("info")

    def step(self):
        moves = []
        small_hold = 10
        cs = [(i, s) for i, s in enumerate(self.info['holds'])]
        random.shuffle(cs)
        for i, s in cs:
        # for i, s in enumerate(self.info['holds']):
            side, count = s
            # 寻找自己的星球
            if side != self.user_id: continue

            for route in self.map['routes']:
                # # 数量超过一定程度的时候, 才派兵
                if count < small_hold:
                    break
                # 当前星球的路径, 并且对方星球不是自己的星球
                _from, to, step = route
                if _from != i or self.info['holds'][to][0] == self.user_id:
                    continue

                if self.info['holds'][to][1] > count:
                    continue
                # 派兵!
                moves.append([count/2, _from, to])
                count -= count/2

        move = dict(id = self.me["id"], moves = moves)

        tactic = self.choose_tactic()
        if tactic:
            move['tactic'] = tactic
            
        print move
        return self.cmd("moves", move)

    def choose_tactic(self):
        # check can use terminator
        if self.info['players'][self.user_id]['points'] < 2: return
        
        # get max unit player
        target_player = None
        target_count = 0
        for i, player in enumerate(self.info['players']):
            if i == self.user_id: continue
            if player["units"] < target_count: continue
            target_player = i
            target_count = player["units"]
                
        if target_player == None: return
        
        # random planet
        ps = [ i
               for i, v in enumerate(self.info["holds"])
               if v[0] == target_player
               ]
        if len(ps) <= 0: return
        planet = ps[random.randint(0, len(ps)-1)]
        return dict(type='terminator', planet=planet)

    def is_restart(self):
        current_round = self.info['round']
        return True if current_round < 0 else False

def main(room=0):
    while True:
        time.sleep(3)
        rs = SimpleAI(room)
        rs.cmd_map()
        
        if not rs.cmd_add(): next
        
        while True:
            time.sleep(1.0)
            rs.cmd_info()
            if rs.info['status'] == 'finished': break
            try:
                result = rs.step()
                print result
                if result['status'] == 'noid': break
            except:
                raise
    
if __name__=="__main__":
    main()



