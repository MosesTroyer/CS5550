from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room
from threading import Thread
from gevent import monkey
import datetime, time, json
application = Flask(__name__)
application.config['SECRET_KEY'] = "secret"
socketio = SocketIO(application)
#monkey.patch_all()

#TODO ASK ALA - Should I be using a database to store these variables, or is it fine
#for this smaller application?
playerActions = {}
playerList = {}

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
	emit("confirmPlayerJoin", {"roomName": roomName, "player": player}, room=roomName)

@socketio.on("chatMessage", namespace="/rpg")
def chat_message(dataInput):
	data = json.loads(dataInput);
	emit("chatMessage", data, room=data['roomName'])

##### BATTLE CONTROL #####
def battle_loop(roomName, initialPlayer):
	playerActions[roomName] = {}
	playerList[roomName] = [initialPlayer["name"]]
	rollCall = {}

	for i in range(10):
		turn_start(roomName)
		time.sleep(10)
		turn_end(roomName)
		
		#Assemble player actions
		for player in playerList[roomName]:
			if player in playerActions:
				#group into list
				#remove from roll call
				pass
			else:
				if player in rollCall:
					rollCall[player] = rollCall[player] + 1
				else:
					rollCall[player] = 1

		for player in rollCall:
			if rollCall[player] >= 3:
				socketio.emit("kickPlayer", player, room=roomName, namespace="/rpg")
				rollCall.pop(player, None)
				(playerList[roomName]).remove(player)


def turn_start(roomName):
	socketio.emit("turnStart", {"data": ""}, room=roomName, namespace="/rpg")

def turn_end(roomName):
	socketio.emit("turnEnd", {"data": ""}, room=roomName, namespace="/rpg")

if __name__ == "__main__":
	socketio.run(application, host='0.0.0.0')
