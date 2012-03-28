import os, sys, time
from multiprocessing import Process, Queue

class Logger(object):
    def __init__(self, name):
        if not os.path.exists('log'):
            try:
                os.mkdir('log')
            except OSError:
                print 'can\'t make dir log'
                sys.exit(1)
        self.f = open(os.path.join('log', name), 'w')

    def write(self, s):
        self.f.write(s)
        self.f.flush()

    def __del__(self):
        self.f.close()

    def flush(self):
        self.f.flush()

def start_game(q):
    from srcs.zmq_game_server import Server
    sys.stdout = Logger('game.log')
    from srcs.lib import GEME_STEP_TIME
    Server().run(max_waits=GEME_STEP_TIME,
                 min_waits=GEME_STEP_TIME,
                 enable_no_resp_die=False,
                 msg_queue=q)

def start_http():
    from srcs.web_server import main
    sys.stdout = Logger('http.log')
    #application.settings['debug'] = False
    #application.listen(9999)
    #try:
        #ioloop.IOLoop.instance().start()
    #except KeyboardInterrupt:
        #print "bye!"

    main()

def start_ai(name, roomid):
    ai = __import__('examples.%s' % name, globals(), locals(), ['main'])
    sys.stdout = Logger('%s.log' % name)
    ai.main(roomid)

def start_brower():
    import webbrowser
    webbrowser.GenericBrowser('google-chrome').open('./website/build/room_0.html')

def start_room(roomid, rooms):
    ais = rooms.get(roomid)[0]
    ps = rooms.get(roomid)[1]
    if ps:
        stop_room(roomid, rooms)
    else:
        [ps.append(Process(target=start_ai, args=(ai, roomid))) for ai in ais]
        [p.start() for p in ps]

def stop_room(roomid, rooms):
    ps = rooms[roomid][1]
    [r.terminate() for r in ps]

def run_all():
    ps = []
    q = Queue()
    ps.append(Process(target=start_game, args=(q,)))
    ps.append(Process(target=start_http))
    # ps.append(Process(target=start_brower))

    for p in ps:
        time.sleep(1)
        p.start()

    rooms = {0: [['ai_flreeyv2', 'ai_flreeyv2', 'ai_flreeyv2', 'ai_flreeyv2'], []]}
    # rooms.update({1: [['ai_flreeyv2', 'ai_flreeyv2'], []]})
    start_room(0, rooms)
    #start_room(1, rooms)

    while True:
        try:
            roomid = q.get()
            stop_room(roomid, rooms)
            time.sleep(3)
            start_room(roomid, rooms)
        except KeyboardInterrupt:
            break

def kill_all():
    pass

def main():
    run_all()

if __name__ == '__main__':
    main()
