import serial
from flask import Flask, request, send_file

app = Flask(__name__)
arduino = serial.Serial('/dev/ttyACM0', 115200, timeout=1)

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
    app.run(host='0.0.0.0', port=5000)
