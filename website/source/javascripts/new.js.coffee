if MozWebSocket?
  WS = MozWebSocket
else
  WS = WebSocket

this.ws = new WS("ws://#{config.addr}/info")

ws._send = ws.send

ws.send = (data)->
  if typeof data is 'string'
    data = {
      op: data
    }
  data.room = config.room
  this._send JSON.stringify(data)

ws.onopen = ->
  ws.send 'setroom'
  ws.send 'map'
  ws.send 'info'

ws.onmessage = (e)->
  data = $.parseJSON(e.data)
  console.log data if config.debug
  switch data.op
    when 'map'
      window.map = data
      map.step = map.step * 1000
      map.dom = $('#map')
      cell = Math.floor(940/map.map_size[0])

      info = "<h2 id='map-name'>#{map.name}</h2>"
      info += " <div id='map-author'>author: #{map.author}</div>"
      info += "<div id='map-desc'>#{map.desc}</div>"
      $('#map-info').html(info)

      for p, i in map.planets
        p.id = i
        $("<div id='planet_#{i}' planet_type='#{p.type || 'normal'}' class='cell planet planet-#{p.type}' style='margin:#{p.pos[1] * cell}px 0 0 #{p.pos[0] * cell}px'></div>").appendTo(map.dom)
        p.dom = $('#planet_' + i)
        p.dom.data('planet', i)
        map.offest_size = $('#planet_0').width() if i == 0
        def = []
        _.times(Math.floor(p.def + 1), ->
          def.push '⊙'
        )
        def = def.join ' '
        res = []
        _.times(Math.floor(p.res), ->
          res.push '★'
        )
        res = res.join ' '
        p.dom.after("<span class='planet_info' style='margin:#{p.pos[1] * cell - 16}px 0 0 #{p.pos[0] * cell - map.offest_size / 2}px'>⊙#{p.def} ★#{p.res} + #{p.cos}</span><span class='planet_info' style='margin:#{p.pos[1] * cell + map.offest_size + 4}px 0 0 #{p.pos[0] * cell - map.offest_size / 2}px'>≥#{p.max}</span>").next()
        map.planets[i] = p


      html = ["<svg style='width:100%;height:#{cell * map.map_size[1]}px;position:absolute'>"]
      for r in map.routes
        continue if r[0] > r[1]
        from = $('#planet_' + r[0]).offset()
        to = $('#planet_' + r[1]).offset()
        html.push("<line x1='#{from.left + (map.offest_size / 2)}' y1='#{from.top + (map.offest_size / 2)}' x2='#{to.left + (map.offest_size / 2)}' y2='#{to.top + (map.offest_size / 2)}' style='stroke:#444;stroke-width:2px' stroke-dasharray='3,3' />")
      html.push('</svg>')
      $('body').prepend(html.join(''))

    when 'info'
      window.players = data.players
      return unless data.players
      players[0].color = '#EE2C44' if players[0]
      players[1].color = '#42C3D9' if players[1]
      players[2].color = '#E96FA9' if players[2]
      players[3].color = '#A5CF4E' if players[3]
      for hold, planet_id in data.holds
        planet = map.planets[planet_id]
        planet.hold = hold[0]
        if hold[0] isnt null
          planet.dom.html(hold[1])[0].className = 'cell player_' + hold[0]
        else
          planet.dom.html('')[0].className = 'cell planet'

      logs = $('#logs').html('')
      for log in data.logs
        switch log.type
          when 'move'
            ((move)->
              from = map.planets[move.from].dom
              from_xy = from.offset()
              to = map.planets[move.to].dom
              to_xy = to.offset()
              dom = $("<div class='move player_#{move.side}' style='left:#{from_xy.left + map.offest_size/3.7}px;top:#{from_xy.top + map.offest_size/3.7}px'>#{move.count}</div>")
              map.dom.append(dom)
              dom.animate({left: to_xy.left + map.offest_size/3.7, top: to_xy.top + map.offest_size/3.7}, map.step * (move.step-1), ->
                dom.remove()
              )
            )(log)
            logs.trigger 'log', "<p style='color:#{players[log.side].color}'>#{players[log.side].name}: Send #{log.count} troops from No.#{log.from} to No.#{log.to}.</p>"
          when 'production'
            true
            # logs.trigger 'log', "<p style='color:#{players[log.side].color}'>#{players[log.side].name}: Planet No.#{log.planet} production to #{log.count}</p>"
          when 'occupy'
            $('#planet_' + log.planet).animate({
              opacity: 0
            }, 500, ->
              $(this).animate({opacity: 1}, 500)
            )
          when 'battle'
            if log.winner is log.defence
              logs.trigger 'log', "<p style='color:#{players[log.winner].color}'>#{players[log.winner].name}: Successfully block the #{players[log.attack].name}'s offensive<p>"
            else
              logs.trigger 'log', "<p style='color:#{players[log.winner].color}'>#{players[log.winner].name}: Occupation of the No.#{log.planet} planet</p>"
          when 'tactic'
            tactic = log.tactic
            logs.trigger 'log', "<p style='color: red'>tactic: #{tactic.type}</p>"


      top = []
      for t, i in _.sortBy(players, (p)->
        -(p.planets*10000 + p.units)
      )
        top.push("<div class='top_#{i}' style='color:#{t.color}'><span>#{i+1}</span><p><strong>#{t.name}</strong><br />Planets: #{t.planets}<br />Units: #{t.units}<br />Status: #{t.status}<br />Points: #{t.points}</p></div>")
      $('#top').html(top.join(''))
      $('#round').html("Round #{data.round}/#{map.max_round}")
      $('#status').html(data.status)

ws.onerror = (e)->
  console.log e if config.debug

$('#logs').bind('log', (e, msg)->
  this.innerHTML = msg + this.innerHTML
)

$('#show_logs').click ->
    $("#logs").toggle(200)
