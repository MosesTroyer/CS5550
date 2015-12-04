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
	},

	"spider": {
		"name": "Giant Spider",
		"level": 2,
		"HP": 5,
		"currentHP": 5,
		"mana": 1,
		"currentMana": 1,
		"stats": {
			"strength": 2,
			"fortitude": 3,
			"intelligence": 2,
			"constitution": 1,
			"agility": 3
		}
	},

	"harpy": {
		"name": "Harpy",
		"level": 5,
		"HP": 14,
		"currentHP": 14,
		"mana": 5,
		"currentMana": 5,
		"stats": {
			"strength": 3,
			"fortitude": 2,
			"intelligence": 5,
			"constitution": 4,
			"agility": 5
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
			inRoom = True
			playerList[room].append(confirm_player_join(room, data['player']))
			break
	if not inRoom:
		name = str(datetime.datetime.now())
		join_room(name)
		thread = Thread(target=battle_loop, args=(name, confirm_player_join(name, data['player'])))
		thread.start()	

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
	return player

@socketio.on("chatMessage", namespace="/rpg")
def chat_message(dataInput):
	data = json.loads(dataInput)
	emit("chatMessage", data, room=data['roomName'])

@socketio.on("playerAction", namespace="/rpg")
def player_action(dataInput):
	data = json.loads(dataInput)
	(playerActions[data["roomName"]])[(data["player"])["name"]] = data

##### BATTLE CONTROL #####
def battle_loop(roomName, initialPlayer):
	playerActions[roomName] = {}
	playerList[roomName] = [initialPlayer]
	rollCall = {}
	actions = []
	monsters = []
	monsters.append(create_monster())

	while len(playerList[roomName]) > 0:
		send_monsters(roomName, monsters)
		turn_start(roomName)
		actions = []
		for i in range(10):
			time.sleep(1)
			socketio.emit("heartbeat", str(i) + " seconds in", room=roomName, namespace="/rpg")
		turn_end(roomName)
		
		#Assemble player actions
		for player in playerList[roomName]:
			if player["name"] in playerActions[roomName]: 
				actions.append((playerActions[roomName]).pop(player["name"]))
				rollCall[player["name"]] = 0
				#if((actions[player])["action"] == "attack"):
				#	socketio.emit("heartbeat", "you attacked", room=roomName, namespace="/rpg")
			else: #Inactivity logic
				if player["name"] in rollCall:
					(rollCall[player["name"]]) = rollCall[player["name"]] + 1
					if rollCall[player["name"]] >= 3:
						socketio.emit("kickPlayer", player["name"], room=roomName, namespace="/rpg")
						rollCall.pop(player["name"], None)
						(playerList[roomName]).remove(player)
				else:
					rollCall[player["name"]] = 1

		#assemble monster actions
		for mon in monsters:
			pass
			#random select player character
			#create attack

		#sort actions based on speed

		#make all actions happen
		for action in actions:
			if action["action"] == "attack":
				damage = attack(action["player"], action["target"], roomName)
				for mon in monsters:
					if mon["name"] == (action["target"])["name"]:
						monsters.remove(mon)
						monsters.append(action["target"])

	playerList.pop(roomName, None)

def create_monster():
	return monsterTypes["slime"]

def send_monsters(roomName, monsters):
	socketio.emit("monstersBroadcast", monsters, room=roomName, namespace="/rpg")

##### ACTIONS #####
def attack(attacker, target, roomName):
	damage = (attacker["stats"])["strength"]

	target["currentHP"] = target["currentHP"] - damage

	data = {}
	data["attacker"] = attacker
	data["target"] = target
	data["damage"] = damage
	data["message"] = attacker["name"] + " attacked " + target["name"] + " for " + str(damage) + " damage!"
	socketio.emit("gameUpdate", data, room=roomName, namespace="/rpg")
	return damage

def turn_start(roomName):
	socketio.emit("turnStart", {"data": ""}, room=roomName, namespace="/rpg")

def turn_end(roomName):
	socketio.emit("turnEnd", {"data": ""}, room=roomName, namespace="/rpg")

if __name__ == "__main__":
	socketio.run(application, host='0.0.0.0')
