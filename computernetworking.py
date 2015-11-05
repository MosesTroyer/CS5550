from flask import Flask, render_template
from flask_socketio import SocketIO, emit
application = Flask(__name__)
application.config['SECRET_KEY'] = "secret"
socketio = SocketIO(application)

@application.route("/")
def hello():
	return render_template("index.html")

@socketio.on("connect", namespace="/rpg")
def test_connect():
	print("someone connected")

@socketio.on("chatMessage", namespace="/rpg")
def chat_message(data):
	emit("chatMessage", data, broadcast=True) 

if __name__ == "__main__":
	#application.host = "0.0.0.0"
	socketio.run(application, host='0.0.0.0')
	#application.run(host="0.0.0.0")
