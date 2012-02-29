# check WS
if MozWebSocket?
  WS = MozWebSocket
else
  WS = WebSocket

random_color = ()->
    "#fff"
    # todo
draw_circle = (ctx, x, y, r)->
    ctx.arc(x, y, r, 0, Math.PI*2, true)

SIZE = 20

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
            when "add"
                Game.trigger "add", data
            when  "map"
                Game.trigger "map", data
            else
                if data.status != 'ok'
                  console.log(data)

class GameShower extends Spine.Module
    @extend(Spine.Events)

    constructor: (@game, @canvas)->
        Game.bind "map", @proxy((@map)-> @update())
        Game.bind "info", @proxy((@info)-> @update())
        @info = {}
        @map = {}
        @ctx = @canvas[0].getContext("2d")

    update: ()->
        ctx = @ctx
        # clear screen
        ctx.fillStyle = '#ccc'
        ctx.fillRect 0, 0, ctx.canvas.width, ctx.canvas.height
        # draw planets
        for planet in @map.planets
            ctx.fillStyle = '#000'
            x = planet.pos[0]
            y = planet.pos[1]
            draw_circle(ctx, x*SIZE, y*SIZE, SIZE)
            console.log x, y
        ctx.fill()

        # draw holds
        # draw moves
        # todo

# export
window.Game = Game
window.GameShower = GameShower