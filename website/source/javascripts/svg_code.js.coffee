# container = new Group().addTo(stage)
# for r in [0..10]
#     for c in [0..10]
#         new Rect(c*10, r*10, 10, 10).addTo(container).fill('random')
#

d = {}

stage.on 'message:map', (data)->
    d.map = map = data
    console.log 'message map'
    cell = Math.floor(940/map.map_size[0])
    cell = 30

    for p, i in map.planets
        p.id = i
        c = new Circle(p.pos[0] * cell, p.pos[1] * cell, cell/2 + 2).fill('green').addTo(stage)
        continue

        $("<div id='planet_#{i}' planet_type='#{p.type || 'normal'}' class='cell planet planet-#{p.type}' style='margin:#{p.pos[1] * cell}px 0 0 #{p.pos[0] * cell}px'></div>").appendTo(map.dom)
        p.dom = $('#planet_' + i)
        p.dom.data('planet', i)
        map.offest_size = $('#planet_0').width() if i == 0
        def = []
        _.times(Math.floor(p.def + 1), ->
          def.push '⊙'
        )
        def = def.join ' '
        res = []
        _.times(Math.floor(p.res), ->
          res.push '★'
        )
        res = res.join ' '
        p.dom.after("<span class='planet_info' style='margin:#{p.pos[1] * cell - 16}px 0 0 #{p.pos[0] * cell - map.offest_size / 2}px'>⊙#{p.def} ★#{p.res} + #{p.cos}</span><span class='planet_info' style='margin:#{p.pos[1] * cell + map.offest_size + 4}px 0 0 #{p.pos[0] * cell - map.offest_size / 2}px'>≤#{p.max}</span>").next()
        map.planets[i] = p


    for r in map.routes
        continue if r[0] > r[1]
        from = map.planets[r[0]].pos
        to = map.planets[r[1]].pos
        console.log 'fuck', from, to
        new Path().moveTo(from[0]*cell, from[1]*cell).lineTo(to[0]*cell, to[1]*cell).stroke('#444', 2, 'stroke-dasharray': "3,3").addTo(stage)

stage.on 'message:info', (info)->
    console.log 'message info'
    # new Rect(10, 10, 300, 100).fill('random').addTo(stage)

stage.on 'message:echo', (data)->
    stage.sendMessage 'echo', data
