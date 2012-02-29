(function() {
  var Game, GameShower, SIZE, WS, create_svg, draw_circle, side_color,
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
          return Game.trigger("info", data);
        case "add":
          return Game.trigger("add", data);
        case "map":
          return Game.trigger("map", data);
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
      this.scene = $('#scene');
      this.svg = this.scene.svg();
      this.desc = $('#desc');
    }

    GameShower.prototype.show_planet_desc = function(e) {
      var count, hold, id, planet_info, side;
      id = $(e.target).attr('planet_id');
      planet_info = this.map.planets[id];
      hold = this.info.holds[id];
      side = hold[0];
      count = hold[1];
      return this.desc.html("<div class=\"desc-planet\">the planet: " + id + "<br/>            <span>def<span> " + planet_info.def + "<br/>            <span>res<span> " + planet_info.res + "<br/>            <span>cos<span> " + planet_info.cos + "<br/>            <span>max<span> " + planet_info.max + "<br/>            </div>            <div class=\"desc-holds\">with side: " + side + "<br/>            <div class=\"desc-holds\">count: " + count + "<br/>                ");
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
      return this.desc.html("            <div class=\"desc-route\">                step: " + route[2] + "                moves: " + moves + "            </div>            ");
    };

    GameShower.prototype.update_map = function() {
      var i, planet, pos1, pos2, route, step, svg_planet, svg_planet_text, svg_route, to, _from, _len, _len2, _ref, _ref2, _results;
      this.svg_planets = [];
      this.svg_routes = [];
      _ref = this.map.routes;
      for (i = 0, _len = _ref.length; i < _len; i++) {
        route = _ref[i];
        _from = route[0];
        to = route[1];
        step = route[2];
        pos1 = this.map.planets[_from].pos;
        pos2 = this.map.planets[to].pos;
        svg_route = $(create_svg("line"));
        svg_route.attr({
          id: "route-" + i,
          "class": "route",
          route_id: i,
          style: "stroke:rgb(0,0,255);stroke-width:3",
          x1: pos1[0] * SIZE + SIZE / 2,
          y1: pos1[1] * SIZE + SIZE / 2,
          x2: pos2[0] * SIZE + SIZE / 2,
          y2: pos2[1] * SIZE + SIZE / 2
        });
        svg_route.hover(this.proxy(this.show_route_desc));
        this.scene.append(svg_route);
        this.svg_planets.push(svg_route);
      }
      _ref2 = this.map.planets;
      _results = [];
      for (i = 0, _len2 = _ref2.length; i < _len2; i++) {
        planet = _ref2[i];
        svg_planet = $(create_svg("circle"));
        svg_planet.attr({
          id: "planet-" + i,
          "class": "planet",
          planet_id: i,
          cx: planet.pos[0] * SIZE + SIZE / 2,
          cy: planet.pos[1] * SIZE + SIZE / 2,
          r: SIZE / 4,
          fill: "white"
        });
        svg_planet.hover(this.proxy(this.show_planet_desc));
        this.scene.append(svg_planet);
        this.svg_routes.push(svg_planet);
        svg_planet_text = $(create_svg("text"));
        svg_planet_text.text('he');
        svg_planet_text.attr({
          id: "planet-text-" + i,
          "class": "planet-text",
          x: planet.pos[0] * SIZE + SIZE / 2,
          y: planet.pos[1] * SIZE + SIZE / 2,
          dx: -SIZE / 4,
          dy: +SIZE / 16
        });
        _results.push(this.scene.append(svg_planet_text));
      }
      return _results;
    };

    GameShower.prototype.update_info = function() {
      var hold, i, _len, _ref, _results;
      _ref = this.info.holds;
      _results = [];
      for (i = 0, _len = _ref.length; i < _len; i++) {
        hold = _ref[i];
        $('circle#planet-' + i).attr({
          fill: side_color(hold[0])
        });
        _results.push($('text#planet-text-' + i).text(hold[1]));
      }
      return _results;
    };

    return GameShower;

  })(Spine.Controller);

  window.Game = Game;

  window.GameShower = GameShower;

}).call(this);
