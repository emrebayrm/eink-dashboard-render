import socket
from datetime import datetime

class SystemInfoProvider:
    def get_info(self):
        # TODO: integrate with network status retrieval
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname) + ", LastUpdated: " + str(datetime.now())
