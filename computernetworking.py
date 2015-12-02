from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room
from threading import Thread
from gevent import monkey
import datetime, time, json
application = Flask(__name__)
application.config['SECRET_KEY'] = "secret"
socketio = SocketIO(application)

playerActions = {}
playerList = {}

monsterTypes = {
	"slime": {
		"name": "Slime",
		"level": 1,
		"HP": 2,
		"currentHP": 2,
		"mana": 1,
		"currentMana": 1,
		"stats": {
			"strength": 1,
			"fortitude": 1,
			"intelligence": 1,
			"constitution": 1,
			"agility": 1
		}
	}

}

##### WEBPAGES #####
@application.route("/")
def index():
	return render_template("index.html")

##### RPG SOCKET EVENTS #####
@socketio.on("connect", namespace="/rpg")
def rpg_connect():
	pass

@socketio.on("playerJoin", namespace="/rpg")
def player_join(dataInput):
	data = json.loads(dataInput);
	inRoom = False
	for room in playerList:
		if (not inRoom) and len(playerList[room]) < 4:
			join_room(room)
			playerList[room].append((data['player'])['name'])
			inRoom = True
			confirm_player_join(room, data['player'])
			break
	if not inRoom:
		name = str(datetime.datetime.now())
		join_room(name)
		thread = Thread(target=battle_loop, args=(name, data['player']))
		thread.start()
		confirm_player_join(name, data['player'])

def confirm_player_join(roomName, player):
	#build player data
	player["HP"] = 10
	player["level"] = 1
	player["exp"] = 0
	player["currentHP"] = 10
	player["mana"] = 10
	player["currentMana"] = 10
	stats = {"strength": 1, "fortitude": 1, "intelligence": 1, "constitution": 1, "agility": 1}
	player["stats"] = stats
	emit("confirmPlayerJoin", {"roomName": roomName, "player": player}, room=roomName)

@socketio.on("chatMessage", namespace="/rpg")
def chat_message(dataInput):
	data = json.loads(dataInput)
	emit("chatMessage", data, room=data['roomName'])

@socketio.on("playerAction", namespace="/rpg")
def player_action(dataInput):
	data = json.loads(dataInput)
	(playerActions[data["roomName"]])[(data["player"])["name"]] = data["action"]

##### BATTLE CONTROL #####
def battle_loop(roomName, initialPlayer):
	playerActions[roomName] = {}
	playerList[roomName] = [initialPlayer["name"]]
	rollCall = {}
	actions = {}
	monsters = []
	monsters.append(create_monster())

	while len(playerList[roomName]) > 0:
		send_monsters(roomName, monsters)
		turn_start(roomName)
		for i in range(10):
			time.sleep(1)
			socketio.emit("heartbeat", str(i) + " seconds in", room=roomName, namespace="/rpg")
		turn_end(roomName)
		
		#Assemble player actions
		for player in playerList[roomName]:
			if player in playerActions[roomName]:
				actions[player] = (playerActions[roomName]).pop(player)
				rollCall[player] = 0
				print(actions[player])
			else:
				if player in rollCall:
					rollCall[player] = rollCall[player] + 1
					if rollCall[player] >= 3:
						socketio.emit("kickPlayer", player, room=roomName, namespace="/rpg")
						rollCall.pop(player, None)
						(playerList[roomName]).remove(player)
				else:
					rollCall[player] = 1

		#assemble monster actions

		#make all actions happen

		actions = {}
	
	playerList.pop(roomName, None)

def create_monster():
	return monsterTypes["slime"]

def send_monsters(roomName, monsters):
	socketio.emit("monstersBroadcast", monsters, room=roomName, namespace="/rpg")

def turn_start(roomName):
	socketio.emit("turnStart", {"data": ""}, room=roomName, namespace="/rpg")

def turn_end(roomName):
	socketio.emit("turnEnd", {"data": ""}, room=roomName, namespace="/rpg")

if __name__ == "__main__":
	socketio.run(application, host='0.0.0.0')
