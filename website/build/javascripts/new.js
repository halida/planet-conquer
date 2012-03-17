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
    var data, hold, html, i, move, planet, planet_id, td_width, _i, _len, _len2, _len3, _ref, _ref2, _ref3, _results, _results2;
    data = $.parseJSON(e.data);
    if (config.debug) console.log(data);
    switch (data.op) {
      case 'map':
        window.map = data;
        map.dom = $('#map');
        i = 0;
        td_width = 820 / data.map_size[0] - 4;
        html = [];
        _(data.map_size[1] * data.map_size[0]).times(function() {
          html.push("<div class='cell' style='width:" + td_width + "px;height:" + td_width + "px' id='" + i + "'>&nbsp;</div>");
          return i = i + 1;
        });
        map.dom.html(html.join(''));
        _ref = map.planets;
        _results = [];
        for (i = 0, _len = _ref.length; i < _len; i++) {
          planet = _ref[i];
          planet.id = i;
          planet.dom = $('#' + (planet.pos[0] + (planet.pos[1] * data.map_size[0]))).addClass('planet').data('planet', i);
          _results.push(map.planets[i] = planet);
        }
        return _results;
        break;
      case 'info':
        window.players = data.players;
        _ref2 = data.holds;
        for (planet_id = 0, _len2 = _ref2.length; planet_id < _len2; planet_id++) {
          hold = _ref2[planet_id];
          planet = map.planets[planet_id];
          planet.hold = hold[0];
          if (hold[0] !== null) {
            planet.dom.html(data.players[hold[0]].name + ' ' + hold[1]);
          } else {
            planet.dom.html('');
          }
        }
        _ref3 = data.moves;
        _results2 = [];
        for (_i = 0, _len3 = _ref3.length; _i < _len3; _i++) {
          move = _ref3[_i];
          _results2.push((function(move) {
            var dom, from, to;
            from = map.planets[move[1]].dom.position();
            to = map.planets[move[2]].dom.position();
            dom = $("<div class='move' style='left:" + from.left + "px;top:" + from.top + "px'>" + data.players[move[0]].name + " " + move[3] + "</div>");
            map.dom.append(dom);
            return dom.animate({
              left: to.left,
              top: to.top
            }, 4000, function() {
              return dom.remove();
            });
          })(move));
        }
        return _results2;
    }
  };

  ws.onerror = function(e) {
    if (config.debug) return console.log(e);
  };

  $('#map').on('hover click', '.cell', function() {
    var data, hold, planet;
    data = $.data(this);
    if (typeof data.planet !== 'undefined') {
      planet = map.planets[data.planet];
      if (planet.hold === null) {
        hold = '無';
      } else {
        hold = "" + players[planet.hold].name + " (" + players[planet.hold].planets + ")";
      }
      return $('#cell').html("<h3>No." + this.id + "</h3><p>類型：星球</p><p>防御系数：X" + planet.def + "</p><p>资源系数：X" + planet.res + " +" + planet.cos + "</p><p>最大生产量：" + planet.max + "</p><p>佔領者：" + hold + "</p>");
    } else {
      return $('#cell').html("<h3>No." + this.id + "</h3><p>類型：無</p>");
    }
  });

}).call(this);
