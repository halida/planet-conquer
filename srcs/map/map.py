#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
module: map
"""
import yaml, string

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
        # route data
        self.routes = {}
        for _from, to, step in self.meta['routes']:
            from_id = self.planet_name_to_id[_from]
            to_id   = self.planet_name_to_id[to]
            self.routes[(from_id, to_id)] = step
            self.routes[(to_id, from_id)] = step
                       
        self.starts = [self.planet_name_to_id[name]
                       for name in self.meta['starts']]
        
def test():
    """
    >>> map = Map.loadfile("srcs/map/test.yml")
    >>> map.planets
    [{'res': 1, 'cos': 10, 'def': 2, 'max': 1000}, {'res': 1, 'cos': 10, 'def': 2, 'max': 1000}, {'res': 1, 'cos': 10, 'def': 2, 'max': 1000}, {'res': 1, 'cos': 10, 'def': 2, 'max': 1000}, {'res': 1.5, 'cos': 0, 'def': 0.5, 'max': 300}]
    >>> map.starts
    [0, 1, 2, 3]
    """
    import doctest
    doctest.testmod()

if __name__=="__main__":
    test()
