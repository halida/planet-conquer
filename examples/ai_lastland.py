#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
author: 梦里醉逍遥 <hnkfliyao@gmail.com>
module: ai_lastland
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
	self.name = ai_name
	self.side = side
	self.me = None
	self.cmd_add(self.name, self.side)
	self.init()

    def init(self):
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
	if not self.me and self.info['status'] == 'waitforplayer':
	    self.cmd_add(self.name, self.side)
	    self.init()

        current_round = self.info['round']
        next_round = False
        if current_round > self.round:
            self.round = current_round
            next_round = True
        return next_round

    def count_growth(self, planet_count, planet):
	max = planet['max']
	res = planet['res']
	cos = planet['cos']
	new_count = int(planet_count * res + cos)
	if planet_count < max:
	    planet_count = min(new_count, max)
	elif new_count < planet_count:
	    planet_count = new_count
	return planet_count

    def battle(self, move):
        side, _from, to, count, _round = move
        planet_side, planet_count = self.info['holds'][to]
        _def = self.map['planets'][to]['def']

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
        return planet_side, planet_count

    def get_myplanets(self):
	return [n for n, h in enumerate(self.info['holds']) if h[0] == self.me['seq']]

    def get_frontline_planets(self):
	routes = self.map['routes']
	my_planets = self.get_myplanets()
	frontlines = filter(lambda x:x[0] in my_planets and x[1] not in my_planets, routes)
	return [p[0] for p in frontlines]

    def get_dangerous_planets(self):
        moves = self.info['moves']
        my_planets = self.get_myplanets()
        dangerous = filter(lambda x:x[0] is not self.me['seq'] and x[2] in my_planets, moves)
	return dangerous

    def get_frontline_value(self, frontlines):
	value = dict()
	stack = []
	for p in frontlines:
	    value[p] = 0
	    for _from, _to, step in self.map['routes']:
		if _from == p and _to not in value:
		    value[_to] = 1
		    stack.append(_to)
	i = 0
	while i < len(stack):
	    for _from, _to, step in self.map['routes']:
		if _from == stack[i] and _to not in value:
		    value[_to] = value[stack[i]] + 1
		    stack.append(_to)
	    i += 1
	return value

    def count_after_n_steps(self, planet_id, n):
	moves = self.info['moves']
	owner, count = self.info['holds'][planet_id]
	for i in range(n):
	    # production
	    count = self.count_growth(count, self.map['planets'][planet_id])
	    for move in moves:
		if move[2] == planet_id and move[4] == i + 1:
		    print "%d将在%d回合后发生战斗！守方:%d, 进攻:%d" % (planet_id, i + 1, count, move[3])
		    owner, count = self.battle(move)
	    # reinforcements
	    #for seq, _, target, cnt, step in moves:
		#if target != planet_id or seq != owner or step != i:
		    #continue
		#count += cnt
	    # battle loss

	return owner, count

    def no_enermies_around(self, planet_id):
	for _from, _to in routes:
	    if _from == planet_id and _to in self.info['holds']:
		return false
	return  true


    def step(self):
	if self.info['status'] == 'finished' or self.info['status'] == 'waitforplayer':
	    print "游戏结束了"
	    self.me = None
	    return

        moves = []
        small_hold = 50
	frontlines = self.get_frontline_planets()
	dangerous = self.get_dangerous_planets()
	frontline_value = self.get_frontline_value(frontlines)
	
	dangerous_enermies = dict()

	for _, _, s, cnt, step in dangerous:
	    print s, cnt, step
	    if step == 1:
		if s not in dangerous_enermies:
		    dangerous_enermies[s] = cnt
		else:
		    dangerous_enermies[s] += cnt

	for s, cnt in dangerous_enermies.items():
	    my_cnt = self.info['holds'][s][1]
	    print "%d处于危险！我方：%d, 对方：%d" % (s, my_cnt, cnt)
	    if self.count_after_n_steps(s, 1)[0] == self.me['seq']:
		continue
	    print "打不过！"
	    # 打不过， 跑
	    sended = my_cnt
	    for route in self.map['routes']:
		_from, _to, step = route
		next_owner, next_cnt = self.count_after_n_steps(_to, step)
		if _from == s and (self.info['holds'][_to][0] == self.me['seq'] or next_cnt < sended): 
		    moves.append([sended, _from, _to])
		    self.info['holds'][s][1] -= sended 
		    break

        for i, s in enumerate(self.info['holds']):
            side, count = s
	    planet = self.map['planets'][i]
            # 寻找自己的星球
            if side != self.me['seq']:
                continue

	    # 援军把兵力运往前线
	    if i not in frontlines and i not in dangerous_enermies:
		sended = 0
		targets = []
		if planet['res'] <= 1:
		    sended = count - 1
		elif planet['max'] <= count or planet['res'] * count + planet['cos'] > planet['max']:
		    sended = count - (planet['max'] - planet['cos']) / planet['res']
		for _from, _to, step in self.map['routes']:
		    if self.count_after_n_steps(_to, step)[0] != self.me['seq']:
			continue
		    if _from == i and frontline_value[_to] < frontline_value[i]:
			targets.append(_to)
		if (len(targets) <= 0):
		    continue
		sended_each = int(sended / len(targets))
		if sended_each <= 0:
		    continue
		for t in targets:
		    moves.append([sended_each, i, t])
		    self.info['holds'][i][1] -= sended_each

            for route in self.map['routes']:
                # 数量超过一定程度的时候, 才派兵
                if count < small_hold:
                    break
                sended = int(count * 0.6)
                # 当前星球的路径, 并且对方星球不是自己的星球
                _from, to, step = route
		owner_of_to, count_of_to = self.count_after_n_steps(to, step)
                if _from != i or self.info['holds'][to][0] == self.me['seq']:
                    continue
		if count < planet['max'] and (owner_of_to == self.me['seq'] or count_of_to >= sended):
		    continue
		if count_of_to >= sended: 
		    sended = int(count - (planet['max'] - planet['cos']) / planet['res'])

                # 派兵!
                moves.append([sended, _from, to])
                count -= sended

        return moves

    def is_restart(self):
        current_round = self.info['round']
        return True if current_round < 0 else False

def main(room=0):
    player_nickname = 'lastland'
    language = 'python' #ruby or python
    rs = SimpleAI(player_nickname, language)
    while True:
        #服务器每三秒执行一次，所以没必要重复发送消息
        time.sleep(1)
        #rs = SimpleAI()
        if rs.is_next_round():
            #计算自己要执行的操作
            result = rs.step()
            #把操作发给服务器
            rs.cmd_moves(result)

if __name__=="__main__":
    main()
