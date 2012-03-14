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
      td_width = 820/data.map_size[0] - 4
      html = []
      _(data.map_size[1]).times(->
        html.push('<tr>')
        _(data.map_size[0]).times(->
          html.push "<td style='width:#{td_width}px;height:#{td_width}px' id='#{i}'>&nbsp;</td>"
          i = i + 1
        )
        html.push('</tr>')
      )
      map.dom.html(html.join(''))
      for planet, i in map.planets
        planet.id = i
        planet.dom = $('#' + (planet.pos[0] + (planet.pos[1] * data.map_size[0]))).addClass('planet')
        map.planets[i] = planet
      
    when 'info'
      for hold, planet_id in data.holds
        if hold[0]
          map.planets[planet_id].dom.html(data.players[hold[0]].name + ' ' + hold[1])
        else
          map.planets[planet_id].dom.html('')
      for move in data.moves
        from = map.planets[move[1]].dom.position()
        to = map.planets[move[2]].dom.position()
        dom = $("<div class='move' style='left:#{from.left}px;top:#{from.top}px'>#{data.players[move[0]].name} #{move[3]}</div>")
        map.dom.after(dom)
        dom.animate({left: to.left, top: to.top}, 4000, ->
          $(this).remove()
        )

ws.onerror = (e)->
  console.log e if config.debug


