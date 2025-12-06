import argparse
import serial
from flask import Flask, request, send_from_directory
from flask_socketio import SocketIO

app = Flask(__name__, static_folder='static')
socketio = SocketIO(app)

testing_controller = 4 # VIRTUAL_CONTROLLER_1

rok_action = {
  "press": 0,
  "release": 1,
  "edit": 2,
  "enable": 3,
  "disable": 4,
  "reset": 5
}

button_map = {
    0: {'name': 'a', 'rok_cmd': 8},
    1: {'name': 'b', 'rok_cmd': 9}
}

@socketio.on('gamepad')
def handle_gamepad(data):
    button_index = data['button']
    pressed = data['pressed']
    
    if button_index in button_map:
        btn = button_map[button_index]
        action = "press" if pressed else "release"
        arduino.write(bytes([rok_action[action], testing_controller, btn['rok_cmd']]))

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/control.js')
def script():
    return send_from_directory('static', 'control.js')

@app.route('/press', methods=['POST'])
def press():
    data = request.json
    controller = data['controller']
    button = data['button']
    arduino.write(bytes([rok_action["press"], controller, button]))
    return "OK"

@app.route('/release', methods=['POST'])
def release():
    data = request.json
    controller = data['controller']
    button = data['button']
    arduino.write(bytes([rok_action["release"], controller, button]))
    return "OK"

@app.route('/edit', methods=['POST'])
def edit():
    data = request.json
    controller = data['controller']
    selection = data['selection']
    arduino.write(bytes([rok_action["edit"], controller, selection]))
    return "OK"

@app.route('/enable', methods=['POST'])
def enable():
    controller = request.json['controller']
    arduino.write(bytes([rok_action["enable"], controller, 0]))
    return "OK"

@app.route('/disable', methods=['POST'])
def disable():
    controller = request.json['controller']
    arduino.write(bytes([rok_action["disable"], controller, 0]))
    return "OK"

@app.route('/reset', methods=['POST'])
def reset():
    arduino.write(bytes([rok_action["reset"], 0, 0]))
    return "OK"

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Starts the Arduino SmartPort web controller')
    parser.add_argument('serial_device', help='The serial device name of your Arduino')
    parser.add_argument('-i', '--ip', help='What IP the server will listen on', default='0.0.0.0')
    parser.add_argument('-p', '--port', help='What port the server will listen on', default='5000')
    args = parser.parse_args()
    arduino = serial.Serial(args.serial_device, 115200, timeout=1)
    socketio.run(app)
