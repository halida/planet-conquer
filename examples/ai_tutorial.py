#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
module: ai_tutorial
"""
import json, time
import urllib, httplib, logging

logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s - %(levelname)s - %(message)s")

SERVER = "localhost"
PORT = 9999
DIRS = [[-1, 0], [0, -1], [1, 0], [0, 1]]

class SimpleAI():
    def __init__(self, ai_name, side='python'):
        self.conn = httplib.HTTPConnection(SERVER, PORT)
        self.room = 0
        self.d = 0
        #加入房间
        self.cmd_add(ai_name, side)
        #获取地图
        self.cmd_map()
        #更新地图信息
        self.cmd_info()

        #得到当前的回合
        self.round = self.info['round']

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
        self.me = self.cmd("add",
                           dict(name=ai_name, side=side))
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
    def is_next_round(self):
        self.cmd_info()
        current_round = self.info['round']
        next_round = False
        if current_round > self.round:
            self.round = current_round
            next_round = True
        return next_round

    def step(self):
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
                if _from != i or self.info['holds'][to][0] == self.me['seq']:
                    continue

                # 派兵!
                moves.append([sended, _from, to])
                count -= sended

        return moves

    def is_restart(self):
        current_round = self.info['round']
        return True if current_round < 0 else False

def main():
    player_nickname = 'tutorial'
    language = 'python' #ruby or python
    rs = SimpleAI(player_nickname, language)
    while True:
        #服务器每三秒执行一次，所以没必要重复发送消息
        time.sleep(1)
        rs = SimpleAI()
        if rs.is_next_round():
            #计算自己要执行的操作
            result = rs.step()
            #把操作发给服务器
            rs.cmd_moves(result)

if __name__=="__main__":
    main()
