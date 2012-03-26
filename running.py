import os, sys, time
from multiprocessing import Process

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

def start_game():
    from srcs.zmq_game_server import Server
    sys.stdout = Logger('game.log')
    from srcs.lib import GEME_STEP_TIME
    Server().run(max_waits=GEME_STEP_TIME,
                 min_waits=GEME_STEP_TIME,
                 enable_no_resp_die=False)

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

def start_ai(name):
    ai = __import__('examples.%s' % name, globals(), locals(), ['main'])
    sys.stdout = Logger('%s.log' % name)
    ai.main()

def start_brower():
    import webbrowser
    webbrowser.GenericBrowser('google-chrome').open('./website/build/room_0.html')

def run_all():
    ps = []
    ps.append(Process(target=start_game))
    ps.append(Process(target=start_http))
    ps.append(Process(target=start_brower))

    ps.append(Process(target=start_ai, args=(['ai_flreeyv2'])))
    ps.append(Process(target=start_ai, args=(['ai_flreeyv2'])))

    for p in ps:
        time.sleep(1)
        p.start()

    for p in ps:
        p.join()

def kill_all():
    pass

def main():
    run_all()

if __name__ == '__main__':
    main()
