#!/home/esther/.local/venvs/python-epics/bin/python3
#
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

"idEstacao": 1210762,
"localEstacao": "Lisboa, Tapada da Ajuda",

"idEstacao": 7240919,
"localEstacao": "Lisboa, Amoreiras (Lic. Franc\u00eas)",

"idEstacao": 1200535,
"localEstacao": "Lisboa (Geof\u00edsico)",

"idEstacao": 1200579,
"localEstacao": "Lisboa (G.Coutinho)",

"""
import geojson
import urllib.request
from epics import caput  # , cainfo
# import pprint as pp

IPMA_URL = ('https://api.ipma.pt/open-data/observation/'
            'meteorology/stations/obs-surface.geojson')
# file = 'obs-surface.geojson'
# with open(file, 'r') as file:
#    gj2 = geojson.load(file)


def readMeteo():
    with urllib.request.urlopen(IPMA_URL, timeout=4) as url:
        gj = geojson.load(url)
        # data = json.load(url)
    # Now, let's print the GeoJSON data to understand its structure
    # pp.pprint(dict(gj))
    features = gj['features']
    printLoc = True
    ambient = []
    for feat in features:
        prop = feat['properties']
        if feat['properties']['idEstacao'] == 1200579:
            if printLoc:
                printLoc = False
                print(feat['properties']['localEstacao'])

            time = prop['time']
            temp = prop['temperatura']
            press = prop['pressao']
            hum = prop['humidade']
            print("time %s, temperatura %.2f ºC" % (time, press), end='')
            # print(", temperatura %.2f ºC" % temp, end='')
            # print(", pressao %.2f mBar" % prop['pressao'], end='')
            # print(", humidade %.1f%%" % prop['humidade'])
            caput('Esther:gas:Pressure', press)
            caput('Esther:gas:Humidity', hum)
            print(", caput Esther:gas:Pressure  %.2f mBar " % prop['pressao'],
                  end='')
            print(", caput Esther:gas:Humidity  %.1f%% " % prop['humidade'])

    if not printLoc:
        ambient.append(time)
        ambient.append(temp)
        ambient.append(press)
        ambient.append(hum)
        return ambient
    else:
        pass


if __name__ == '__main__':
    print(readMeteo())
