from datetime import datetime
import time
import requests

class token:

    def __init__(self, config):
        self.config = config
        self.access_token = config['data_access']['ACCESS_TOKEN']
        self.start = datetime(int(config['global']['start'][:4]),
                              int(config['global']['start'][4:6]),
                              int(config['global']['start'][6:8]),
                              0)
        self.end = datetime(int(config['global']['end'][:4]),
                            int(config['global']['end'][4:6]),
                            int(config['global']['end'][6:8]),
                            0)
        # Convertir les dates en timestamps UNIX
        self.start_ts = to_unix_timestamp(self.start.strftime("%Y%m%d"))
        self.end_ts = to_unix_timestamp(self.end.strftime("%Y%m%d"))
        self.scale = config['global']['scale']

    def get_mod_device(self):
        url = "https://api.netatmo.com/api/getstationsdata"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.get(url, headers=headers)
        data = response.json()
        # Afficher les device_id et module_id
        for station in data['body']['devices']:
            self.pres_token = station['_id']
            for module in station['modules']:
                if 'Temperature' in module['data_type']:
                    self.th_token = module['_id']
                elif 'Rain' in module['data_type']:
                    self.rain_token = module['_id']
                elif 'Wind' in module['data_type']:
                    self.wind_token = module['_id']
                else:
                    raise Exception ("Le module {} n'a pas de id".format(module['data_type']))

    def get_historical_data(self, measure_type):
        if  measure_type == 'th':
            a = ['Temperature', 'Humidity']
            module_id = self.th_token
        elif measure_type == 'rain':
            a = ['Rain']
            module_id = self.rain_token
        elif measure_type == 'wind':
            a = ['WindStrength']
            module_id = self.wind_token
        elif measure_type == 'pressure':
            a = ['Pressure']
            module_id = self.pres_token
        headers = {"Authorization": f"Bearer {self.access_token}"}
        payload = {
            "device_id": self.pres_token,
            "module_id": module_id,
            "scale": self.scale,
            "type": a,
            "date_begin": int(self.start_ts),
            "date_end": int(self.end_ts),
            "optimize": "true",
            "real_time": "false",
        }
        response = requests.get("https://api.netatmo.com/api/getmeasure", headers=headers, params=payload)
        if response.status_code == 200:
            self.data[measure_type] = response.json()
        else:
            print("Erreur :", response.json())
            self.data[measure_type] = None

    def getdata(self):
        self.data = {}
        self.get_mod_device()
        for measure_type in ['pressure', 'wind', 'rain', 'th']:
            self.get_historical_data(measure_type)
            if measure_type == 'wind':
                print(measure_type, self.data[measure_type])
            

# Convertir une date en timestamp UNIX
def to_unix_timestamp(date):
    return int(time.mktime(datetime.strptime(date, "%Y%m%d").timetuple()))
