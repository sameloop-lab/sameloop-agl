#!/usr/bin/env python3
"""Real broker + separate provider/controller; no mocked transport."""
import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from sameloop_agl.broker import Broker
from sameloop_agl.contract import dumps,obj

p=argparse.ArgumentParser();p.add_argument('--broker',required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[1]
with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
processes=[];logs=[]
def launch(cmd):
    log=tempfile.TemporaryFile(mode='w+t');logs.append(log)
    proc=subprocess.Popen(cmd,stdout=log,stderr=log);processes.append(proc);return proc

def service(name,*args):
    # Invoke installed console entry via Python to avoid PATH differences.
    return launch([sys.executable,'-c','from sameloop_agl.cli import main; raise SystemExit(main())','--port',str(port),name,*args])

def until(fn,timeout=5):
    end=time.monotonic()+timeout;last=None
    while time.monotonic()<end:
        try:
            result=fn()
            if result:return result
        except Exception as e:last=e
        time.sleep(.05)
    raise AssertionError(f'Timeout: {last}')

def state():return obj(b.get(['State'])['State'])
def frame():return obj(b.get(['Frame'])['Frame'])
def stop(proc,kill=False):
    if proc.poll() is None:
        proc.kill() if kill else proc.terminate()
        proc.wait(timeout=5)
def passed(name):print('PASS '+name,flush=True)

b=Broker(port=port)
try:
    broker=launch([a.broker,'--address','127.0.0.1','--port',str(port),'--insecure','--disable-authorization','--vss',str(root/'config/vss.json')])
    until(lambda: b.get(['Temperature']))
    prov=service('provider','--allow-faults');ctrl=service('controller')
    until(lambda:state()['available'])
    assert state()['mode']=='OFF' and state()['setpoint']==25 and state()['demand']==0
    passed('startup_OFF_25_and_live_frame')
    b.set({'Settings':dumps(dict(id='auto',mode='AUTO',setpoint=25))},target=True)
    until(lambda:state()['mode']=='AUTO' and state()['demand']>0 and frame()['applied']>2)
    passed('AUTO_cross_process_actuation')
    duplicate=service('controller');assert duplicate.wait(timeout=5)!=0
    assert state()['mode']=='AUTO'
    passed('duplicate_controller_refused_without_reset')
    watcher=service('watch','--count','2');assert watcher.wait(timeout=5)==0
    passed('real_gRPC_subscription')
    b.set({'Settings':dumps(dict(id='bad',mode='OFF',setpoint=41))},target=True)
    until(lambda:state()['request_id']=='bad' and state()['error'])
    assert state()['mode']=='AUTO' and state()['setpoint']==25
    passed('atomic_rejection_of_invalid_setting')
    b.set({'Faults':dumps(dict(invalid=True,hot=False))},target=True)
    until(lambda:not state()['available'] and state()['demand']==0)
    passed('invalid_sensor_inhibits_demand')
    b.set({'Faults':dumps(dict(invalid=False,hot=False))},target=True)
    until(lambda:state()['available'] and state()['demand']>0)
    stop(prov,kill=True)
    until(lambda:not state()['available'] and state()['demand']==0)
    passed('cached_frame_expires_after_provider_loss')
    prov=service('provider')
    until(lambda:state()['available'] and frame()['demand']>0)
    passed('provider_restart_and_recovery')
    b.set({'Faults':dumps(dict(invalid=True,hot=True))},target=True)
    time.sleep(.4);assert frame()['valid'] and state()['available']
    passed('fault_injection_disabled_by_default')
    stop(ctrl,kill=True)
    until(lambda:frame()['demand']==0)
    passed('controller_loss_provider_watchdog')
    ctrl=service('controller')
    until(lambda:state()['mode']=='OFF' and state()['available'])
    passed('controller_restart_resets_OFF')
    # User-facing command also waits for the matching request acknowledgement.
    client=service('set','--mode','AUTO','--setpoint','26');assert client.wait(timeout=5)==0
    passed('CLI_set_acknowledgement')
    stop(broker,kill=True)
    until(lambda:ctrl.poll() is not None and prov.poll() is not None)
    assert ctrl.returncode!=0 and prov.returncode!=0
    passed('broker_loss_visible_nonzero_exit')
except Exception:
    for i,log in enumerate(logs):
        log.seek(0);print(f'--- Process {i} ---\n'+log.read(),file=sys.stderr)
    raise
finally:
    for proc in reversed(processes):stop(proc)
    b.close()
    for log in logs:log.close()
