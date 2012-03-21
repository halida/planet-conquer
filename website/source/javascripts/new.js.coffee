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
      i = 0
      html = []
      _(data.map_size[1] * data.map_size[0]).times(->
        html.push "<div class='cell' id='#{i}'>&nbsp;</div>"
        i = i + 1
      )
      map.dom.html(html.join(''))
      for planet, i in map.planets
        planet.id = i
        planet.dom = $('#' + (planet.pos[0] + (planet.pos[1] * data.map_size[0]))).addClass('planet').data('planet', i)
        map.planets[i] = planet
      
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
          planet.dom.html('')[0].className = 'cell planet'
      
      for move in data.moves
        ((move)->
          from = map.planets[move[1]].dom
          from_xy = from.position()
          to = map.planets[move[2]].dom
          to_xy = to.position()
          dom = $("<div class='move player_#{move[0]}' style='left:#{from_xy.left + from.width()/3.2}px;top:#{from_xy.top + from.height()/3.2}px'>#{move[3]}</div>")
          map.dom.append(dom)
          dom.animate({left: to_xy.left + to.width()/3.2, top: to_xy.top + to.height()/3.2}, 1700, ->
            dom.remove()
          )
        )(move)
      
      top = []
      for t, i in _.sortBy(players, (player)->
        -player.planets
      )
        top.push("<p style='color:#{t.color}'>No.#{i + 1} #{t.name} #{t.planets}/#{t.units}</p>")
      $('#top').html(top.join(''))

ws.onerror = (e)->
  console.log e if config.debug

$('#map').on('mouseenter', '.cell.planet,.cell.player_0,.cell.player_1,.cell.player_2,.cell.player_3', ->
  data = $.data(this)
  planet = map.planets[data.planet]
  if planet.hold is null
    hold = '無'
  else
    hold = "#{players[planet.hold].name} (#{players[planet.hold].planets})"
  $('#planet').html("<hr /><p>DEF：X#{planet.def}</p><p>RES：X#{planet.res} +#{planet.cos}</p><p>MAX：#{planet.max}</p><p>OWNER：#{hold}</p>")
).on('mouseleave', '.cell.planet,.cell.player_0,.cell.player_1,.cell.player_2,.cell.player_3', ->
  $('#planet').html('')
)
