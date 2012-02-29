# check WS
if MozWebSocket?
  WS = MozWebSocket
else
  WS = WebSocket

class Game extends Spine.Module

    constructor: ()->

    set_server: (@addr, @room)->
        console.log('set server:', @addr, "with room: ", @room)

        @ws = new WS("ws://#{addr}/info")

        @ws.onmessage = @proxy (e)-> @onmessage(e.data)
        @ws.onerror = (e)-> console.log e
        @ws.onclose = (e)-> console.log "connection closed, refresh please.."
        @ws.onopen = @proxy ()->
            @ws.send JSON.stringify(op: 'setroom', room: @room)
            @ws.send JSON.stringify(op: 'map', room: @room)
            @ws.send JSON.stringify(op: 'info', room: @room)

    onmessage: (data)->
        switch data.op
            when "info"
                @trigger "info", data
            when "add"
                @trigger "add", data
            when  "map"
                @trigger "map", data
            else
                if data.status != 'ok'
                  console.log(data)

# export
window.Game = Game