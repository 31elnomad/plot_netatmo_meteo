from datetime import datetime, timedelta
import time
import requests
import numpy as np
import pandas as pd
from diagnostics import cmp_cumul_rain, calculer_point_de_rosee, calculer_humidex

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
                self.data['Rain'] = np.array(self.data['Rain'])[mask_t]
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
        columns=['Date', 'Température', 'Humidité', 'Point de rosée', 'Humidex', 'Windchill',
                 'Direction', 'Vent', 'Rafales', 'Pression', 'Pluie 5min', 'Pluie 1h',
                 'Pluie 3h', 'Pluie 6h', 'Pluie 12h', 'Pluie 24h']
        df = pd.DataFrame(columns=columns)
        for i in range(dim):
            dt_object = datetime.fromtimestamp(start_ts)
            formatted_time = dt_object.strftime("%Y-%m-%d %H:%M:%S")
            tmp = {'Date':formatted_time}
            list_measure = ['Pressure', 'Temperature', 'Humidity', 'Rain', 'WindAngle',
                            'GustStrength', 'WindStrength']
            for measure_type in list_measure:
                time_measure = measure_type + '_t'
                mask1 = np.array(self.data[time_measure]) < start_ts + self.scale_sec/2 
                mask2 = np.array(self.data[time_measure]) >= start_ts - self.scale_sec/2
                mask = mask1 * mask2
                data = np.array(self.data[measure_type])[mask]
                if measure_type in ['Pressure']:
                    if len(data) > 0:
                        tmp['Pression'] = np.mean(data)
                    else:
                        tmp['Pression'] = np.nan
                elif measure_type in ['Temperature']:
                    if len(data) > 0:
                        tmp['Température'] = np.mean(data)
                    else:
                        tmp['Température'] = np.nan
                elif measure_type in ['Humidity']:
                    if len(data) > 0:
                        tmp['Humidité'] = int(np.mean(data))
                    else:
                        tmp['Humidité'] = np.nan
                elif measure_type in ['Rain']:
                    if len(data) > 0:
                        tmp['Pluie 5min'] = np.mean(data)
                        tmp['Pluie 1h'] = np.round(np.mean(np.array(self.data[measure_type+'_1h'])[mask]), 1)
                        tmp['Pluie 3h'] = np.round(np.mean(np.array(self.data[measure_type+'_3h'])[mask]), 1)
                        tmp['Pluie 6h'] = np.round(np.mean(np.array(self.data[measure_type+'_6h'])[mask]), 1)
                        tmp['Pluie 12h'] = np.round(np.mean(np.array(self.data[measure_type+'_12h'])[mask]), 1)
                        tmp['Pluie 24h'] = np.round(np.mean(np.array(self.data[measure_type+'_1d'])[mask]), 1)
                    else:
                        tmp['Pluie 5min'] = np.nan
                        tmp['Pluie 1h'] = np.nan
                        tmp['Pluie 3h'] = np.nan
                        tmp['Pluie 6h'] = np.nan
                        tmp['Pluie 12h'] = np.nan
                        tmp['Pluie 24h'] = np.nan
                elif measure_type in ['WindAngle']:
                    if len(data) > 0:
                        tmp['Direction'] = np.mean(data)
                    else:
                        tmp['Direction'] = np.nan
                elif measure_type in ['GustStrength']:
                    if len(data) > 0:
                        tmp['Rafales'] = np.mean(data)
                    else:
                        tmp['Rafales'] : np.nan
                elif measure_type in ['WindStrength']:
                    if len(data) > 0:
                        tmp['Vent'] = np.mean(data)
                    else:
                        tmp['Vent'] = np.nan
            if tmp['Humidité'] != np.nan and tmp['Température'] != np.nan:
                td = calculer_point_de_rosee(tmp['Température'], tmp['Humidité'])
                tmp['Point de rosée'] = np.round(td, 1)
            if tmp['Point de rosée'] != np.nan:
                humidex = calculer_humidex(tmp['Température'], tmp['Point de rosée'])
                tmp['Humidex'] = np.round(humidex, 1)
            start_ts += self.scale_sec
            new_ligne = pd.DataFrame([tmp])
            df = pd.concat([df, new_ligne], ignore_index=True)
        print(df)


def to_unix_timestamp(date):
    """
    Convert a date to a UNIX timestamp.
    / Convertit une date en timestamp UNIX.
    """
    return int(time.mktime(datetime.strptime(date, "%Y%m%d").timetuple()))
