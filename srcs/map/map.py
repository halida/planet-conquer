#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
module: map
"""
import yaml, string, random

class Map:
    # planet tokens
    planet_tokens = string.uppercase + string.lowercase

    def __init__(self):
        # default meta
        self.meta = dict(
            name = 'unknown',
            author = 'none',
            version = 1.0,
            max_round = 3000,
            start_unit = 100,
            max_player = 4,
            min_player = 2,
            )
        
    @staticmethod
    def loadfile(filename):
        data = yaml.load(open(filename).read())
        return Map.loaddata(data)

    @staticmethod
    def loaddata(data):
        map = Map()
        map.load(data)
        return map

    def __getattr__(self, name):
        return self.meta[name]
    
    def load(self, data):
        for key in data:
            self.meta[key] = data[key]
        # planets data
        self.planets = self.meta['planets'].items()
        self.planets.sort()
        self.planet_name_to_id = dict([(i[0], c)
                                       for c, i in enumerate(self.planets)])
        self.planets = [i[1] for i in self.planets]
        # set planet location
        x, y = 0, 0
        map = self.meta['map'].strip().split("\n")
        for line in map:
            x = 0
            for c in line:
                if c in self.planet_tokens:
                    id = self.planet_name_to_id[c]
                    self.planets[id]['pos'] = (x, y)
                x += 1
            y += 1
        self.map_size = (len(map[0]), len(map))
        
        # route data
        self.routes = {}
        for _from, to, step in self.meta['routes']:
            from_id = self.planet_name_to_id[_from]
            to_id   = self.planet_name_to_id[to]
            self.routes[(from_id, to_id)] = step
            self.routes[(to_id, from_id)] = step
        # only for transport to client
        self.seq_routes = [(t[0], t[1], step)
                           for t, step in self.routes.items()]
                       
        self.starts = [self.planet_name_to_id[name]
                       for name in self.meta['starts']]
        random.shuffle(self.starts)
        
def test():
    """
    >>> map = Map.loadfile("srcs/map/test.yml")
    >>> map.planets
    [{'res': 1, 'cos': 10, 'pos': (0, 0), 'def': 2, 'max': 1000}, {'res': 1, 'cos': 10, 'pos': (4, 0), 'def': 2, 'max': 1000}, {'res': 1, 'cos': 10, 'pos': (0, 4), 'def': 2, 'max': 1000}, {'res': 1, 'cos': 10, 'pos': (4, 4), 'def': 2, 'max': 1000}, {'res': 1.5, 'cos': 0, 'pos': (2, 2), 'def': 0.5, 'max': 300}]
    >>> map.starts
    [0, 1, 2, 3]
    """
    import doctest
    doctest.testmod()

if __name__=="__main__":
    test()
