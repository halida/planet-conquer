import sys
from random import randint
import math

planet_string = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+-*/!@#$%"

def main():
    
    map_name = sys.argv[1]
    planet_count = int(sys.argv[2])
    map_size = int (sys.argv[3])

    if map_size % 2 != 1:
        return

    fout = open(map_name + ".yml", "w")

    print >> fout, "name:", map_name
    print >> fout, """desc: auto generated map
author: generator(resty)
version: 0.1

max_round: 2000
max_player: 4
start_unit: 100
"""


    mid = int(map_size / 2)

    map = []
    for x in range(map_size):
        map.append([-1] * map_size)
    ed = []
    for x in range(map_size):
        ed.append([False] * map_size)

    ls = int(map_size / 2)
    planets = []
    for i in range(int(planet_count / 4) + 1):
        pos = [randint(0, ls), randint(0, ls)]
        if not pos in planets:
            planets.append(pos)

    start_id = randint(0, len(planets) - 1)
    print >> fout, """starts:
  - %s
  - %s
  - %s
  - %s
""" % (planet_string[start_id],
       planet_string[start_id + len(planets)],
       planet_string[start_id + 2 * len(planets)],
       planet_string[start_id + 3 * len(planets)])
    print >> fout, "planets:"
    for (i,p) in enumerate(planets):
        x = randint(0,5)
        if x == 0:
            def_ = 1.2
            res = 0.9
            cos = 0
            max = 1000
        elif x == 1:
            def_ = 0.3
            res = 1.5
            cos = 2
            max = 300
        else:
           def_ = 1.2
           res = 1
           cos = 5
           max = 1000
         
        if i == start_id:
            def_ = 1.5
            res = 1.4
            cos = 5
            max = 2000
        for k in xrange(4):
            print >> fout, "  %s:" % planet_string[i + k * len(planets)]
            print >> fout,"""    def: %.1f
    res: %f
    cos: %d
    max: %d""" % (def_, res, cos, max)
        ms = map_size - 1
        map[p[0]][p[1]] = i
        map[p[1]][ms- p[0]] = i + len(planets)
        map[ms - p[0]][ms - p[1]] = i + 2 * len(planets)
        map[ms - p[1]][p[0]] = i + 3 * len(planets)
        
    mid_planet = 4 * len(planets)
    map[mid][mid] = mid_planet
    print >> fout, "  %s:" % planet_string[mid_planet]
    print >> fout, """    def: 0.3
    res: 2
    cos: 20
    max: 400
"""

    print >> fout, "map: |"
    for i in xrange(map_size):
        s = "  "
        
        for j in xrange(map_size):
            if map[i][j] == -1:
                s += '.'
            else:
                s +=  planet_string[map[i][j]]
        print >> fout, "%s" % s

    mm = 100000000
    mi = -1
    for (i, p) in enumerate(planets):
        dist = abs(p[0] - mid) + abs(p[1] - mid)
        if dist < mm:
            mm = dist
            mi = i

    bd = int(dist / 3)
    print >> fout, "\nroutes:"
    
    for (i, p) in enumerate(planets):
        dist = abs(p[0] - mid) + abs(p[1] - mid)
        if (int(dist/3) == bd):
            for k in xrange(4):
                print >> fout, """  - - %s
    - %s
    - %d""" % ( planet_string[i + k * len(planets)], planet_string[mid_planet], int(dist / 2) + 1)
    sqr = lambda x : x*x
    for (i, p) in enumerate(planets):
        mm = 100000000000
        mj = -1
        for (j, q) in enumerate(planets):
            dist = sqr(p[0]-q[0]) + sqr(p[1]-q[1])
            if i!=j and dist < mm:
                mm = dist
                mj = j
        for k in range(4):
            print >> fout, """  - - %s
    - %s
    - %d""" % (planet_string[i + k * len(planets)],
               planet_string[mj + k * len(planets)],
               int(math.sqrt(mm)) + 1)
    
    fout.close()
    

    

main()
