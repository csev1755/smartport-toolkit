# smartport-arduino
An Arduino sketch that listens to commands from its USB serial interface to perform commands via the SmartPort protocol

## SmartPort pinout

![SmartPort diagram](./mini-din-6.jpg)

| SmartPort Pin | Function | Arduino Uno | Arduino Nano
|---|---|---|---|
| 1 | Serial Clock | 13 | 13 |
| 2 | MISO | 12 | 12 |
| 3 | MOSI | 11 | 11 |
| 4 | Frame End | - | - |
| 5 | Slave Ready | 9 | 9 |
| 6 | Ground | GND | GND |

## Other projects

### https://github.com/stepstools/Rokenbok-Smart-Port-WiFi
Custom ESP32 controller with web interface

### https://github.com/jordan-woyak/rokenbok-smart-port
Arduino controller

### https://github.com/rgill02/rokenbok
Arduino controller with Python client, server, and hub
