(function() {
  var DUR, Game, GameShower, SIZE, WS, create_svg, draw_circle, log, side_color,
    __hasProp = Object.prototype.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor; child.__super__ = parent.prototype; return child; };

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

  SIZE = 80;

  DUR = 30;

  log = function() {
    return console.log(arguments);
  };

  Game = (function(_super) {

    __extends(Game, _super);

    Game.extend(Spine.Events);

    function Game() {}

    Game.prototype.set_server = function(addr, room) {
      this.addr = addr;
      this.room = room;
      console.log('set server:', this.addr, "with room: ", this.room);
      this.ws = new WS("ws://" + addr + "/info");
      this.ws.onmessage = this.proxy(function(e) {
        return this.onmessage($.parseJSON(e.data));
      });
      this.ws.onerror = function(e) {
        return console.log(e);
      };
      this.ws.onclose = function(e) {
        return console.log("connection closed, refresh please..");
      };
      return this.ws.onopen = this.proxy(function() {
        this.ws.send(JSON.stringify({
          op: 'setroom',
          room: this.room
        }));
        this.ws.send(JSON.stringify({
          op: 'map',
          room: this.room
        }));
        return this.ws.send(JSON.stringify({
          op: 'info',
          room: this.room
        }));
      });
    };

    Game.prototype.onmessage = function(data) {
      switch (data.op) {
        case "info":
          Game.trigger("info", data);
          return log("info:", data);
        case "add":
          return Game.trigger("add", data);
        case "map":
          Game.trigger("map", data);
          return log("map:", data);
        default:
          if (data.status !== 'ok') return console.log(data);
      }
    };

    return Game;

  })(Spine.Module);

  GameShower = (function(_super) {

    __extends(GameShower, _super);

    function GameShower(game) {
      this.game = game;
      GameShower.__super__.constructor.apply(this, arguments);
      Game.bind("map", this.proxy(function(map) {
        this.map = map;
        return this.update_map();
      }));
      Game.bind("info", this.proxy(function(info) {
        this.info = info;
        return this.update_info();
      }));
      this.info = {};
      this.map = {};
      this.div_scene = $('#board-scene');
      this.div_desc = $('#desc');
      this.div_status = $('#game-status');
      this.div_round = $('#current-round');
      this.div_maxround = $('#max-round');
      this.div_logs = $('#board-logs');
    }

    GameShower.prototype.show_move_desc = function(e) {
      var count, id, remain, side, to, _from, _ref;
      id = $(e.target).attr('move_id');
      _ref = this.info.moves[id], side = _ref[0], _from = _ref[1], to = _ref[2], count = _ref[3], remain = _ref[4];
      return this.div_desc.html("<div class=\"desc-move\">            <span>player<span> " + side + "<br/>            <span>from<span> " + _from + "<br/>            <span>to<span> " + to + "<br/>            <span>count<span> " + count + "<br/>            <span>remain<span> " + remain + "<br/>            </div>                ");
    };

    GameShower.prototype.show_planet_desc = function(e) {
      var count, hold, id, planet_info, side;
      id = $(e.target).attr('planet_id');
      planet_info = this.map.planets[id];
      hold = this.info.holds[id];
      side = hold[0];
      count = hold[1];
      return this.div_desc.html("<div class=\"desc-planet\">the planet: " + id + "<br/>            <span>def<span> " + planet_info.def + "<br/>            <span>res<span> " + planet_info.res + "<br/>            <span>cos<span> " + planet_info.cos + "<br/>            <span>max<span> " + planet_info.max + "<br/>            </div>            <div class=\"desc-holds\">with side: " + side + "<br/>            <div class=\"desc-holds\">count: " + count + "<br/>                ");
    };

    GameShower.prototype.show_route_desc = function(e) {
      var id, move, moves, route, _i, _len, _ref;
      id = $(e.target).attr('route_id');
      route = this.map.routes[id];
      moves = [];
      _ref = this.info.moves;
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        move = _ref[_i];
        if (move[1] !== route[0] || move[2] !== route[1]) continue;
        moves.push(move);
      }
      return this.div_desc.html("            <div class=\"desc-route\">                step: " + route[2] + "                moves: " + moves + "            </div>            ");
    };

    GameShower.prototype.update_map = function() {
      var div_planet, i, planet, _len, _ref, _results;
      this.div_maxround.html(this.map.max_round);
      this.count_route_pos();
      this.div_planets = [];
      this.div_routes = [];
      this.div_moves = [];
      this.div_scene.width(SIZE * this.map.map_size[0]);
      this.div_scene.height(SIZE * this.map.map_size[1]);
      _ref = this.map.planets;
      _results = [];
      for (i = 0, _len = _ref.length; i < _len; i++) {
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
      var div_planet, hold, i, _len, _ref;
      this.div_round.html(this.info.round);
      this.update_players();
      this.update_logs();
      this.div_status.html(this.info.status);
      _ref = this.info.holds;
      for (i = 0, _len = _ref.length; i < _len; i++) {
        hold = _ref[i];
        div_planet = this.div_planets[i];
        div_planet.css("background", side_color(hold[0]));
        div_planet.html(hold[1]);
      }
      return this.update_moves();
    };

    GameShower.prototype.update_moves = function() {
      var count, div_move, i, move, next, pos, remain, side, to, _from, _i, _len, _len2, _ref, _ref2, _ref3, _results;
      _ref = this.div_moves;
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        div_move = _ref[_i];
        div_move.remove();
      }
      _ref2 = this.info.moves;
      _results = [];
      for (i = 0, _len2 = _ref2.length; i < _len2; i++) {
        move = _ref2[i];
        side = move[0], _from = move[1], to = move[2], count = move[3], remain = move[4];
        _ref3 = this.get_route_pos_and_next(_from, to, remain), pos = _ref3[0], next = _ref3[1];
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
        div_move.animate({
          left: pos[0],
          top: pos[1]
        }, 4000);
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
      var dx, dy, fx, fy, i, j, move_step, route, step, to, tx, ty, _from, _len, _ref, _ref2, _ref3, _ref4, _results;
      this.route_move_pos = {};
      _ref = this.map.routes;
      _results = [];
      for (i = 0, _len = _ref.length; i < _len; i++) {
        route = _ref[i];
        _from = route[0], to = route[1], step = route[2];
        _ref2 = this.map.planets[_from].pos, fx = _ref2[0], fy = _ref2[1];
        _ref3 = this.map.planets[to].pos, tx = _ref3[0], ty = _ref3[1];
        tx = tx * SIZE + SIZE / 2;
        ty = ty * SIZE + SIZE / 2;
        fx = fx * SIZE + SIZE / 2;
        fy = fy * SIZE + SIZE / 2;
        dx = (tx - fx) / (step - 1);
        dy = (ty - fy) / (step - 1);
        move_step = [];
        for (j = 0, _ref4 = step - 1; 0 <= _ref4 ? j <= _ref4 : j >= _ref4; 0 <= _ref4 ? j++ : j--) {
          move_step.push([fx + dx * j, fy + dy * j]);
        }
        this.route_move_pos[to * 1000 + _from] = move_step;
        _results.push(this.route_move_pos[_from * 1000 + to] = move_step.slice(0).reverse());
      }
      return _results;
    };

    GameShower.prototype.update_players = function() {
      var data, player, player_data, _i, _len, _ref;
      data = [];
      _ref = this.info.players;
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        player = _ref[_i];
        player_data = ["" + player.side + " - " + player.name, "planets: " + player.planets, "units: " + player.units, "" + player.status];
        data.push('<div class="player">' + player_data.join("<br/>") + '</div>');
      }
      return $('#players').html(data.join("\n"));
    };

    GameShower.prototype.update_logs = function() {
      var log, _i, _len, _ref;
      this.logs = ['<div class="log">round: ' + this.info.round + '</div>'];
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
      if (data.attack === data.defence) return;
      return this.logs.push('<div class="log">' + ("planet: " + data.planet + ": player " + data.attack + " attack player " + data.defence + ".") + '</div>');
    };

    GameShower.prototype.display_production = function(data) {
      return this.logs.push('<div class="log">' + ("planet " + data.planet + ": production to " + data.count + ".") + '</div>');
    };

    return GameShower;

  })(Spine.Controller);

  window.Game = Game;

  window.GameShower = GameShower;

}).call(this);
