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

SIZE = 60
DUR = 30

log = ()->
    console.log arguments

class Game extends Spine.Module
    @extend(Spine.Events)

    constructor: ()->
        super
        @on_get_message = true

    set_server: (@addr, @room)->
        console.log('set server:', @addr, "with room: ", @room)

        @ws = new WS("ws://#{addr}/info")

        @ws.onmessage = @proxy (e)->
            # log e.data
            return unless @on_get_message
            Game.trigger "data", $.parseJSON(e.data)
        @ws.onerror = (e)-> console.log e
        @ws.onclose = (e)-> console.log "connection closed, refresh please.."
        @ws.onopen = @proxy ()->
            @set_room()
            @get_map()
            @get_info()

    set_room: ()->
        @ws.send JSON.stringify(op: 'setroom', room: @room)
    get_info: ()->
        @ws.send JSON.stringify(op: 'info', room: @room)
    get_map: ()->
        @ws.send JSON.stringify(op: 'map', room: @room)


class GameShower extends Spine.Controller

    constructor: (@game)->
        super
        Game.bind "data", @proxy(@update_data)
        @info = {}
        @map = {}

        @div_scene = $('#board-scene')

        @div_desc = $('#desc')
        @div_status =  $('#game-status')
        @div_round = $('#current-round')
        @div_maxround = $('#max-round')
        @div_logs = $('#logs')

        @div_map_name = $('#map-name')
        @div_map_author = $('#map-author')
        @div_map_desc = $('#map-desc')

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

        text = "<div class=\"desc-planet\">the planet: #{id}<br/>
            <span>def<span> #{planet_info.def}<br/>
            <span>res<span> #{planet_info.res}<br/>
            <span>cos<span> #{planet_info.cos}<br/>
            <span>max<span> #{planet_info.max}<br/>
            </div>
                "

        if @info? and side != null
            player = @info.players[side]
            text += "<div class=\"desc-holds\">with player: #{player.name}
            <div style='background: #{player.color}' class='side-mark'/>
                </div>
            <div class=\"desc-holds\">count: #{count}</div>
                "
        @div_desc.html(text)

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

    update_data: (data)->
        switch data.op
            when "info"
                @info = data
                @update_info()
            when "add"
                false
            when  "map"
                @map = data
                @update_map()
            else
                if data.status != 'ok'
                  console.log(data)

    update_map: ()->
        @animate_time = @map.step * 1000
        # clear all
        @div_scene.find('.planet').remove()
        @div_scene.find('.move').remove()
        # info
        @div_maxround.html(@map.max_round)
        @div_map_name.html(@map.name)
        @div_map_author.html(@map.author)
        @div_map_desc.html(@map.desc)
        @count_route_pos()

        @div_planets = []
        @div_routes = []
        @div_moves = []
        # set board size
        @div_scene.width(SIZE * @map.map_size[0])
        @div_scene.height(SIZE * @map.map_size[1])

        # draw routes
        # for route, i in @map.routes
        #     [_from, to, step] = route
        #     pos1 = @map.planets[_from].pos
        #     pos2 = @map.planets[to].pos

        #     div_route = $ create_svg("line")
        #     div_route.attr
        #         id: "route-"+i
        #         class: "route"
        #         route_id: i
        #         style: "stroke:rgb(0,0,255);stroke-width:3"
        #         x1: pos1[0]*SIZE + SIZE/2
        #         y1: pos1[1]*SIZE + SIZE/2
        #         x2: pos2[0]*SIZE + SIZE/2
        #         y2: pos2[1]*SIZE + SIZE/2

        #     div_route.hover @proxy @show_route_desc
        #     @div_scene.append(div_route)
        #     @svg_routes.push(div_route)

        # draw planets
        for planet, i in @map.planets
            # planet
            div_planet = $("<div/>")
            div_planet.attr
                id: "planet-"+i
                class: "planet"
                planet_id: i
            div_planet.css
                left: planet.pos[0]*SIZE + SIZE/2
                top: planet.pos[1]*SIZE + SIZE/2
                background: "white"
            div_planet.html('?')
            div_planet.hover @proxy @show_planet_desc

            @div_planets.push div_planet
            @div_scene.append div_planet

    update_info: ()->
        @div_round.html(@info.round)
        @update_players()
        @update_logs()

        # game state
        @div_status.html @info.status
        @update_moves()
        # draw holds after animate_time
        # info = @info
        # setTimeout( @proxy(()-> @update_holds(info))
        # , @animate_time)
        @update_holds(@info)

    update_holds: (info)->
        for hold, i in info.holds
            div_planet = @div_planets[i]
            if hold[0] != null
                div_planet.css "background", side_color(hold[0])
            else
                div_planet.css "background", "#ccc"
            div_planet.html(hold[1])

    update_moves: ()->
        # remove old
        @div_scene.find('.move').remove()

        # add new
        for move, i in @info.moves
            [side, _from, to, count, remain] = move
            [pos, next] = @get_route_pos_and_next(_from, to, remain)
            div_move = $("<div/>")
            div_move.attr
                id: "move-"+i
                class: "move"
                move_id: i
            div_move.css
                left: next[0]
                top: next[1]
                background: side_color(side)
            div_move.html(count)
            div_move.hover @proxy @show_move_desc

            # div_move.animate {left: pos[0], top: pos[1]}, @animate_time
            div_move.transition {left: pos[0], top: pos[1]}, @animate_time

            @div_moves.push div_move
            @div_scene.append div_move

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

            dx = (tx - fx) / (step-1)
            dy = (ty - fy) / (step-1)

            move_step = []
            for j in [0..step-1]
                move_step.push [fx+dx*j, fy+dy*j]

            @route_move_pos[to*1000+_from] = move_step
            @route_move_pos[_from*1000+to] = move_step.slice(0).reverse()


    update_players: ()->
        data = []
        list = @info.players.slice()
        for player, i in list
            player.color = side_color(i)

        list.sort (a, b)->
            a.planets - b.planets
        list.reverse()

        for player, i in list
            player_data = [
                "#{player.side} - #{player.name} <div style='background: #{player.color}' class='side-mark'/>",
                "planets: #{player.planets}",
                "units: #{player.units}",
                "#{player.status}",
            ]
            data.push '<div class="player">' + player_data.join("<br/>") + '</div>'
        $('#players').html(data.join("\n"))

    update_logs: ()->
        @logs = ['<div class="log">------------ round: '+@info.round+'</div>']
        for log in @info.logs
            switch log.type
                when "production" then @display_production(log)
                when "battle" then @display_battle(log)

        @div_logs.prepend @logs.join("\n")

    display_battle: (data)->
        #todo
        if data.attack == data.defence
            return
        @logs.push '<div class="log">'+ "planet: #{data.planet}: player #{data.attack} attack player #{data.defence}." + '</div>'

    display_production: (data)->
        #todo
        @logs.push '<div class="log">'+ "planet #{data.planet}: production to #{data.count}." + '</div>'


class Recorder extends Spine.Controller

    constructor: (@game, div)->
        super
        @div = $(div)
        @div_record = @div.find('.record-record')
        @div_replay = @div.find('.record-replay')
        @div_record_count = @div.find('.record-count')
        @div_replay_on = @div.find('.replay-on')

        @div.on 'click', '.record-record', @proxy(@on_record)
        @div.on 'click', '.record-replay', @proxy(@on_replay)
        @on_replay = false
        @on_record = false
        @data_list = []
        @replay_on = 0
        @animate_time = 2000 # fixed replay time
        Game.bind "data", @proxy(@save_data)


    on_record: ()->
        @on_record = not @on_record
        @div_record.toggleClass('on')
        if @on_record
            @data_list = []
            @replay_on = 0
            @game.get_map() #force game get map again

    on_replay: ()->
        @on_replay = not @on_replay
        @div_replay.toggleClass('on')
        @game.on_get_message = not @on_replay # enable/disable game message
        setTimeout(@proxy(@replay_timer), @animate_time)

    replay_timer: ()->
        # console.log "on replay timer: ", @on_replay, @data_list
        return unless @on_replay
        return if @data_list.length <= 0
        Game.trigger "data", @data_list[@replay_on]
        @div_replay_on.html @replay_on
        @replay_on += 1
        @replay_on %= @data_list.length
        setTimeout(@proxy(@replay_timer), @animate_time)

    save_data: (data)->
        return unless @on_record
        @data_list.push data
        @div_record_count.html @data_list.length

# export
window.Game = Game
window.Recorder = Recorder
window.GameShower = GameShower