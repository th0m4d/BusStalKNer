# -*- encoding: utf-8 -*-
from fastkml import kml
import json

class Placemark:

    startExtNr = ""
    startKurz = ""
    startLang = ""
    zielExtNr = ""
    zielKurz = ""
    zielLang = ""
    betriebsbe = ""

    def extractAttribute(self, placemark, attributeName):
        extendedData = list(placemark.etree_element()).pop(2)
        simpleDatas = list(extendedData).pop(0)
        filteredAttributes = list(filter(lambda simpleData: simpleData.attrib['name'] == attributeName,
            simpleDatas))
        filteredAttributesText = list(map(lambda attribute: attribute.text, filteredAttributes))
        filteredAttributeText = filteredAttributesText.pop()
        return filteredAttributeText

    def __init__(self, placemark):
        self.startExtNr = self.extractAttribute(placemark, 'StartExtNr')
        self.startKurz = self.extractAttribute(placemark, 'StartKurz')
        self.startLang = self.extractAttribute(placemark, 'StartLang')
        self.zielExtNr = self.extractAttribute(placemark, 'ZielExtNr')
        self.zielKurz = self.extractAttribute(placemark, 'ZielKurz')
        self.zielLang = self.extractAttribute(placemark, 'ZielLang')
        self.betriebsbe = self.extractAttribute(placemark, 'Betriebsbe')

    def __str__(self):
        return "StartExtNr: %s,\nStartKurz: %s,\nStartLang: %s" % (
            self.startExtNr,
            self.startKurz,
            self.startLang)

class KmlParser:
    linie = ""
    def __init__(self, linie):
        KmlParser.linie = linie

    def f(self, placemark):
        extendedData = list(placemark.etree_element()).pop(2)
        simpleDatas = list(extendedData).pop(0)
        for simpleData in simpleDatas:
            if simpleData.attrib['name'] == KmlParser.linie and simpleData.text == '1':
                return placemark

    def parse(self):
        with open('data/Buslinie_WGS84.kml', 'rb') as myfile:
            k = kml.KML()
            k.from_string(myfile.read())

            kmlFeatures = list(k.features())
            kmlFolders = list(kmlFeatures.pop().features())
            kmlPlacemarks = list(kmlFolders.pop().features())

            filteredKmlPlacemarks = list(filter(lambda p: KmlParser.f(self, p), kmlPlacemarks))
            placemarks = list(map(lambda p: Placemark(p), filteredKmlPlacemarks))
            return placemarks

class JsonBuslinie:
    linie = ""
    def __init__(self, linie):
        self.linie = linie

    def parse(self):
        filename = 'data/' + self.linie + '.json'
        with open(filename, 'rb') as jsonFile:
            jsonData = json.loads(jsonFile.read())
            return jsonData[self.linie]

class Fahrplan:

    def splitDepartureTime(self, departureTime):
        return departureTime.split(':')

    def createDeparture(self, placemark, departureTime):
        return {
            "time": {
                "hour": self.splitDepartureTime(departureTime)[0],
                "min": self.splitDepartureTime(departureTime)[1]
            },
            "startLang": placemark.startLang,
            "startKurz": placemark.startKurz,
            "zielLang": placemark.zielLang,
            "zielKurz": placemark.zielKurz
        }

def create(placemarks, runde, haltestelle):
    p = next(filter(lambda p: haltestelle == p.startLang, placemarks), None)
    if(p is None):
        return

    abfahrszeit = runde[haltestelle]
    return Fahrplan().createDeparture(p, abfahrszeit)

def extract_time(haltestelleUhrzeitTuple):
    try:
        # Also convert to int since update_time will be string.  When comparing
        # strings, "10" is smaller than "2".
        uhrzeit = haltestelleUhrzeitTuple[1].split(':')
        return int(uhrzeit[0]+uhrzeit[1])
    except KeyError:
        return 0


def doit(kmlLinie, linieDepatureTimesFilename):
    kmlParser = KmlParser(kmlLinie)
    placemarks = kmlParser.parse()

    jsonBuslinie = JsonBuslinie(linieDepatureTimesFilename)
    runden = jsonBuslinie.parse()

    linie = {
        "name": kmlLinie,
        "departures": []
    }

    for runde in runden:
        runde=sorted(runde.items(), key=extract_time)
        # list to dict
        runde = dict((k[0],k[1]) for k in runde)
        for haltestelle in runde.keys():
            depature = create(placemarks, runde, haltestelle)
            if(depature is None):
                print("'", haltestelle, "' nicht gefunden")
                continue

            linie["departures"].append(depature)
    return linie

result = { "linien": [] }
configs = [
    ('B1', 'linie_1'),
    ('B2', 'linie_2'),
    ('B3', 'linie_3'),
    ('B5', 'linie_5'),
    ('B6', 'linie_6'),
    #('B9', 'linie_9ab'),
    #('B11', 'linie_11'),
    ('B12', 'linie_12')
]

for config in map(lambda x: doit(x[0], x[1]), configs):
    result["linien"].append(config)


with open('data/fahrplan.json', 'w') as outfile:
    json.dump(result, outfile, indent=2, ensure_ascii=False)
