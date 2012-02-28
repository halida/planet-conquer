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
                           dict(name = "SimplePython"))
        return self.me
    
    def cmd_map(self):
        self.map = self.cmd("map")

    def cmd_info(self):
        self.info = self.cmd("info")

    def cmd_moves(self, moves):
        return self.cmd("move",
                        dict(id = self.me["id"],
                             moves = moves))

    def step(self):
        return []


def main():
    rs = SimpleAI()
    rs.cmd_map()
    logging.debug(rs.cmd_add())
    while True:
        time.sleep(0.3)
        rs.cmd_info()
        result = rs.step()
        rs.cmd_moves(result)
        logging.debug(result)
    
if __name__=="__main__":
    main()



