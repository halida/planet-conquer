(function() {
  var WS, audio, bg_img, board, init_websocket, onmusic, onmusic_btn, onplay, onplay_btn, start_move, start_occupy;

  onmusic = true;

  audio = $('audio#music')[0];

  onmusic_btn = $('#music_play');

  onmusic_btn.click(function() {
    if (onmusic) {
      audio.pause();
      onmusic_btn.text("=");
    } else {
      audio.play();
      onmusic_btn.text(">");
    }
    return onmusic = !onmusic;
  });

  bg_img = $('.bg img');

  bg_img.load(function() {
    return bg_img.addClass('on');
  });

  onplay = true;

  onplay_btn = $('#game_play');

  onplay_btn.click(function() {
    if (onplay) {
      onplay_btn.text("=");
    } else {
      onplay_btn.text(">");
    }
    return onplay = !onplay;
  });

  if (typeof MozWebSocket !== "undefined" && MozWebSocket !== null) {
    WS = MozWebSocket;
  } else {
    WS = WebSocket;
  }

  init_websocket = function() {
    var ws;
    ws = new WS("ws://" + config.addr + "/info");
    ws._send = ws.send;
    ws.send = function(data) {
      if (typeof data === 'string') {
        data = {
          op: data
        };
      }
      data.room = config.room;
      return this._send(JSON.stringify(data));
    };
    ws.onopen = function() {
      ws.send('setroom');
      ws.send('map');
      return ws.send('info');
    };
    ws.onmessage = function(e) {
      var data;
      if (!onplay) {
        return;
      }
      data = $.parseJSON(e.data);
      if (config.debug) {
        console.log(data);
      }
      switch (data.op) {
        case 'map':
          return init_map(data);
        case 'info':
          return update_info(data);
      }
    };
    return ws.onerror = function(e) {
      if (config.debug) {
        return console.log(e);
      }
    };
  };

  board = Raphael('map');

  window.mapinfo = {
    logs: $('#logs').html(''),
    planet_size: 21
  };

  window.init_map = function(data) {
    var c, cell, from, i, info, map, p, planet_size, r, td, to, tp, tt, _i, _j, _len, _len1, _ref, _ref1, _results;
    console.log('map');
    mapinfo.map = map = data;
    mapinfo.cell = cell = Math.floor(940 / (map.map_size[0] + 1));
    board.setViewBox(-40, -40, cell * (map.map_size[0] + 1), cell * (map.map_size[1] + 1));
    console.log('cell:', cell);
    planet_size = mapinfo.planet_size;
    info = "<h2 id='map-name'>" + map.name + "</h2>";
    info += " <div id='map-author'>author: " + map.author + "</div>";
    info += "<div id='map-desc'>" + map.desc + "</div>";
    $('#map-info').html(info);
    _ref = map.routes;
    for (_i = 0, _len = _ref.length; _i < _len; _i++) {
      r = _ref[_i];
      if (r[0] > r[1]) {
        continue;
      }
      from = map.planets[r[0]].pos;
      to = map.planets[r[1]].pos;
      c = board.path("M " + (from[0] * cell) + " " + (from[1] * cell) + " L" + (to[0] * cell) + " " + (to[1] * cell));
      c.attr("stroke", "#444");
      c.attr('stroke-width', 2);
      c.attr('stroke-dasharray', '-');
    }
    mapinfo.planet_objs = [];
    mapinfo.planet_nums = [];
    _ref1 = map.planets;
    _results = [];
    for (i = _j = 0, _len1 = _ref1.length; _j < _len1; i = ++_j) {
      p = _ref1[i];
      p.id = i;
      c = board.circle(p.pos[0] * cell, p.pos[1] * cell, planet_size);
      c.attr("fill", "#000");
      c.attr("stroke", "#fff");
      c.attr("stroke-width", 2);
      mapinfo.planet_objs.push(c);
      tt = board.text(p.pos[0] * cell, p.pos[1] * cell - planet_size - 10, "⊙" + p.def + " ★" + p.res + " + " + p.cos);
      tt.attr('font-size', 11).attr('width', 84).attr('fill', '#888');
      td = board.text(p.pos[0] * cell, p.pos[1] * cell + planet_size + 11, "≤" + p.max);
      td.attr('font-size', 11).attr('width', 84).attr('fill', '#888');
      tp = board.text(p.pos[0] * cell, p.pos[1] * cell, "0");
      tp.attr('font-size', 15).attr('width', planet_size * 2).attr('fill', '#000');
      _results.push(mapinfo.planet_nums.push(tp));
    }
    return _results;
  };

  window.update_info = function(data) {
    var hold, i, log, map, planet, planet_id, players, t, tactic, top, _i, _j, _k, _len, _len1, _len2, _ref, _ref1, _ref2, _results;
    console.log('info');
    map = mapinfo.map;
    mapinfo.players = players = data.players;
    if (!data.players) {
      return;
    }
    if (players[0]) {
      players[0].color = '#EE2C44';
    }
    if (players[1]) {
      players[1].color = '#42C3D9';
    }
    if (players[2]) {
      players[2].color = '#E96FA9';
    }
    if (players[3]) {
      players[3].color = '#A5CF4E';
    }
    _ref = data.holds;
    for (planet_id = _i = 0, _len = _ref.length; _i < _len; planet_id = ++_i) {
      hold = _ref[planet_id];
      planet = map.planets[planet_id];
      planet.hold = hold[0];
      if (hold[0] !== null) {
        mapinfo.planet_nums[planet_id].attr('text', hold[1]);
        mapinfo.planet_objs[planet_id].attr('fill', players[hold[0]].color);
      } else {
        mapinfo.planet_nums[planet_id].attr('text', '0');
        mapinfo.planet_objs[planet_id].attr('fill', 'black');
      }
    }
    top = [];
    _ref1 = _.sortBy(players, function(p) {
      return -(p.planets * 10000 + p.units);
    });
    for (i = _j = 0, _len1 = _ref1.length; _j < _len1; i = ++_j) {
      t = _ref1[i];
      top.push("<div class='top_" + i + "' style='color:" + t.color + "'>", "<span>" + (i + 1) + "</span><p><strong>" + t.name + "</strong><br />", "Planets: " + t.planets + "<br />Units: " + t.units + "<br />", "status: " + t.status + "<br/>Points: " + t.points + "</p></div>");
    }
    $('#top').html(top.join(''));
    $('#round').html("Round " + data.round + "/" + map.max_round);
    $('#status').html(data.status);
    console.log(data.logs);
    _ref2 = data.logs;
    _results = [];
    for (_k = 0, _len2 = _ref2.length; _k < _len2; _k++) {
      log = _ref2[_k];
      switch (log.type) {
        case 'move':
          _results.push(start_move(log));
          break;
        case 'production':
          _results.push(true);
          break;
        case 'occupy':
          _results.push(start_occupy(log));
          break;
        case 'battle':
          if (log.winner === log.defence) {
            _results.push(mapinfo.logs.trigger('log', "<p style='color:" + players[log.winner].color + "'>" + players[log.winner].name + ":", " Successfully block the " + players[log.attack].name + "'s offensive<p>"));
          } else {
            _results.push(mapinfo.logs.trigger('log', "<p style='color:" + players[log.winner].color + "'>" + players[log.winner].name + ":", " Occupation of the No." + log.planet + " planet</p>"));
          }
          break;
        case 'tactic':
          tactic = log.tactic;
          _results.push(mapinfo.logs.trigger('log', "<p style='color: red'>tactic: " + tactic.type + "</p>"));
          break;
        default:
          _results.push(void 0);
      }
    }
    return _results;
  };

  start_move = function(log) {
    var c, cell, f, from_xy, move, players, t, to_xy, w;
    move = log;
    cell = mapinfo.cell;
    players = mapinfo.players;
    f = mapinfo.map.planets[move.from].pos;
    from_xy = [f[0] * cell, f[1] * cell];
    t = mapinfo.map.planets[move.to].pos;
    to_xy = [t[0] * cell, t[1] * cell];
    c = board.circle(from_xy[0], from_xy[1], mapinfo.planet_size / 2).attr('fill', players[log.side].color).attr('stroke', players[log.side].color);
    w = board.text(from_xy[0], from_xy[1], log.count).attr('fill', 'black').attr('height', mapinfo.planet_size / 2).attr('width', mapinfo.planet_size / 2);
    c.animate({
      cx: to_xy[0],
      cy: to_xy[1]
    }, mapinfo.map.step * (move.step - 1) * 1000, '<>', function() {
      return c.remove();
    });
    w.animate({
      x: to_xy[0],
      y: to_xy[1]
    }, mapinfo.map.step * (move.step - 1) * 1000, '<>', function() {
      return w.remove();
    });
    return mapinfo.logs.trigger('log', "<p style='color:" + players[log.side].color + "'>" + players[log.side].name + ":", " Send " + log.count + " troops from No." + log.from + " to No." + log.to + ".</p>");
  };

  start_occupy = function(log) {
    var obj;
    obj = mapinfo.planet_objs[log.planet];
    return obj.animate({
      "fill-opacity": 0
    }, 500, 'linear', function() {
      return obj.animate({
        "fill-opacity": 1
      }, 500);
    });
  };

  $('#logs').bind('log', function(e, msg) {
    return this.innerHTML = msg + this.innerHTML;
  });

  $('#show_logs').click(function() {
    return $("#logs").toggle(200);
  });

  init_websocket();

}).call(this);
