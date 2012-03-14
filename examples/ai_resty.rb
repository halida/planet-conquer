require 'json'
require 'net/http'

SERVER = "localhost"
PORT = 9999
ROOM = 0

class PlanetAI
  def initialize
    @conn = Net::HTTP.new(SERVER, PORT)
    @room = ROOM
    @last_round_id = -1
  end
  
  def cmd(cmd, data={})
    data['op'] = cmd
    data['room'] = @room
    puts data.to_json
    request = Net::HTTP::Post.new("/cmd")
    request.set_form_data(data)
    response = @conn.request(request)
    result = JSON.parse(response.body)
  end

  def cmd_add
    @me = cmd "add", name: "ai_resty", side: "ruby"
  end

  def cmd_map
    @map = cmd "map"
  end

  def cmd_info
    @info = cmd "info"
  end

  def cmd_moves moves
    cmd "moves",  'id' => @me['id'], 'moves' => moves.to_json
  end

  def step
    if @info['round'] == @last_round_id
      return
    end
    @last_round_id = @info['round'] 
    moves = []
    @info['holds'].each_with_index do | hold, ind |
      (side, count) = hold
      if side == @me['seq']
        routes = @map['routes'].find_all { |r| r[0] == ind }
        puts "count=#{count}"
        puts routes.to_s
        if routes.size > 0
          cnt = ((count - 1) / routes.size).to_i
          routes.each { |r| moves << [cnt, r[0], r[1]] }
        end
      end
    end
    cmd_moves moves
  end
end


ai = PlanetAI.new
ai.cmd_map
ai.cmd_add
while true
  sleep 0.3
  ai.cmd_info
  puts ai.step
end

