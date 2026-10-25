# SPDX-License-Identifier: MIT
from sameloop_plant import finite
from .contract import Freshness, obj, settings


class Controller:
    def __init__(self):
        self.mode, self.setpoint = 'OFF', 25.0
        self.accepted = {'id': 'startup', 'mode': 'OFF', 'setpoint': 25.0}
        self.error, self.last_request_id = '', 'startup'
        self.last_raw = None
        self.frame = None
        self.clock = Freshness()
        self.confirmed = False
        self.overheat = False
        self.bad_frame = False

    def request(self, raw):
        if raw is None or raw == self.last_raw:
            return False
        self.last_raw = raw
        self.last_request_id = ''
        try:
            request = settings(raw)
            self.mode, self.setpoint = request['mode'], request['setpoint']
            self.accepted = request
            self.last_request_id = request['id']
            self.error = ''
            return True
        except (ValueError, TypeError) as e:
            self.error = str(e)
            try:
                self.last_request_id = str(obj(raw).get('id', ''))[:80]
            except (ValueError, TypeError):
                pass
            return False

    def observe(self, raw, now):
        try:
            f = obj(raw)
            if type(f.get('valid')) is not bool:
                raise ValueError('valid bool requis')
            for key,lo,hi in [('temperature',-40,150),('applied',0,100),('rpm',0,10000)]:
                finite(f.get(key),lo,hi,key)
            previous = self.clock.key
            if self.clock.accept(f, now):
                self.confirmed = previous is not None and previous[0] == f['generation']
                self.frame, self.bad_frame = f, False
        except (ValueError, TypeError):
            self.bad_frame = True

    def state(self, now):
        available = bool(self.frame and self.frame['valid'] and not self.bad_frame
                         and self.confirmed and self.clock.fresh(now))
        if available:
            self.overheat = self.frame['temperature'] > 50.0
        demand = min(100.0, max(0.0, 20*(self.frame['temperature']-self.setpoint))) \
            if available and self.mode == 'AUTO' else 0.0
        return {'mode': self.mode, 'setpoint': self.setpoint, 'available': available,
                'overheat': self.overheat, 'alarm_quality': 'valid' if available else 'unavailable',
                'demand': demand, 'temperature': self.frame['temperature'] if self.frame else None,
                'applied': self.frame['applied'] if self.frame else None,
                'rpm': self.frame['rpm'] if self.frame else None,
                'error': self.error, 'request_id': self.last_request_id,
                'sensor_generation': self.clock.key[0] if self.clock.key else None,
                'sensor_sequence': self.clock.key[1] if self.clock.key else None}
