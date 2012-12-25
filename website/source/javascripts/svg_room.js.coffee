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
# display game
window.board = board = bonsai.run(
    document.getElementById('map'),
    url: config.code_url
    )

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
        console.log 'xxx'
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

board.on 'load', ->
    console.log 'load'
    init_websocket()

    board.on 'message:echo', (data)->
        console.log 'echo: ', data

#--------------------------------------
# display game

window.init_map = (data)->
    window.map = data

    # show map info
    info = "<h2 id='map-name'>#{map.name}</h2>"
    info += " <div id='map-author'>author: #{map.author}</div>"
    info += "<div id='map-desc'>#{map.desc}</div>"
    $('#map-info').html(info)

    board.sendMessage('map', data)


window.update_info = (data)->
    board.sendMessage('info', data)
    return

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
              dom = $("<div class='move player_#{move.side}' " + \
                "style='left:#{from_xy.left + map.offest_size/3.7}px;top:#{from_xy.top + map.offest_size/3.7}px'" + \
                ">#{move.count}</div>")
              map.dom.append(dom)
              dom.animate({left: to_xy.left + map.offest_size/3.7, top: to_xy.top + map.offest_size/3.7}, map.step * (move.step-1), ->
                dom.remove()
              )
            )(log)
            logs.trigger 'log',
              "<p style='color:#{players[log.side].color}'>#{players[log.side].name}:" + \
              " Send #{log.count} troops from No.#{log.from} to No.#{log.to}.</p>"
          when 'production'
            true
          when 'occupy'
            $('#planet_' + log.planet).animate({
              opacity: 0
            }, 500, ->
              $(this).animate({opacity: 1}, 500)
            )
          when 'battle'
            if log.winner is log.defence
              logs.trigger 'log',
                "<p style='color:#{players[log.winner].color}'>#{players[log.winner].name}:" + \
                " Successfully block the #{players[log.attack].name}'s offensive<p>"
            else
              logs.trigger 'log',
                "<p style='color:#{players[log.winner].color}'>#{players[log.winner].name}:" + \
                " Occupation of the No.#{log.planet} planet</p>"
          when 'tactic'
            tactic = log.tactic
            logs.trigger 'log', "<p style='color: red'>tactic: #{tactic.type}</p>"

    top = []
    for t, i in _.sortBy(players, (p)->
        -(p.planets*10000 + p.units)
    )
        top.push("<div class='top_#{i}' style='color:#{t.color}'><span>#{i+1}</span><p><strong>#{t.name}</strong><br />Planets: #{t.planets}<br />Units: #{t.units}<br />status: #{t.status}<br/>Points: #{t.points}</p></div>")
    $('#top').html(top.join(''))
    $('#round').html("Round #{data.round}/#{map.max_round}")
    $('#status').html(data.status)

#--------------------------------------
# log
$('#logs').bind('log', (e, msg)->
    this.innerHTML = msg + this.innerHTML
)

$('#show_logs').click ->
    $("#logs").toggle(200)

#--------------------------------------
# log
onmusic_btn.click()
# onplay_btn.click()