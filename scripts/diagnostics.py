import numpy as np
import math

def cmp_cumul_rain(duration, time, data):
    """
    Calculate cumulative rainfall over a specified duration.
    / Calcule le cumul de pluie sur une durée spécifiée.
    
    Parameters:
    - duration (str): The duration for the cumulative calculation (e.g., '1h', '3h', '6h').
                      / La durée pour le calcul du cumul (par ex. : '1h', '3h', '6h').
    - time (list or array): Array of timestamps corresponding to the data.
                            / Tableau des timestamps correspondant aux données.
    - data (list or array): Array of rainfall values.
                            / Tableau des valeurs de pluie.
    
    Returns:
    - cumul (array): Array of cumulative rainfall values for the given duration.
                     / Tableau des valeurs de pluie cumulées pour la durée spécifiée.
    """
    # Define the time delta based on the duration. / Définir le delta temporel en fonction de la durée.
    if duration in ['1h']:
        deltat = 3600  # 1 hour in seconds / 1 heure en secondes
    elif duration in ['3h']:
        deltat = 3 * 3600  # 3 hours in seconds / 3 heures en secondes
    elif duration in ['6h']:
        deltat = 6 * 3600  # 6 hours in seconds / 6 heures en secondes
    elif duration in ['12h']:
        deltat = 12 * 3600  # 12 hours in seconds / 12 heures en secondes
    elif duration in ['1d', '1j', '24h']:
        deltat = 24 * 3600  # 1 day in seconds / 1 jour en secondes
    else:
        raise Exception("La durée pour calculer le cumul de pluie n'est pas connue / Unknown duration for cumulative rainfall calculation.")

    # Initialize an empty array for the cumulative rainfall values.
    # / Initialiser un tableau vide pour les valeurs de pluie cumulées.
    cumul = np.empty(len(data))

    # Iterate through the data to compute cumulative rainfall for each point.
    # / Itérer sur les données pour calculer le cumul de pluie pour chaque point.
    for i in range(len(data)):
        # Get the time window based on the duration. / Obtenir la fenêtre temporelle en fonction de la durée.
        tmp = np.array(time[:i+1])
        mask = tmp > time[i] - deltat  # Select data within the time window. / Sélectionner les données dans la fenêtre temporelle.
        data_tmp = np.array(data[:i+1])[mask]

        # Compute the cumulative sum of rainfall, rounded to 1 decimal.
        # / Calculer la somme cumulée des pluies, arrondie à 1 décimale.
        cumul[i] = np.sum(np.round(data_tmp, 1))
    return cumul



def calculer_point_de_rosee(temperature, humidite_relative):
    """
    Calcule le point de rosée à partir de la température et de l'humidité relative.

    Arguments :
    - temperature : Température de l'air en °C
    - humidite_relative : Humidité relative en pourcentage (ex. 50 pour 50%)

    Retourne :
    - Point de rosée en °C
    """
    # Constantes pour la formule de Magnus-Tetens
    a = 17.27
    b = 237.7

    # Convertir l'humidité relative en fraction
    RH = humidite_relative / 100.0

    # Calculer alpha
    alpha = (a * temperature) / (b + temperature) + math.log(RH)

    # Calculer le point de rosée
    Td = (b * alpha) / (a - alpha)

    return Td

def calculer_humidex(temperature, point_de_rosee):
    """
    Calcule l'indice humidex à partir de la température et de l'humidité relative.

    Arguments :
    - temperature : Température de l'air en °C
    - humidite_relative : Humidité relative en pourcentage (ex. 50 pour 50%)

    Retourne :
    - Humidex
    """
    if temperature >= 20:
        # Calcul de la tension de vapeur
        e = 6.112 * math.exp((17.27 * point_de_rosee) / (237.7 + point_de_rosee))
    
        # Calcul de l'humidex
        humidex = temperature + 0.5555 * (e - 10)
    else:
        humidex = temperature
    return humidex

