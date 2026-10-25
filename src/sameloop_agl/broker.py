# SPDX-License-Identifier: MIT
"""Explicit VAL v1 calls: no transparent v2 fallback, deadlines on every RPC."""
import grpc
from kuksa.val.v1 import types_pb2 as t, val_pb2 as v, val_pb2_grpc as g
from .contract import SIGNALS, PREFIX


class Broker:
    def __init__(self, host='127.0.0.1', port=55555, timeout=0.4):
        if host not in ('127.0.0.1', 'localhost', '::1'):
            raise ValueError('Profil 0.1.0 en clair limité au loopback')
        self.timeout = timeout
        self.channel = grpc.insecure_channel(f'[{host}]:{port}' if ':' in host else f'{host}:{port}')
        self.stub = g.VALStub(self.channel)

    def close(self):
        self.channel.close()

    @staticmethod
    def check(reply):
        if reply.HasField('error') and reply.error.code:
            raise RuntimeError(str(reply.error))
        if reply.errors:
            raise RuntimeError('; '.join(str(e) for e in reply.errors))

    def get(self, names, target=False):
        field = t.FIELD_ACTUATOR_TARGET if target else t.FIELD_VALUE
        reply = self.stub.Get(v.GetRequest(entries=[v.EntryRequest(
            path=PREFIX+n, fields=[field]) for n in names]), timeout=self.timeout)
        self.check(reply)
        result = {n: None for n in names}
        for entry in reply.entries:
            dp = entry.actuator_target if target else entry.value
            value_field = dp.WhichOneof('value')
            result[entry.path.removeprefix(PREFIX)] = getattr(dp, value_field) if value_field else None
        return result

    def set(self, values, target=False):
        field = t.FIELD_ACTUATOR_TARGET if target else t.FIELD_VALUE
        updates = []
        for name, value in values.items():
            kind = SIGNALS[name][0]
            member = 'bool' if kind == 'boolean' else kind
            dp = t.Datapoint(**{member: value})
            dp.timestamp.GetCurrentTime()
            entry = t.DataEntry(path=PREFIX+name)
            (entry.actuator_target if target else entry.value).CopyFrom(dp)
            updates.append(v.EntryUpdate(entry=entry, fields=[field]))
        reply = self.stub.Set(v.SetRequest(updates=updates), timeout=self.timeout)
        self.check(reply)
