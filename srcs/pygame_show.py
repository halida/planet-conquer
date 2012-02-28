#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
module: pygame_show
用pygame来显示逻辑..
"""
from lib import *
import pygame

SIZE = 40

def random_planet_color():
    return (random.randint(120, 225), random.randint(120, 225), random.randint(120, 225))

def random_player_color():
    return (random.randint(0, 120), random.randint(0, 120), random.randint(0, 120))

class Shower():
    def __init__(self, map):
        pygame.init()
        self.font = pygame.font.SysFont('sans', 12)
        self.set_map(map)
        self.player_colors = []

    def set_map(self, map):
        print map
        self.map = map
        size = self.map['map_size']
        self.screen = pygame.display.set_mode(
            (size[0]*SIZE, size[1]*SIZE))
        for s in self.map['planets']:
            s['color'] = random_planet_color()

    def flip(self, info):
        print info
        # 退出判断
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

        # 给玩家加颜色
        while len(info['players']) > len(self.player_colors):
            self.player_colors.append(random_player_color())
        
        size = SIZE
        def drawRect(c, x, y, w, h):
            pygame.draw.rect(self.screen, c,
                             pygame.Rect(x, y, w, h))
        def drawCircle(c, pos):
            pygame.draw.circle(self.screen, c,
                               (pos[0]*SIZE+SIZE/2, pos[1]*SIZE+SIZE/2), SIZE/2)
        
        # draw map background
        self.screen.fill((200,200,200))
        
        # planets
        for i, s in enumerate(self.map['planets']):
            pos = s['pos']
            drawCircle(s['color'], s['pos'])
            
        # players
        for i, s in enumerate(info['holds']):
            print s
            sur = self.font.render(s[2], True, self.player_colors[s[0]])
            planet_pos = self.map['planets'][i[1]]['pos']
            self.screen.blit(sur,
                             (planet_pos[0]*SIZE,
                              planet_pos[1]*SIZE))
            
        pygame.display.flip()


def pygame_testai(ais):
    """
    输入ai列表, 跑一个pygame的测试游戏看看
    """
    from snake_game import Game
    from game_controller import Controller
    
    game = Game()
    c = Controller(game)
    m = c.map()
    for ai in ais:
        ai.setmap(m)
        result = c.add(ai.name, ai.type)
        ai.seq = result['seq']
        ai.id = result['id']

    clock = Clock(3)
    s = Shower(m)

    while True:
        clock.tick()
        
        info = c.info()
        for ai in ais:
            d = ai.onprocess(info)
            c.turn(ai.id, d, game.round)
        game.step()

        s.flip(info)


def main():
    from ai_simple import AI
    ais = [AI() for i in range(20)]
    pygame_testai(ais)

    
if __name__=="__main__":
    main()
