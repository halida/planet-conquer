#--------------------------------------
# music
onmusic = true
audio = $('audio#music')[0]
onmusic_btn = $('#music_play')

onmusic_btn.click ->
    if onmusic
        audio.pause()
        onmusic_btn.text("=")
    else
        audio.play()
        onmusic_btn.text(">")
    onmusic = not onmusic

#--------------------------------------
# background
bg_img = $('.bg img')
bg_img.load ->
    bg_img.addClass('on')

#--------------------------------------
# game play
onplay = true
onplay_btn = $('#game_play')

onplay_btn.click ->
    if onplay
        onplay_btn.text("=")
    else
        onplay_btn.text(">")
    onplay = not onplay

#--------------------------------------
# websocket
if MozWebSocket?
    WS = MozWebSocket
else
    WS = WebSocket

init_websocket = ->
    ws = new WS("ws://#{config.addr}/info")
    ws._send = ws.send

    ws.send = (data)->
        if typeof data is 'string'
            data = {op: data}

        data.room = config.room
        this._send JSON.stringify(data)

    ws.onopen = ->
        ws.send 'setroom'
        ws.send 'map'
        ws.send 'info'

    ws.onmessage = (e)->
        return unless onplay
        data = $.parseJSON(e.data)
        console.log data if config.debug
        switch data.op
            when 'map'
                init_map(data)
            when 'info'
                update_info(data)

    ws.onerror = (e)->
        console.log e if config.debug

#--------------------------------------
# display game
board = Raphael('map')
window.mapinfo =
    logs: $('#logs').html(''),
    planet_size: 21

window.init_map = (data)->
    console.log 'map'
    mapinfo.map = map = data
    mapinfo.cell = cell = Math.floor(940/(map.map_size[0]+1))
    board.setViewBox(-40, -40, cell*(map.map_size[0]+1), cell*(map.map_size[1]+1))
    console.log 'cell:', cell
    planet_size = mapinfo.planet_size

    # show map info
    info = "<h2 id='map-name'>#{map.name}</h2>"
    info += " <div id='map-author'>author: #{map.author}</div>"
    info += "<div id='map-desc'>#{map.desc}</div>"
    $('#map-info').html(info)

    # draw routes
    for r in map.routes
        continue if r[0] > r[1]
        from = map.planets[r[0]].pos
        to = map.planets[r[1]].pos
        c = board.path("M #{from[0]*cell} #{from[1]*cell} L#{to[0]*cell} #{to[1]*cell}")
        c.attr("stroke", "#444")
        c.attr('stroke-width', 2)
        c.attr('stroke-dasharray', '-')

    # draw planets
    mapinfo.planet_objs = []
    mapinfo.planet_nums = []
    for p, i in map.planets
        p.id = i
        c = board.circle(p.pos[0] * cell, p.pos[1] * cell, planet_size)
        c.attr("fill", "#000")
        c.attr("stroke", "#fff")
        c.attr("stroke-width", 2)
        mapinfo.planet_objs.push(c)

        tt = board.text(p.pos[0] * cell, p.pos[1] * cell - planet_size - 10, "⊙#{p.def} ★#{p.res} + #{p.cos}")
        tt.attr('font-size', 11).attr('width', 84).attr('fill', '#888')

        td = board.text(p.pos[0] * cell, p.pos[1] * cell + planet_size + 11, "≤#{p.max}")
        td.attr('font-size', 11).attr('width', 84).attr('fill', '#888')

        tp = board.text(p.pos[0] * cell, p.pos[1] * cell, "0")
        tp.attr('font-size', 15).attr('width', planet_size * 2).attr('fill', '#000')
        mapinfo.planet_nums.push(tp)



window.update_info = (data)->
    console.log 'info'
    map = mapinfo.map

    mapinfo.players = players = data.players
    return unless data.players
    players[0].color = '#EE2C44' if players[0]
    players[1].color = '#42C3D9' if players[1]
    players[2].color = '#E96FA9' if players[2]
    players[3].color = '#A5CF4E' if players[3]

    # set planet info
    for hold, planet_id in data.holds
        planet = map.planets[planet_id]
        planet.hold = hold[0]
        if hold[0] isnt null
            mapinfo.planet_nums[planet_id].attr('text', hold[1])
            mapinfo.planet_objs[planet_id].attr('fill', players[hold[0]].color)
        else
            mapinfo.planet_nums[planet_id].attr('text', '0')
            mapinfo.planet_objs[planet_id].attr('fill', 'black')

    # set uplayer info
    top = []
    for t, i in _.sortBy(players, (p)->
        -(p.planets*10000 + p.units)
    )
        top.push(
            "<div class='top_#{i}' style='color:#{t.color}'>"
            "<span>#{i+1}</span><p><strong>#{t.name}</strong><br />"
            "Planets: #{t.planets}<br />Units: #{t.units}<br />"
            "status: #{t.status}<br/>Points: #{t.points}</p></div>")

    $('#top').html(top.join(''))
    $('#round').html("Round #{data.round}/#{map.max_round}")
    $('#status').html(data.status)

    # set event by log
    console.log data.logs
    for log in data.logs
        switch log.type
            when 'move'
                start_move(log)
            when 'production'
                true
            when 'occupy'
                start_occupy(log)
            when 'battle'
                if log.winner is log.defence
                    mapinfo.logs.trigger 'log',
                        "<p style='color:#{players[log.winner].color}'>#{players[log.winner].name}:"
                        " Successfully block the #{players[log.attack].name}'s offensive<p>"
                else
                    mapinfo.logs.trigger 'log',
                        "<p style='color:#{players[log.winner].color}'>#{players[log.winner].name}:"
                        " Occupation of the No.#{log.planet} planet</p>"
            when 'tactic'
                tactic = log.tactic
                mapinfo.logs.trigger 'log', "<p style='color: red'>tactic: #{tactic.type}</p>"

start_move = (log)->
    move = log
    cell = mapinfo.cell
    players = mapinfo.players

    f = mapinfo.map.planets[move.from].pos
    from_xy = [f[0]*cell, f[1]*cell]

    t = mapinfo.map.planets[move.to].pos
    to_xy = [t[0]*cell, t[1]*cell]

    c = board.circle(from_xy[0], from_xy[1], mapinfo.planet_size / 2).attr('fill', players[log.side].color).attr('stroke', players[log.side].color)
    w = board.text(from_xy[0], from_xy[1], log.count).attr('fill', 'black').attr('height', mapinfo.planet_size / 2).attr('width', mapinfo.planet_size / 2)
    c.animate({cx: to_xy[0], cy: to_xy[1]}, mapinfo.map.step * (move.step-1) * 1000, '<>', -> c.remove())
    w.animate({ x: to_xy[0],  y: to_xy[1]}, mapinfo.map.step * (move.step-1) * 1000, '<>', -> w.remove())

    mapinfo.logs.trigger 'log',
        "<p style='color:#{players[log.side].color}'>#{players[log.side].name}:"
        " Send #{log.count} troops from No.#{log.from} to No.#{log.to}.</p>"

start_occupy = (log)->
    obj = mapinfo.planet_objs[log.planet]

    obj.animate {"fill-opacity": 0}, 500, 'linear', ->
        obj.animate({"fill-opacity": 1}, 500)

#--------------------------------------
# log
$('#logs').bind('log', (e, msg)->
    this.innerHTML = msg + this.innerHTML
)

$('#show_logs').click ->
    $("#logs").toggle(200)

#--------------------------------------
# main
onmusic_btn.click()
# onplay_btn.click()
init_websocket()