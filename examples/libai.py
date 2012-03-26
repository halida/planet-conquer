# -*- coding:utf-8 -*- #

import urllib, httplib, json

class Server(object):
    """docstring for Server"""
    def __init__(self):
        pass

    def _cmd(self, cmd, data={}):
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

    def add_player(self, ai_name, language):
        return self._cmd("add", dict(name=ai_name, side=language))

    def get_map(self):
        return self._cmd("map")

    def get_info(self):
        return self._cmd('info')

    def is_next_round(self):
        pass
