from datetime import datetime, timedelta
import time
import requests
import numpy as np
import pandas as pd
from diagnostics import cmp_cumul_rain

class token:

    def __init__(self, config):
        """
        Initialize the token object with the given configuration.
        / Initialise l'objet token avec la configuration donnée.
        """
        self.config = config
        self.access_token = config['data_access']['ACCESS_TOKEN']
        # Parse start and end dates from the configuration.
        # / Analyse les dates de début et de fin depuis la configuration.
        self.start = datetime(int(config['global']['start'][:4]),
                              int(config['global']['start'][4:6]),
                              int(config['global']['start'][6:8]),
                              0)
        self.end = datetime(int(config['global']['end'][:4]),
                            int(config['global']['end'][4:6]),
                            int(config['global']['end'][6:8]),
                            0)
        self.scale = config['global']['scale']
        if self.scale not in ['max', '5min', '30min', '1hour', '1day']:
            raise Exception ("scale must be in 'max', '5min', '30min', '1hour', '1day'.")
        else:
            if self.scale in ['5min', 'max']:
                self.scale_sec = 300
            elif self.scale in ['30min']:
                self.scale_sec = 1800
            elif self.scale in ['1hour']:
                self.scale_sec = 3600
            elif self.scale in ['1day']:
                self.scale_sec = 3600 * 24
            elif self.scale in ['1week']:
                self.scale_sec = 3600 * 24 * 7

    def get_mod_device(self):
        """
        Retrieve module and device IDs from the Netatmo API.
        / Récupère les IDs des modules et des appareils depuis l'API Netatmo.
        """
        url = "https://api.netatmo.com/api/getstationsdata"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.get(url, headers=headers)
        data = response.json()
        # Display and store device/module IDs.
        # / Affiche et stocke les IDs des appareils/modules.
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
                    raise Exception(f"Le module {module['data_type']} n'a pas d'ID / Module {module['data_type']} has no ID.")

    def get_historical_data(self, measure_type):
        """
        Fetch historical data for a specific measure type.
        / Récupère les données historiques pour un type de mesure spécifique.
        """
        start_ts = to_unix_timestamp(self.start.strftime("%Y%m%d"))
        end_ts = to_unix_timestamp(self.end.strftime("%Y%m%d"))
        # Determine the appropriate module ID based on measure type.
        # / Détermine l'ID de module approprié en fonction du type de mesure.
        if measure_type in ['Temperature', 'Humidity']:
            module_id = self.th_token
        elif measure_type == 'Rain':
            module_id = self.rain_token
            tmp = self.start - timedelta(days=1)
            start_ts = to_unix_timestamp(tmp.strftime("%Y%m%d"))
        elif measure_type in ['WindStrength', 'WindAngle', 'GustStrength']:
            module_id = self.wind_token
        elif measure_type == 'Pressure':
            module_id = self.pres_token
        headers = {"Authorization": f"Bearer {self.access_token}"}
        payload = {
            "device_id": self.pres_token,
            "module_id": module_id,
            "scale": self.scale,
            "type": [measure_type],
            "date_begin": int(start_ts),
            "date_end": int(end_ts),
            "optimize": "true",
            "real_time": "false",
        }
        response = requests.get("https://api.netatmo.com/api/getmeasure", headers=headers, params=payload)
        if response.status_code == 200:
            self.data[measure_type] = response.json()
        else:
            print(f"Erreur : {response.json()} / Error: {response.json()}")
            self.data[measure_type] = None

    def getdata(self):
        """
        Retrieve and process data for all relevant measure types.
        / Récupère et traite les données pour tous les types de mesures pertinents.
        """
        start_ts = to_unix_timestamp(self.start.strftime("%Y%m%d"))
        self.data = {}
        self.get_mod_device()
        for measure_type in ['Pressure', 'Temperature', 'Humidity', 'Rain', 'WindAngle', 'GustStrength', 'WindStrength']:
            self.get_historical_data(measure_type)
            self.reformate_data(measure_type)
            if measure_type == 'Rain':
                # Exclude previous day's rain data used for cumulative calculation.
                # / Supprime les données de pluie de la veille utilisées pour le calcul du cumul.
                mask_t = np.array(self.data['Rain_t']) >= int(start_ts)
                for duration in ['1h', '3h', '6h', '12h', '1d']:
                    name = measure_type + '_' + duration
                    self.data[name] = cmp_cumul_rain(
                        duration=duration,
                        time=self.data['Rain_t'],
                        data=self.data['Rain']
                    )
                    self.data[name] = self.data[name][mask_t]
                self.data['Rain_t'] = np.array(self.data['Rain_t'])[mask_t]
        self.cmpt_date()

    def reformate_data(self, measure_type):
        """
        Reformat the raw data into a structured format.
        / Reformate les données brutes dans un format structuré.
        """
        tmp = self.data[measure_type]['body']
        self.data[measure_type] = []
        self.data[measure_type + '_t'] = []
        for entry in tmp:
            begintime = int(entry['beg_time'])
            deltat = int(entry['step_time'])
            for j, value in enumerate(entry['value']):
                self.data[measure_type].append(np.array(value).flatten()[0])
                self.data[measure_type + '_t'].append(begintime + j * deltat)

    def cmpt_date(self):
        if self.scale in ['max', '5min']:
            dim = 24 * 12
        elif self.scale in ['30min']:
            dim = 48
        elif self.scale in ['1hour']:
            dim = 24
        elif self.scale in ['1day']:
            dim = 1
        start_ts = to_unix_timestamp(self.start.strftime("%Y%m%d")) + self.scale_sec/2
        print(type(start_ts))
        quit()
        columns=['Date', 'Temperature', 'Humidité', 'Point de rosé', 'Humidex', 'Windchill',
                 'Direction', 'Vent', 'Rafales', 'Pression', 'Pluie 5min', 'Pluie 1h',
                 'Pluie 3h', 'Pluie 6h', 'Pluie 12h', 'Pluie 24h']
        df = pd.DataFrame(columns=columns)
        for i in range(dim):
            formatted_time = start_ts.strftime("%Y-%m-%d %H:%M:%S")
            print(formatted_time)
            quit()
            #ligne = pd.DataFrame([{'Date'
        
        
        

def to_unix_timestamp(date):
    """
    Convert a date to a UNIX timestamp.
    / Convertit une date en timestamp UNIX.
    """
    return int(time.mktime(datetime.strptime(date, "%Y%m%d").timetuple()))
