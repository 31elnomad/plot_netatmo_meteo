import numpy as np

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
