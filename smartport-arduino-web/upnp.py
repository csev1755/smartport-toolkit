import upnpy

class UPnPPortMapper:
    def __init__(self, external_port=None, internal_port=None, internal_client=None, description=None):
        self.upnp = upnpy.UPnP()
        self.device = None
        self.service = None
        self.mappings = []

        self.external_port = external_port
        self.internal_port = internal_port
        self.internal_client = internal_client
        self.description = description

        try:
            devices = self.discover_devices()
            for device in devices:
                if self.select_device(device):
                    services = self.get_services()
                    if services:
                        for service in services:
                            self.service = service
                            self.add_port_mapping(self.external_port, self.internal_port, self.internal_client, self.description)
        except:
            print("Failed to configure UPnP")

    def discover_devices(self):
        devices = self.upnp.discover()
        if not devices:
            print("No UPnP devices found on the network")
            return []
        print("Discovered:")
        for device in devices:
            print(f" - {device}")
        return devices

    def select_device(self, device):
        self.device = device
        if not self.device:
            print("No device, cannot proceed with port mapping")
            return False
        print(f"Using {self.device}")
        return True

    def get_services(self):
        services = self.device.get_services()
        if not services:
            print(f"No services found for device {self.device}")
            return []
        return services

    def add_port_mapping(self, external_port, internal_port, internal_client, description):
        try:
            if 'AddPortMapping' in [action.name for action in self.service.get_actions()]:
                response = self.service.AddPortMapping(
                    NewRemoteHost='',
                    NewExternalPort=external_port,
                    NewProtocol='TCP',
                    NewInternalPort=internal_port,
                    NewInternalClient=internal_client,
                    NewEnabled=1,
                    NewPortMappingDescription=description,
                    NewLeaseDuration=86400
                )
                self.mappings.append({
                    'external_port': external_port,
                    'internal_port': internal_port,
                    'internal_client': internal_client,
                    'description': description,
                    'service': self.service
                })
                print(f"Port mapping '{self.description}' added to {self.service}")
        except upnpy.exceptions.ServiceNotFoundError as e:
            print(f"ServiceNotFoundError: {e}")
        except Exception as e:
            print(f"Error with service {self.service}: {e}")
            print(f"Response: {response}")

    def remove_port_mapping(self):
        if not self.description:
            print("No description provided for the port mapping to remove")
            return
        for mapping in self.mappings:
            if mapping['description'] == self.description:
                try:
                    print(f"Removing port mapping '{self.description}'")
                    response = mapping['service'].DeletePortMapping(
                        NewRemoteHost='',
                        NewExternalPort=mapping['external_port'],
                        NewProtocol='TCP'
                    )
                    self.mappings.remove(mapping)
                    print(f"Port mapping removed successfully")
                except Exception as e:
                    print(f"Error removing port mapping '{self.description}': {e}")
                    print(f"Response: {response}")
                return
        print(f"No active port mapping found with description '{self.description}'")
