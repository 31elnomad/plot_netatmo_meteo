from datetime import datetime
import requests

class token:

    def __init__(self, config):
        self.config = config
        self.access_token = config['data_access']['ACCESS_TOKEN']
        self.devide_id = config['data_access']['DEVICE_ID']
        self.module_id = config['data_access']['MODULE_ID']
        self.api_url = config['data_access']['API_URL']
        self.start = datetime(int(config['date']['start'][:4]),
                              int(config['date']['start'][4:6]),
                              int(config['date']['start'][6:8]),
                              0)
        self.end = datetime(int(config['date']['end'][:4]),
                            int(config['date']['end'][4:6]),
                            int(config['date']['end'][6:8]),
                            0)

    def get_mod_device(self):
        url = "https://api.netatmo.com/api/getstationsdata"
        headers = {
                  "Authorization": "Bearer YOUR_ACCESS_TOKEN"
        }
        response = requests.get(url, headers=headers)
        data = response.json()
        print(data)

    def getdata(self):
        self.get_mod_device()
