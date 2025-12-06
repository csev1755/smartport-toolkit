import argparse
import serial
from flask import Flask, request, send_file, jsonify

app = Flask(__name__)

rok_action = {
  "press": 0,
  "release": 1,
  "edit": 2,
  "enable": 3,
  "disable": 4
}

@app.route('/')
def index():
    return send_file('index.html')

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

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Starts the Arduino SmartPort web controller')
    parser.add_argument('serial_device', help='The serial device name of your Arduino')
    parser.add_argument('-i', '--ip', help='What IP the server will listen on', default='0.0.0.0')
    parser.add_argument('-p', '--port', help='What port the server will listen on', default='5000')
    args = parser.parse_args()
    
    arduino = serial.Serial(args.serial_device, 115200, timeout=1)
    app.run(host=args.ip, port=args.port)
