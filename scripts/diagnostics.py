
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
    for i in range(len(data)):
        tmp = time[:i]
        mask = tmp > time[i] - deltat
        
        print(mask)
        
