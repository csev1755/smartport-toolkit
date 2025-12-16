# rokenbok-webserver
A modular Python Flask application to control Rokenbok over the internet
## [web.py](/web.py)
A Flask webserver that handles requests to interact with Rokenbok

## [rokenbok_control.py](/rokenbok_control.py)
A module called by the Flask webserver that defines Command Deck functions and logic

## [rokenbok_device.py](/rokenbok_device.py)
A module called by rokenbok_control.py module to control a Rokenbok device like a SmartPort adapter ([smartport-arduino](/smartport-arduino))

## [upnp.py](/upnp.py)
A module that can be used by the webserver to open its port on a router via UPnP
