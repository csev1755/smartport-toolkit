## web.py
A Flask webserver that handles requests to interact with Rokenbok

## rokenbok_control.py
A module called by the Flask webserver that defines Command Deck functions and logic

## rokenbok_device.py
A module called by the `rokenbok_control` module to control a Rokenbok device like a SmartPort adapter

## upnp.py
A module that can be used by the webserver to open its port on a router via UPnP
