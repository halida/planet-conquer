#-*- coding:utf-8 -*-
PYTHON?=python

unittest:
	$(PYTHON) srcs/map/map.py
	$(PYTHON) srcs/game.py
	$(PYTHON) srcs/game_controller.py
# $(PYTHON) srcs/ailib.py

# run the game server
game:
	$(PYTHON) srcs/zmq_game_server.py local
webgame:
	$(PYTHON) srcs/zmq_game_server.py web

# run the website
website:
	cd rubyweb; bundle exec rails server -p 2000

# run http interface server
http:
	cd srcs; $(PYTHON) web_server.py

# run a test ai
ai:
	$(PYTHON) examples/ai_halida.py zero 0

ai_flreey:
	$(PYTHON) examples/ai_flreey.py zero 0
# run lots of test ai
ais:
	$(PYTHON) examples/ai_halida.py zero 0 4

# pygame show local game
pygame:
	$(PYTHON) srcs/pygame_show.py
show:
	$(PYTHON) srcs/zmq_pygame_show.py 0

# record/replay log
record:
	$(PYTHON) srcs/zmq_logger.py zero 0 test.log
replay:
	$(PYTHON) srcs/zmq_replayer.py test.log

all:
	$(PYTHON) running.py
