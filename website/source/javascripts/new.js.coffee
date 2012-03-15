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
      _(data.map_size[1] * data.map_size[0]).times(->
        html.push "<div class='cell' style='width:#{td_width}px;height:#{td_width}px' id='#{i}'>&nbsp;</div>"
        i = i + 1
      )
      map.dom.html(html.join(''))
      for planet, i in map.planets
        planet.id = i
        planet.dom = $('#' + (planet.pos[0] + (planet.pos[1] * data.map_size[0]))).addClass('planet').data('planet', i)
        map.planets[i] = planet
      
    when 'info'
      window.players = data.players
      for hold, planet_id in data.holds
        planet = map.planets[planet_id]
        planet.hold = hold[0]
        if hold[0] isnt null
          planet.dom.html(data.players[hold[0]].name + ' ' + hold[1])
        else
          planet.dom.html('')
      for move in data.moves
        ((move)->
          from = map.planets[move[1]].dom.position()
          to = map.planets[move[2]].dom.position()
          dom = $("<div class='move' style='left:#{from.left}px;top:#{from.top}px'>#{data.players[move[0]].name} #{move[3]}</div>")
          map.dom.append(dom)
          dom.animate({left: to.left, top: to.top}, 4000, ->
            dom.remove()
          )
        )(move)

ws.onerror = (e)->
  console.log e if config.debug

$('#map').on('hover click', '.cell', ->
  data = $.data(this)
  if typeof data.planet isnt 'undefined'
    planet = map.planets[data.planet]
    if planet.hold is null
      hold = '無'
    else
      hold = "#{players[planet.hold].name} (#{players[planet.hold].planets})"
    $('#cell').html("<h3>No.#{this.id}</h3><p>類型：星球</p><p>防御系数：X#{planet.def}</p><p>资源系数：X#{planet.res} +#{planet.cos}</p><p>最大生产量：#{planet.max}</p><p>佔領者：#{hold}</p>")
  else
    $('#cell').html("<h3>No.#{this.id}</h3><p>類型：無</p>")
)
