from datetime import datetime

class SystemInfoProvider:
    def get_info(self):
        return  "LastUpdated: " + str(datetime.now().isocalendar())
