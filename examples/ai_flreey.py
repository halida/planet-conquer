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
                           dict(name = "Flreey", side='python'))
        return self.me
    
    def cmd_map(self):
        self.map = self.cmd("map")

    def cmd_info(self):
        self.info = self.cmd("info")

    def cmd_moves(self, moves):
        return self.cmd("moves",
                        dict(id = self.me["id"],
                             moves = moves))

    def step(self):
        #anemy = filter(lambda x: x[0] != self.me['seq'], self.info['holds'])
        #print anemy, sorted(anemy)
        #moves = []
        #sended = 20
        #small_hold = 50
        #for i, s in enumerate(self.info['holds']):
            #side, count = s
            ## 寻找自己的星球
            #if side != self.me['seq']:
                #continue

            #for route in self.map['routes']:
                ## 数量超过一定程度的时候, 才派兵
                #if count < small_hold:
                    #break
                ## 当前星球的路径, 并且对方星球不是自己的星球
                #_from, to, step = route
                #if _from != i or self.info['holds'][to] == self.me['seq']:
                    #continue
                ## 派兵!
                #moves.append([sended, _from, to])
                #count -= sended

        #print 'moves', moves
        #return moves

        moves = []
        small_hold = 50
        for i, s in enumerate(self.info['holds']):
            side, count = s
            # 寻找自己的星球
            if side != self.me['seq']:
                continue

            for route in self.map['routes']:
                # 数量超过一定程度的时候, 才派兵
                if count < small_hold:
                    break
                sended = count / 2
                # 当前星球的路径, 并且对方星球不是自己的星球
                _from, to, step = route
                if _from != i or self.info['holds'][to] == self.me['seq']:
                    continue
                # 派兵!
                moves.append([sended, _from, to])
                count -= sended

        return moves

def main():
    rs = SimpleAI()
    rs.cmd_map()
    logging.debug(rs.cmd_add())
    while True:
        time.sleep(1.0)
        rs.cmd_info()
        result = rs.step()
        rs.cmd_moves(result)
    
if __name__=="__main__":
    main()



