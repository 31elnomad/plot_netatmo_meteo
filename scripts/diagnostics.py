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
        if i == 0:
            cumul[i] = np.round(data[i],1)
        else:
            tmp = np.array(time[:i])
            mask = tmp > time[i] - deltat
        
        print(cumul[0])
        quit()
        
