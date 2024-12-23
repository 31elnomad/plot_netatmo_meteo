import numpy as np

def cmp_cumul_rain(duration, time, data):
    if duration in ['1h']:
        deltat = 3600
    elif duration in ['3h']:
        deltat = 3 * 3600
    elif duration in ['6h']:
        deltat = 6 * 3600
    elif duration in ['12h']:
        deltat = 12 * 3600
    elif duration in ['1d', '1j', '24h']:
        delta = 24 * 3600
    else:
        raise Exception ("La durée pour calculer le cumul de pluie n'est pas connue") 
    cumul = np.empty(len(data))
    for i in range(len(data)):
        tmp = np.array(time[:i+1])
        mask = tmp > time[i] - deltat
        data_tmp = np.array(data[:i+1])[mask]
        cumul[i] = np.sum(np.round(data_tmp,1))
    print(cumul, np.max(cumul))
        

        
