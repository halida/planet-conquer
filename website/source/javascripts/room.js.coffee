# check WS
if MozWebSocket?
  WS = MozWebSocket
else
  WS = WebSocket

side_color = (i)->
    ['red', 'yellow', 'blue', 'green', 'pink', 'lightblue'][i]

draw_circle = (ctx, x, y, r)->
    ctx.arc(x, y, r, 0, Math.PI*2, true)

create_svg = (obj)-> document.createElementNS('http://www.w3.org/2000/svg', obj)

SIZE = 80
DUR = 30

log = ()->
    console.log arguments

class Game extends Spine.Module
    @extend(Spine.Events)

    constructor: ()->

    set_server: (@addr, @room)->
        console.log('set server:', @addr, "with room: ", @room)

        @ws = new WS("ws://#{addr}/info")

        @ws.onmessage = @proxy (e)-> @onmessage($.parseJSON(e.data))
        @ws.onerror = (e)-> console.log e
        @ws.onclose = (e)-> console.log "connection closed, refresh please.."
        @ws.onopen = @proxy ()->
            @ws.send JSON.stringify(op: 'setroom', room: @room)
            @ws.send JSON.stringify(op: 'map', room: @room)
            @ws.send JSON.stringify(op: 'info', room: @room)

    onmessage: (data)->
        switch data.op
            when "info"
                Game.trigger "info", data
                log "info:", data
            when "add"
                Game.trigger "add", data
            when  "map"
                Game.trigger "map", data
                log "map:", data
            else
                if data.status != 'ok'
                  console.log(data)

class GameShower extends Spine.Controller

    constructor: (@game)->
        super
        Game.bind "map", @proxy((@map)-> @update_map())
        Game.bind "info", @proxy((@info)-> @update_info())
        @info = {}
        @map = {}

        @div_scene = $('#board-scene')
        @svg = @div_scene.svg()
        @svg_moves = []

        @div_desc = $('#desc')
        @div_status =  $('#game-status')
        @div_round = $('#current-round')
        @div_maxround = $('#max-round')
        @div_logs = $('#board-logs')

    show_move_desc: (e)->
        id = $(e.target).attr('move_id')
        [side, _from, to, count, remain] = @info.moves[id]
        @div_desc.html(
            "<div class=\"desc-move\">
            <span>player<span> #{side}<br/>
            <span>from<span> #{_from}<br/>
            <span>to<span> #{to}<br/>
            <span>count<span> #{count}<br/>
            <span>remain<span> #{remain}<br/>
            </div>
                ")

    show_planet_desc: (e)->
        id = $(e.target).attr('planet_id')
        planet_info = @map.planets[id]
        hold = @info.holds[id]
        side = hold[0]
        count = hold[1]
        @div_desc.html(
            "<div class=\"desc-planet\">the planet: #{id}<br/>
            <span>def<span> #{planet_info.def}<br/>
            <span>res<span> #{planet_info.res}<br/>
            <span>cos<span> #{planet_info.cos}<br/>
            <span>max<span> #{planet_info.max}<br/>
            </div>
            <div class=\"desc-holds\">with side: #{side}<br/>
            <div class=\"desc-holds\">count: #{count}<br/>
                ")

    show_route_desc: (e)->
        id = $(e.target).attr('route_id')
        route = @map.routes[id]
        moves = []
        for move in @info.moves
            continue if move[1] != route[0] or move[2] != route[1]
            moves.push move
        @div_desc.html(
            "
            <div class=\"desc-route\">
                step: #{route[2]}
                moves: #{moves}
            </div>
            "
        )

    update_map: ()->
        # info
        @div_maxround.html(@map.max_round)
        @count_route_pos()

        @svg_planets = []
        @svg_routes = []
        # set board size
        @div_scene.width(SIZE * @map.map_size[0])
        @div_scene.height(SIZE * @map.map_size[1])

        # draw routes
        for route, i in @map.routes
            [_from, to, step] = route
            pos1 = @map.planets[_from].pos
            pos2 = @map.planets[to].pos

            svg_route = $ create_svg("line")
            svg_route.attr
                id: "route-"+i
                class: "route"
                route_id: i
                style: "stroke:rgb(0,0,255);stroke-width:3"
                x1: pos1[0]*SIZE + SIZE/2
                y1: pos1[1]*SIZE + SIZE/2
                x2: pos2[0]*SIZE + SIZE/2
                y2: pos2[1]*SIZE + SIZE/2

            # svg_route.hover @proxy @show_route_desc
            @div_scene.append(svg_route)
            @svg_routes.push(svg_route)

        # draw planets
        for planet, i in @map.planets
            # planet
            svg_planet = $ create_svg("circle")
            svg_planet.attr
                id: "planet-"+i
                class: "planet"
                planet_id: i
                cx: planet.pos[0]*SIZE + SIZE/2
                cy: planet.pos[1]*SIZE + SIZE/2
                r: SIZE/4
                fill: "white"
            svg_planet.hover @proxy @show_planet_desc

            #planet text
            svg_planet_text = $ create_svg("text")
            svg_planet_text.text('he')
            svg_planet_text.attr
                id: "planet-text-"+i
                class: "planet-text"
                x: planet.pos[0]*SIZE + SIZE/2
                y: planet.pos[1]*SIZE + SIZE/2
                dx: -SIZE/4
                dy: +SIZE/16

            #add them all
            @div_scene.append svg_planet
            @div_scene.append svg_planet_text


    update_info: ()->
        @div_round.html(@info.round)
        @update_players()
        @update_logs()

        # game state
        @div_status.html @info.status
        # draw holds
        for hold, i in @info.holds
            $('circle#planet-'+i).attr
                fill: side_color(hold[0])
            $('text#planet-text-'+i).text(hold[1])
        @update_moves()

    update_moves: ()->
        # remove old
        for svg_move in @svg_moves
            svg_move.remove()

        # add new
        for move, i in @info.moves
            [side, _from, to, count, remain] = move
            [pos, next] = @get_route_pos_and_next(_from, to, remain)
            svg_move = $ create_svg("circle")
            svg_move.attr
                id: "move-"+i
                class: "move"
                move_id: i
                cx: next[0]
                cy: next[1]
                r: SIZE/8
                fill: side_color(side)
            svg_move.hover @proxy @show_move_desc

            # animation = '<animate attributeName="cx" begin="0s" dur="'+DUR+'s" fill="freeze" from="'+pos[0]+'" to="'+next[0]+'" repeatCount="indefinite"/>'
            # animation += '<animate attributeName="cy" begin="0s" dur="'+DUR+'s" fill="freeze" from="'+pos[1]+'" to="'+next[1]+'" repeatCount="indefinite"/>'
            # svg_move.append(animation)

            @svg_moves.push svg_move
            @div_scene.append svg_move

    get_route_pos_and_next: (_from, to, remain)->
        route = @route_move_pos[_from*1000 + to]
        return [route[remain-1], route[remain]]

    count_route_pos: ()->
        @route_move_pos = {}

        for route, i in @map.routes
            [_from, to, step] = route
            [fx, fy] = @map.planets[_from].pos
            [tx, ty] = @map.planets[to].pos
            tx = tx*SIZE + SIZE/2
            ty = ty*SIZE + SIZE/2
            fx = fx*SIZE + SIZE/2
            fy = fy*SIZE + SIZE/2

            dx = (tx - fx) / (step)
            dy = (ty - fy) / (step)

            move_step = []
            for j in [0..step]
                move_step.push [fx+dx*j, fy+dy*j]

            @route_move_pos[to*1000+_from] = move_step
            @route_move_pos[_from*1000+to] = move_step.slice(0).reverse()


    update_players: ()->
        data = []
        for player in @info.players
            player_data = [
                "#{player.side} - #{player.name}",
                "planets: #{player.planets}",
                "unit: #{player.unit}",
                "#{player.status}",
            ]
            data.push '<div class="player">' + player_data.join("<br/>") + '</div>'
        $('#players').html(data.join("\n"))

    update_logs: ()->
        @logs = ['<div class="log">round: '+@info.round+'</div>']
        for log in @info.logs
            switch log.type
                when "production" then @display_production(log)
                when "battle" then @display_battle(log)

        @div_logs.prepend @logs.join("\n")

    display_battle: (data)->
        #todo
        @logs.push '<div class="log">'+ "planet: #{data.planet}: player #{data.attack} attack player #{data.defence}." + '</div>'

    display_production: (data)->
        #todo
        @logs.push '<div class="log">'+ "planet #{data.planet}: production to #{data.count}." + '</div>'


# export
window.Game = Game
window.GameShower = GameShower