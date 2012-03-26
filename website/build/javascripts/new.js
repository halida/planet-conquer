(function() {
  var WS, config;

  config = {
    addr: '127.0.0.1:9999',
    room: 0,
    debug: true
  };

  if (typeof MozWebSocket !== "undefined" && MozWebSocket !== null) {
    WS = MozWebSocket;
  } else {
    WS = WebSocket;
  }

  this.ws = new WS("ws://" + config.addr + "/info");

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
    var cell, data, from, hold, html, i, move, p, planet, planet_id, r, t, to, top, _fn, _i, _j, _len, _len2, _len3, _len4, _len5, _ref, _ref2, _ref3, _ref4, _ref5;
    data = $.parseJSON(e.data);
    if (config.debug) console.log(data);
    switch (data.op) {
      case 'map':
        window.map = data;
        map.dom = $('#map');
        cell = Math.floor(940 / map.map_size[0]);
        _ref = map.planets;
        for (i = 0, _len = _ref.length; i < _len; i++) {
          p = _ref[i];
          p.id = i;
          p.dom = $("<div id='planet_" + i + "' class='cell planet' style='margin:" + (p.pos[1] * cell) + "px 0 0 " + (p.pos[0] * cell) + "px'>" + i + "</div>").appendTo(map.dom);
          p.dom.data('planet', i);
          map.planets[i] = p;
        }
        map.offest_size = $('#planet_0').width();
        html = ["<svg style='width:100%;height:" + (cell * map.map_size[1]) + "px;position:absolute'>"];
        _ref2 = map.routes;
        for (_i = 0, _len2 = _ref2.length; _i < _len2; _i++) {
          r = _ref2[_i];
          if (r[0] > r[1]) continue;
          from = $('#planet_' + r[0]).offset();
          to = $('#planet_' + r[1]).offset();
          html.push("<line x1='" + (from.left + (map.offest_size / 2)) + "' y1='" + (from.top + (map.offest_size / 2)) + "' x2='" + (to.left + (map.offest_size / 2)) + "' y2='" + (to.top + (map.offest_size / 2)) + "' style='stroke:#444;stroke-width:2px' stroke-dasharray='3,3' />");
        }
        html.push('</svg>');
        return $('body').prepend(html.join(''));
      case 'info':
        window.players = data.players;
        if (players[0]) players[0].color = '#EE2C44';
        if (players[1]) players[1].color = '#42C3D9';
        if (players[2]) players[2].color = '#E96FA9';
        if (players[3]) players[3].color = '#A5CF4E';
        _ref3 = data.holds;
        for (planet_id = 0, _len3 = _ref3.length; planet_id < _len3; planet_id++) {
          hold = _ref3[planet_id];
          planet = map.planets[planet_id];
          planet.hold = hold[0];
          if (hold[0] !== null) {
            planet.dom.html(hold[1])[0].className = 'cell player_' + hold[0];
          } else {
            planet.dom.html(planet.id)[0].className = 'cell planet';
          }
        }
        _ref4 = data.moves;
        _fn = function(move) {
          var dom, from_xy, to_xy;
          from = map.planets[move[1]].dom;
          from_xy = from.offset();
          to = map.planets[move[2]].dom;
          to_xy = to.offset();
          dom = $("<div class='move player_" + move[0] + "' style='left:" + (from_xy.left + map.offest_size / 3.7) + "px;top:" + (from_xy.top + map.offest_size / 3.7) + "px'>" + move[3] + "</div>");
          map.dom.append(dom);
          return dom.animate({
            left: to_xy.left + map.offest_size / 3.7,
            top: to_xy.top + map.offest_size / 3.7
          }, 1800, function() {
            return dom.remove();
          });
        };
        for (_j = 0, _len4 = _ref4.length; _j < _len4; _j++) {
          move = _ref4[_j];
          _fn(move);
        }
        top = [];
        _ref5 = _.sortBy(players, function(p) {
          return -(p.planets * 10000 + p.units);
        });
        for (i = 0, _len5 = _ref5.length; i < _len5; i++) {
          t = _ref5[i];
          top.push("<p style='color:" + t.color + "'>No." + (i + 1) + " " + t.name + " " + t.planets + "/" + t.units + "</p>");
        }
        return $('#top').html(top.join(''));
    }
  };

  ws.onerror = function(e) {
    if (config.debug) return console.log(e);
  };

  $('#map').on('mouseenter', '.cell', function() {
    var data, planet;
    data = $.data(this);
    planet = map.planets[data.planet];
    return $('#planet').html("<hr /><h3>No." + data.planet + "</h3><p>DEF：X" + planet.def + "</p><p>RES：X" + planet.res + " +" + planet.cos + "</p><p>MAX：" + planet.max + "</p>");
  }).on('mouseleave', '.cell', function() {
    return $('#planet').html('');
  });

}).call(this);
