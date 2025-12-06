import argparse
import serial
from flask import Flask, request, send_file

app = Flask(__name__)

def send_command(cmd):
    arduino.write(f"{cmd}\n".encode())
    return arduino.readline().decode().strip()

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/press', methods=['POST'])
def press():
    data = request.json
    controller = data['controller']
    button = data['button']
    return send_command(f"PRESS,{controller},{button}")

@app.route('/release', methods=['POST'])
def release():
    data = request.json
    controller = data['controller']
    button = data['button']
    return send_command(f"RELEASE,{controller},{button}")

@app.route('/edit', methods=['POST'])
def edit():
    data = request.json
    controller = data['controller']
    selection = data['selection']
    return send_command(f"EDIT,{controller},{selection}")

@app.route('/enable', methods=['POST'])
def enable():
    controller = request.json['controller']
    return send_command(f"ENABLE,{controller}")

@app.route('/disable', methods=['POST'])
def disable():
    controller = request.json['controller']
    return send_command(f"DISABLE,{controller}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Starts the Arduino SmartPort web controller')
    parser.add_argument('serial_device', help='The serial device name of your Arduino')
    parser.add_argument('-i', '--ip', help='What IP the server will listen on', default='0.0.0.0')
    parser.add_argument('-p', '--port', help='What port the server will listen on', default='5000')
    args = parser.parse_args()
    
    arduino = serial.Serial(args.serial_device, 115200, timeout=1)
    app.run(host=args.ip, port=args.port)
