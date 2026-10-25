# SPDX-License-Identifier: MIT
import json
from sameloop_plant import finite
PREFIX = 'Vehicle.SameLoop.'
SIGNALS = {
    'Settings': ('string', 'actuator', 'Requête JSON atomique mode/consigne ; current = réglage accepté'),
    'Command': ('string', 'actuator', 'Commande interne JSON avec génération, séquence et duty'),
    'Faults': ('string', 'actuator', 'Injection de panne réservée au laboratoire'),
    'Frame': ('string', 'sensor', 'Échantillon cohérent JSON du fournisseur'),
    'State': ('string', 'sensor', 'État cohérent JSON du contrôleur'),
    'Temperature': ('double', 'sensor', 'Température simulée en degrés Celsius'),
    'SensorValid': ('boolean', 'sensor', 'Validité du capteur'),
    'FanApplied': ('double', 'sensor', 'Ventilation appliquée en pourcentage'),
    'FanRpm': ('double', 'sensor', 'Vitesse simulée en tours par minute'),
    'FanDemand': ('double', 'sensor', 'Demande du contrôleur en pourcentage'),
    'Mode': ('string', 'sensor', 'Mode accepté OFF ou AUTO'),
    'Setpoint': ('double', 'sensor', 'Consigne acceptée en degrés Celsius'),
    'Available': ('boolean', 'sensor', 'Échantillon valide et récent'),
    'Overheat': ('boolean', 'sensor', 'Dernière alarme thermique connue ; lire Available'),
    'Error': ('string', 'sensor', 'Dernière erreur de réglage'),
}


def dumps(obj):
    return json.dumps(obj, separators=(',', ':'), allow_nan=False)


def obj(raw):
    if not isinstance(raw, str) or len(raw) > 8192:
        raise ValueError('Message absent ou trop long')
    result = json.loads(raw)
    if not isinstance(result, dict):
        raise ValueError('Objet JSON requis')
    return result


def settings(raw):
    d = obj(raw)
    if set(d) != {'id', 'mode', 'setpoint'}:
        raise ValueError('Champs requis : id, mode, setpoint')
    if not isinstance(d['id'], str) or not 1 <= len(d['id']) <= 80:
        raise ValueError('id invalide')
    if d['mode'] not in ('OFF', 'AUTO'):
        raise ValueError('mode attendu OFF ou AUTO')
    d['setpoint'] = finite(d['setpoint'], 15, 40, 'setpoint')
    return d


def envelope(d):
    if not isinstance(d.get('generation'), str) or not 1 <= len(d['generation']) <= 80:
        raise ValueError('generation invalide')
    if type(d.get('sequence')) is not int or not 0 <= d['sequence'] < 2**53:
        raise ValueError('sequence invalide')
    return d['generation'], d['sequence']


class Freshness:
    """Ignore cached repeats; time measured locally, never cross-host monotonic."""
    def __init__(self):
        self.key = None
        self.received = None
        self.retired = set()

    def accept(self, d, now):
        key = envelope(d)
        if self.key is not None:
            if key[0] in self.retired:
                return False
            if key[0] == self.key[0] and key[1] <= self.key[1]:
                return False
            if key[0] != self.key[0]:
                self.retired.add(self.key[0])
        self.key, self.received = key, now
        return True

    def fresh(self, now):
        return self.received is not None and 0 <= now-self.received < 1.0
