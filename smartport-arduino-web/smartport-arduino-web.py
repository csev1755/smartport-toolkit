import argparse
import serial
import signal
import sys
from enum import Enum
from flask import Flask, request, send_from_directory
from flask_socketio import SocketIO
from upnp import UPnPPortMapper

app = Flask(__name__, static_folder='static')
socketio = SocketIO(app)

class Controller:
    def __init__(self, index, selection):
        self.index = index
        self.selection = selection
        self.button_map = {
            0:  self.Command.A,
            1:  self.Command.B,
            3:  self.Command.X,
            2:  self.Command.Y,
            4:  self.Command.LEFT_TRIGGER,
            5:  self.Command.RIGHT_TRIGGER,
            12: self.Command.DPAD_UP,
            13: self.Command.DPAD_DOWN,
            14: self.Command.DPAD_LEFT,
            15: self.Command.DPAD_RIGHT
        }
        command_deck.send_command(
            command_deck.Command.EDIT,
            self.index,
            self.selection
            )

    class Command(Enum):
        SELECT = 0
        LEFT_TRIGGER = 1
        SHARE_SWITCH = 2
        IS_16_SEL = 3
        DPAD_UP = 4
        DPAD_DOWN = 5
        DPAD_RIGHT = 6
        DPAD_LEFT = 7
        A = 8
        B = 9
        X = 10
        Y = 11
        RIGHT_TRIGGER = 12

    def send_input(self, input):
        if input['button'] in self.button_map:
            command = CommandDeck.Command.PRESS if input['pressed'] else CommandDeck.Command.RELEASE
            button = self.button_map[input['button']]
            command_deck.send_command(command, self.index, button.value)

class CommandDeck:
    def __init__(self, serial_device=None):
        self.smartport = None
        if serial_device is not None:
            self.smartport = serial.Serial(serial_device, 115200, timeout=1)
            print(f"Connected to SmartPort device at {serial_device}")
        else:
            print("No SmartPort device specified, will only print commands for debugging")
    
    class Command(Enum):
        PRESS = 0
        RELEASE = 1
        EDIT = 2
        ENABLE = 3
        DISABLE = 4
        RESET = 5

    def send_command(self, command: Command, controller, value):
        if self.smartport is not None:
            self.smartport.write(bytes([command.value, controller, value]))
        else:
            print(f"DEBUG - Action: {command.value} Controller: {controller} Value: {value}")

@socketio.on('gamepad')
def handle_gamepad(data):
    controller.send_input(data)

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/control.js')
def script():
    return send_from_directory('static', 'control.js')

@app.route('/press', methods=['POST'])
def press():
    data = request.json
    command_deck.send_command(command_deck.Command.PRESS, data['controller'], data['button'])
    return "OK"

@app.route('/release', methods=['POST'])
def release():
    data = request.json
    command_deck.send_command(command_deck.Command.RELEASE, data['controller'], data['button'])
    return "OK"

@app.route('/edit', methods=['POST'])
def edit():
    data = request.json
    command_deck.send_command(command_deck.Command.EDIT, data['controller'], data['selection'])
    return "OK"

@app.route('/enable', methods=['POST'])
def enable():
    command_deck.send_command(command_deck.Command.ENABLE, request.json['controller'])
    return "OK"

@app.route('/disable', methods=['POST'])
def disable():
    command_deck.send_command(command_deck.Command.DISABLE, request.json['controller'])
    return "OK"

@app.route('/reset', methods=['POST'])
def reset():
    command_deck.send_command(command_deck.Command.RESET)
    return "OK"

def handle_exit(signal, frame):
    print("Program interrupted, performing cleanup...")
    if args.upnp == "enable":
        upnp_mapper.remove_port_mapping()
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Starts the Arduino SmartPort web controller')
    
    parser.add_argument('-d', '--device', help='The serial device name of your Arduino', default=None)
    parser.add_argument('-i', '--ip', help='What IP the server will listen on', default='')
    parser.add_argument('-p', '--port', help='What port the server will listen on', default=5000)
    parser.add_argument('-u', '--upnp', help='Enable UPnP for auto port forwarding', default='')
    parser.add_argument('-c', '--controller', help='Override controller used by webserver', default=4)

    args = parser.parse_args()
    
    command_deck = CommandDeck(serial_device=args.device)
    controller = Controller(4, 6)

    if args.upnp == "enable":
        print("Trying to open port via UPnP")
        upnp_mapper = UPnPPortMapper(args.port, args.port, args.ip, "SmartPort Web Server")
    socketio.run(app.run(host=args.ip, port=args.port))
