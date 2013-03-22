(function() {
  var DUR, Game, GameShower, Recorder, SIZE, WS, create_svg, draw_circle, log, side_color,
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  if (typeof MozWebSocket !== "undefined" && MozWebSocket !== null) {
    WS = MozWebSocket;
  } else {
    WS = WebSocket;
  }

  side_color = function(i) {
    return ['red', 'yellow', 'blue', 'green', 'pink', 'lightblue'][i];
  };

  draw_circle = function(ctx, x, y, r) {
    return ctx.arc(x, y, r, 0, Math.PI * 2, true);
  };

  create_svg = function(obj) {
    return document.createElementNS('http://www.w3.org/2000/svg', obj);
  };

  SIZE = 60;

  DUR = 30;

  log = function() {
    return console.log(arguments);
  };

  Game = (function(_super) {

    __extends(Game, _super);

    Game.extend(Spine.Events);

    function Game() {
      Game.__super__.constructor.apply(this, arguments);
      this.on_get_message = true;
    }

    Game.prototype.set_server = function(addr, room) {
      this.addr = addr;
      this.room = room;
      console.log('set server:', this.addr, "with room: ", this.room);
      this.ws = new WS("ws://" + addr + "/info");
      this.ws.onmessage = this.proxy(function(e) {
        if (!this.on_get_message) {
          return;
        }
        return Game.trigger("data", $.parseJSON(e.data));
      });
      this.ws.onerror = function(e) {
        return console.log(e);
      };
      this.ws.onclose = function(e) {
        return console.log("connection closed, refresh please..");
      };
      return this.ws.onopen = this.proxy(function() {
        this.set_room();
        this.get_map();
        return this.get_info();
      });
    };

    Game.prototype.set_room = function() {
      return this.ws.send(JSON.stringify({
        op: 'setroom',
        room: this.room
      }));
    };

    Game.prototype.get_info = function() {
      return this.ws.send(JSON.stringify({
        op: 'info',
        room: this.room
      }));
    };

    Game.prototype.get_map = function() {
      return this.ws.send(JSON.stringify({
        op: 'map',
        room: this.room
      }));
    };

    return Game;

  })(Spine.Module);

  GameShower = (function(_super) {

    __extends(GameShower, _super);

    function GameShower(game) {
      this.game = game;
      GameShower.__super__.constructor.apply(this, arguments);
      Game.bind("data", this.proxy(this.update_data));
      this.info = {};
      this.map = {};
      this.div_scene = $('#board-scene');
      this.div_desc = $('#desc');
      this.div_status = $('#game-status');
      this.div_round = $('#current-round');
      this.div_maxround = $('#max-round');
      this.div_logs = $('#logs');
      this.div_map_name = $('#map-name');
      this.div_map_author = $('#map-author');
      this.div_map_desc = $('#map-desc');
    }

    GameShower.prototype.show_move_desc = function(e) {
      var count, id, remain, side, to, _from, _ref;
      id = $(e.target).attr('move_id');
      _ref = this.info.moves[id], side = _ref[0], _from = _ref[1], to = _ref[2], count = _ref[3], remain = _ref[4];
      return this.div_desc.html("<div class=\"desc-move\">            <span>player<span> " + side + "<br/>            <span>from<span> " + _from + "<br/>            <span>to<span> " + to + "<br/>            <span>count<span> " + count + "<br/>            <span>remain<span> " + remain + "<br/>            </div>                ");
    };

    GameShower.prototype.show_planet_desc = function(e) {
      var count, hold, id, planet_info, player, side, text;
      id = $(e.target).attr('planet_id');
      planet_info = this.map.planets[id];
      hold = this.info.holds[id];
      side = hold[0];
      count = hold[1];
      text = "<div class=\"desc-planet\">the planet: " + id + "<br/>            <span>def<span> " + planet_info.def + "<br/>            <span>res<span> " + planet_info.res + "<br/>            <span>cos<span> " + planet_info.cos + "<br/>            <span>max<span> " + planet_info.max + "<br/>            </div>                ";
      if ((this.info != null) && side !== null) {
        player = this.info.players[side];
        text += "<div class=\"desc-holds\">with player: " + player.name + "            <div style='background: " + player.color + "' class='side-mark'/>                </div>            <div class=\"desc-holds\">count: " + count + "</div>                ";
      }
      return this.div_desc.html(text);
    };

    GameShower.prototype.show_route_desc = function(e) {
      var id, move, moves, route, _i, _len, _ref;
      id = $(e.target).attr('route_id');
      route = this.map.routes[id];
      moves = [];
      _ref = this.info.moves;
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        move = _ref[_i];
        if (move[1] !== route[0] || move[2] !== route[1]) {
          continue;
        }
        moves.push(move);
      }
      return this.div_desc.html("            <div class=\"desc-route\">                step: " + route[2] + "                moves: " + moves + "            </div>            ");
    };

    GameShower.prototype.update_data = function(data) {
      switch (data.op) {
        case "info":
          this.info = data;
          return this.update_info();
        case "add":
          return false;
        case "map":
          this.map = data;
          return this.update_map();
        default:
          if (data.status !== 'ok') {
            return console.log(data);
          }
      }
    };

    GameShower.prototype.update_map = function() {
      var div_planet, i, planet, _i, _len, _ref, _results;
      this.animate_time = this.map.step * 1000;
      this.div_scene.find('.planet').remove();
      this.div_scene.find('.move').remove();
      this.div_maxround.html(this.map.max_round);
      this.div_map_name.html(this.map.name);
      this.div_map_author.html(this.map.author);
      this.div_map_desc.html(this.map.desc);
      this.count_route_pos();
      this.div_planets = [];
      this.div_routes = [];
      this.div_moves = [];
      this.div_scene.width(SIZE * this.map.map_size[0]);
      this.div_scene.height(SIZE * this.map.map_size[1]);
      _ref = this.map.planets;
      _results = [];
      for (i = _i = 0, _len = _ref.length; _i < _len; i = ++_i) {
        planet = _ref[i];
        div_planet = $("<div/>");
        div_planet.attr({
          id: "planet-" + i,
          "class": "planet",
          planet_id: i
        });
        div_planet.css({
          left: planet.pos[0] * SIZE + SIZE / 2,
          top: planet.pos[1] * SIZE + SIZE / 2,
          background: "white"
        });
        div_planet.html('?');
        div_planet.hover(this.proxy(this.show_planet_desc));
        this.div_planets.push(div_planet);
        _results.push(this.div_scene.append(div_planet));
      }
      return _results;
    };

    GameShower.prototype.update_info = function() {
      this.div_round.html(this.info.round);
      this.update_players();
      this.update_logs();
      this.div_status.html(this.info.status);
      this.update_moves();
      return this.update_holds(this.info);
    };

    GameShower.prototype.update_holds = function(info) {
      var div_planet, hold, i, _i, _len, _ref, _results;
      _ref = info.holds;
      _results = [];
      for (i = _i = 0, _len = _ref.length; _i < _len; i = ++_i) {
        hold = _ref[i];
        div_planet = this.div_planets[i];
        if (hold[0] !== null) {
          div_planet.css("background", side_color(hold[0]));
        } else {
          div_planet.css("background", "#ccc");
        }
        _results.push(div_planet.html(hold[1]));
      }
      return _results;
    };

    GameShower.prototype.update_moves = function() {
      var count, div_move, i, move, next, pos, remain, side, to, _from, _i, _len, _ref, _ref1, _results;
      this.div_scene.find('.move').remove();
      _ref = this.info.moves;
      _results = [];
      for (i = _i = 0, _len = _ref.length; _i < _len; i = ++_i) {
        move = _ref[i];
        side = move[0], _from = move[1], to = move[2], count = move[3], remain = move[4];
        _ref1 = this.get_route_pos_and_next(_from, to, remain), pos = _ref1[0], next = _ref1[1];
        div_move = $("<div/>");
        div_move.attr({
          id: "move-" + i,
          "class": "move",
          move_id: i
        });
        div_move.css({
          left: next[0],
          top: next[1],
          background: side_color(side)
        });
        div_move.html(count);
        div_move.hover(this.proxy(this.show_move_desc));
        div_move.transition({
          left: pos[0],
          top: pos[1]
        }, this.animate_time);
        this.div_moves.push(div_move);
        _results.push(this.div_scene.append(div_move));
      }
      return _results;
    };

    GameShower.prototype.get_route_pos_and_next = function(_from, to, remain) {
      var route;
      route = this.route_move_pos[_from * 1000 + to];
      return [route[remain - 1], route[remain]];
    };

    GameShower.prototype.count_route_pos = function() {
      var dx, dy, fx, fy, i, j, move_step, route, step, to, tx, ty, _from, _i, _j, _len, _ref, _ref1, _ref2, _ref3, _results;
      this.route_move_pos = {};
      _ref = this.map.routes;
      _results = [];
      for (i = _i = 0, _len = _ref.length; _i < _len; i = ++_i) {
        route = _ref[i];
        _from = route[0], to = route[1], step = route[2];
        _ref1 = this.map.planets[_from].pos, fx = _ref1[0], fy = _ref1[1];
        _ref2 = this.map.planets[to].pos, tx = _ref2[0], ty = _ref2[1];
        tx = tx * SIZE + SIZE / 2;
        ty = ty * SIZE + SIZE / 2;
        fx = fx * SIZE + SIZE / 2;
        fy = fy * SIZE + SIZE / 2;
        dx = (tx - fx) / (step - 1);
        dy = (ty - fy) / (step - 1);
        move_step = [];
        for (j = _j = 0, _ref3 = step - 1; 0 <= _ref3 ? _j <= _ref3 : _j >= _ref3; j = 0 <= _ref3 ? ++_j : --_j) {
          move_step.push([fx + dx * j, fy + dy * j]);
        }
        this.route_move_pos[to * 1000 + _from] = move_step;
        _results.push(this.route_move_pos[_from * 1000 + to] = move_step.slice(0).reverse());
      }
      return _results;
    };

    GameShower.prototype.update_players = function() {
      var data, i, list, player, player_data, _i, _j, _len, _len1;
      data = [];
      list = this.info.players.slice();
      for (i = _i = 0, _len = list.length; _i < _len; i = ++_i) {
        player = list[i];
        player.color = side_color(i);
      }
      list.sort(function(a, b) {
        return a.planets - b.planets;
      });
      list.reverse();
      for (i = _j = 0, _len1 = list.length; _j < _len1; i = ++_j) {
        player = list[i];
        player_data = ["" + player.side + " - " + player.name + " <div style='background: " + player.color + "' class='side-mark'/>", "planets: " + player.planets, "units: " + player.units, "" + player.status];
        data.push('<div class="player">' + player_data.join("<br/>") + '</div>');
      }
      return $('#players').html(data.join("\n"));
    };

    GameShower.prototype.update_logs = function() {
      var _i, _len, _ref;
      this.logs = ['<div class="log">------------ round: ' + this.info.round + '</div>'];
      _ref = this.info.logs;
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        log = _ref[_i];
        switch (log.type) {
          case "production":
            this.display_production(log);
            break;
          case "battle":
            this.display_battle(log);
        }
      }
      return this.div_logs.prepend(this.logs.join("\n"));
    };

    GameShower.prototype.display_battle = function(data) {
      if (data.attack === data.defence) {
        return;
      }
      return this.logs.push('<div class="log">' + ("planet: " + data.planet + ": player " + data.attack + " attack player " + data.defence + ".") + '</div>');
    };

    GameShower.prototype.display_production = function(data) {
      return this.logs.push('<div class="log">' + ("planet " + data.planet + ": production to " + data.count + ".") + '</div>');
    };

    return GameShower;

  })(Spine.Controller);

  Recorder = (function(_super) {

    __extends(Recorder, _super);

    function Recorder(game, div) {
      this.game = game;
      Recorder.__super__.constructor.apply(this, arguments);
      this.div = $(div);
      this.div_record = this.div.find('.record-record');
      this.div_replay = this.div.find('.record-replay');
      this.div_record_count = this.div.find('.record-count');
      this.div_replay_on = this.div.find('.replay-on');
      this.div.on('click', '.record-record', this.proxy(this.on_record));
      this.div.on('click', '.record-replay', this.proxy(this.on_replay));
      this.on_replay = false;
      this.on_record = false;
      this.data_list = [];
      this.replay_on = 0;
      this.animate_time = 2000;
      Game.bind("data", this.proxy(this.save_data));
    }

    Recorder.prototype.on_record = function() {
      this.on_record = !this.on_record;
      this.div_record.toggleClass('on');
      if (this.on_record) {
        this.data_list = [];
        this.replay_on = 0;
        return this.game.get_map();
      }
    };

    Recorder.prototype.on_replay = function() {
      this.on_replay = !this.on_replay;
      this.div_replay.toggleClass('on');
      this.game.on_get_message = !this.on_replay;
      return setTimeout(this.proxy(this.replay_timer), this.animate_time);
    };

    Recorder.prototype.replay_timer = function() {
      if (!this.on_replay) {
        return;
      }
      if (this.data_list.length <= 0) {
        return;
      }
      Game.trigger("data", this.data_list[this.replay_on]);
      this.div_replay_on.html(this.replay_on);
      this.replay_on += 1;
      this.replay_on %= this.data_list.length;
      return setTimeout(this.proxy(this.replay_timer), this.animate_time);
    };

    Recorder.prototype.save_data = function(data) {
      if (!this.on_record) {
        return;
      }
      this.data_list.push(data);
      return this.div_record_count.html(this.data_list.length);
    };

    return Recorder;

  })(Spine.Controller);

  window.Game = Game;

  window.Recorder = Recorder;

  window.GameShower = GameShower;

}).call(this);
