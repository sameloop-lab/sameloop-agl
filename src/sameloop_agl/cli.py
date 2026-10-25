# SPDX-License-Identifier: MIT
import argparse
import json
import signal
import sys
import threading
import time
import uuid
from .broker import Broker
from .contract import dumps, obj, settings
from .services import controller, provider
from .locking import single_instance


def main():
    p = argparse.ArgumentParser(description='SameLoop — KUKSA VAL v1 sur PC')
    p.add_argument('--host',default='127.0.0.1')
    p.add_argument('--port',type=int,default=55555)
    sub = p.add_subparsers(dest='action', required=True)
    sub.add_parser('controller')
    s=sub.add_parser('provider'); s.add_argument('--allow-faults',action='store_true')
    sub.add_parser('state')
    s=sub.add_parser('watch'); s.add_argument('--count',type=int,default=0,help='0 = continu')
    s=sub.add_parser('set');s.add_argument('--mode',choices=['OFF','AUTO'],required=True);s.add_argument('--setpoint',type=float,required=True)
    s=sub.add_parser('fault');s.add_argument('--invalid',action='store_true');s.add_argument('--hot',action='store_true')
    a=p.parse_args()
    stop=threading.Event()
    for sig in [signal.SIGINT,signal.SIGTERM]:signal.signal(sig,lambda *_:stop.set())
    b=None
    try:
        b=Broker(a.host,a.port)
        if a.action=='provider':
            with single_instance('provider',a.port): provider(b,stop,a.allow_faults)
        elif a.action=='controller':
            with single_instance('controller',a.port): controller(b,stop)
        elif a.action=='state':
            value=b.get(['State'])['State']
            print(json.dumps(obj(value),indent=2))
        elif a.action=='watch':
            # VAL v1 server-streaming, unlike the services' explicit 10 Hz polling.
            from kuksa.val.v1 import val_pb2 as v,types_pb2 as t
            request=v.SubscribeRequest(entries=[v.SubscribeEntry(path='Vehicle.SameLoop.State',fields=[t.FIELD_VALUE])])
            stream=b.stub.Subscribe(request,timeout=None)
            # Cancel blocking receive on Ctrl+C, including when no values change.
            def cancel():stop.wait();stream.cancel()
            threading.Thread(target=cancel,daemon=True).start()
            n=0
            try:
                for reply in stream:
                    for update in reply.updates:
                        print(update.entry.value.string,flush=True);n+=1
                    if a.count>0 and n>=a.count:break
            finally:stream.cancel()
        elif a.action=='set':
            request={'id':str(uuid.uuid4()),'mode':a.mode,'setpoint':a.setpoint}
            raw=dumps(request);settings(raw)
            b.set({'Settings':raw},target=True)
            end=time.monotonic()+3
            while time.monotonic()<end and not stop.is_set():
                raw_state=b.get(['State'])['State']
                state=obj(raw_state) if raw_state else {}
                if state.get('request_id')==request['id']:
                    if state.get('error'):raise ValueError(state['error'])
                    print(json.dumps(state,indent=2));break
                stop.wait(.1)
            else:raise RuntimeError('Pas d’acquittement du contrôleur : résultat inconnu')
        elif a.action=='fault':
            b.set({'Faults':dumps({'invalid':a.invalid,'hot':a.hot})},target=True)
            print('Demande transmise ; effet seulement si provider lancé avec --allow-faults.')
    except Exception as e:
        if not stop.is_set():
            print(f'Erreur: {e}',file=sys.stderr);return 1
    finally:
        stop.set()
        if b:b.close()
    return 0
