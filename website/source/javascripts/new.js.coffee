config = {
  addr: '127.0.0.1:9999'
  room: 0
  debug: true
}

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
      map.dom = $('#map')
      cell = Math.floor(940/map.map_size[0])
      for p, i in map.planets
        p.id = i
        p.dom = $("<div id='planet_#{i}' class='cell planet' style='margin:#{p.pos[1] * cell}px 0 0 #{p.pos[0] * cell}px'>#{i}</div>").appendTo(map.dom)
        p.dom.data('planet', i)
        map.planets[i] = p
      map.offest_size = $('#planet_0').width();
      
      html = ["<svg style='width:100%;height:#{cell * map.map_size[1]}px;position:absolute'>"]
      for r in map.routes
        from = $('#planet_' + r[0]).offset()
        to = $('#planet_' + r[1]).offset()
        html.push("<line id='route_#{r[0]}_#{r[1]}' x1='#{from.left + (map.offest_size / 2)}' y1='#{from.top + (map.offest_size / 2)}' x2='#{to.left + (map.offest_size / 2)}' y2='#{to.top + (map.offest_size / 2)}' style='stroke:#444;stroke-width:1px' />")
      html.push('</svg>')
      $('body').prepend(html.join(''))
    
    when 'info'
      window.players = data.players
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
          planet.dom.html(planet.id)[0].className = 'cell planet'
      
      for move in data.moves
        ((move)->
          from = map.planets[move[1]].dom
          from_xy = from.offset()
          to = map.planets[move[2]].dom
          to_xy = to.offset()
          dom = $("<div class='move player_#{move[0]}' style='left:#{from_xy.left + map.offest_size/3.7}px;top:#{from_xy.top + map.offest_size/3.7}px'>#{move[3]}</div>")
          map.dom.append(dom)
          dom.animate({left: to_xy.left + map.offest_size/3.7, top: to_xy.top + map.offest_size/3.7}, 1800, ->
            dom.remove()
          )
        )(move)
      
      top = []
      for t, i in _.sortBy(players, (p)->
        -(p.planets*10000 + p.units)
      )
        top.push("<p style='color:#{t.color}'>No.#{i + 1} #{t.name} #{t.planets}/#{t.units}</p>")
      $('#top').html(top.join(''))

ws.onerror = (e)->
  console.log e if config.debug

$('#map').on('mouseenter', '.cell', ->
  data = $.data(this)
  planet = map.planets[data.planet]
  $('#planet').html("<hr /><h3>No.#{data.planet}</h3><p>DEF：X#{planet.def}</p><p>RES：X#{planet.res} +#{planet.cos}</p><p>MAX：#{planet.max}</p>")
).on('mouseleave', '.cell', ->
  $('#planet').html('')
)
