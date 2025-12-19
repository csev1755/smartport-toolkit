import serial
import time

key7 = 0x06
controller_bit = 0b00010000
enabled_controllers = 0b11101111 # does this need to be set dynamically?

controller_status_cmd = 0x01
select_cmd = 0x02
button = 0x03

ser = serial.Serial('COM3', 115200)
time.sleep(2) # breaks without this

ser.write(bytes([controller_status_cmd, enabled_controllers]))

ser.write(bytes([select_cmd, 0x00, key7]))

while True:
    ser.write(
        bytes([button, 0x00, 0x00, 0x00, 0x00, controller_bit, 0x00, 0x00, 0x00, 0x00]))

    time.sleep(1)

    ser.write(
        bytes([button, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]))

    time.sleep(1)
