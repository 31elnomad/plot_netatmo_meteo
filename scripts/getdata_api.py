from datetime import datetime, timedelta
import time
import requests
import numpy as np
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
        if self.scale not in ['max', '5min', '30min', '1hour', '1day', '1week']:
            raise Exception ("scale must be in 'max', '5min', '30min', '1hour', '1day', '1week'.")
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
        """
        Validate and print the date range of the data.
        / Valide et affiche la plage de dates des données.
        """
        start_ts = to_unix_timestamp(self.start.strftime("%Y%m%d"))
        print(start_ts, self.data['Pressure_t'][0])
        max_dim = 0
        for measure_type in ['Pressure_t', 'Temperature_t', 'Rain_t', 'WindAngle_t']:
            if len(self.data[measure_type]) > max_dim:
                max_dim = len(self.data[measure_type])
        n = [0, 0, 0, 0]
        self.data['Time'] = np.empty(max_dim).astype(str)
        for i in range(max_dim):
            time_tmp = []
            for measure_type in ['Pressure', 'Temperature', 'Rain', 'WindAngle']:
                name = measure_type + '_t'
                if measure_type in ['Pressure']:
                    j = 0
                elif measure_type in  ['Temperature']:
                    j = 1
                elif measure_type in ['Rain']:
                    j = 2
                elif measure_type in ['WindAngle']:
                    j = 3
                if self.data[name][n[j]] - start_ts < self.scale_sec:
                    time_tmp.append(self.data[name][n[j]])
                    n[j] += 1
            epoch_timestamp = int(np.mean(np.array(time_tmp)))
            dt_object = datetime.fromtimestamp(epoch_timestamp)  
            formatted_time = dt_object.strftime("%Y-%m-%d %H:%M:%S")
            self.data['Time'][i] = formatted_time
            print(self.data['Time'][i])
            start_ts = epoch_timestamp

def to_unix_timestamp(date):
    """
    Convert a date to a UNIX timestamp.
    / Convertit une date en timestamp UNIX.
    """
    return int(time.mktime(datetime.strptime(date, "%Y%m%d").timetuple()))
