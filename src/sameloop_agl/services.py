# SPDX-License-Identifier: MIT
import time
import uuid
from sameloop_plant import Plant, finite
from .contract import Freshness, dumps, obj
from .control import Controller


def controller(broker, stop, period=0.1):
    ctrl, generation, sequence = Controller(), str(uuid.uuid4()), 0
    broker.set({'Settings': dumps(ctrl.accepted)})
    broker.set({'Settings': dumps(ctrl.accepted)}, target=True)
    def command(demand):
        return dumps({'generation': generation, 'sequence': sequence, 'demand': demand})
    try:
        while not stop.is_set():
            started = time.monotonic()
            raw = broker.get(['Settings'], target=True)['Settings']
            ctrl.request(raw)
            ctrl.observe(broker.get(['Frame'])['Frame'], time.monotonic())
            state = ctrl.state(time.monotonic())
            state.update(generation=generation, sequence=sequence)
            broker.set({'Command': command(state['demand'])}, target=True)
            broker.set({'Settings': dumps(ctrl.accepted), 'State': dumps(state),
                        'Mode': ctrl.mode, 'Setpoint': ctrl.setpoint,
                        'Available': state['available'], 'Overheat': state['overheat'],
                        'FanDemand': state['demand'], 'Error': state['error']})
            sequence += 1
            stop.wait(max(0, period-(time.monotonic()-started)))
    finally:
        try:
            broker.set({'Command': command(0.0)}, target=True)
            broker.set({'Available': False, 'FanDemand': 0.0})
        except Exception:
            pass  # Original RPC error remains visible; provider watchdog expires.


def provider(broker, stop, allow_faults=False, period=0.1):
    plant, clock = Plant(), Freshness()
    generation, sequence = str(uuid.uuid4()), 0
    demand, valid, heat = 0.0, True, 0.18
    broker.set({'Command': '', 'Faults': ''}, target=True)  # No cached actuation after restart.
    last = time.monotonic()
    last_fault = None
    def advance(now):
        nonlocal last, demand
        expiry = clock.received + 1.0 if clock.received is not None else last
        # Split at watchdog deadline; no retroactive use of a newly received command.
        mid = max(last, min(now, expiry))
        if mid > last:
            plant.step(min(mid-last,60), demand, heat)
        if now > mid:
            plant.step(min(now-mid,60), 0.0, heat)
        if now >= expiry:
            demand = 0.0
        last = now
    try:
        while not stop.is_set():
            started = time.monotonic()
            targets = broker.get(['Command', 'Faults'], target=True)
            now = time.monotonic()
            if now-last > 60:
                raise RuntimeError('Pause supérieure à 60 s : redémarrage explicite requis')
            advance(now)
            raw = targets['Command']
            if raw:
                try:
                    c = obj(raw)
                    value = finite(c.get('demand'),0,100,'demand')
                    if clock.accept(c, now):
                        demand = value
                except (ValueError, TypeError):
                    demand = 0.0
            raw_fault = targets['Faults']
            if allow_faults and raw_fault and raw_fault != last_fault:
                last_fault = raw_fault
                try:
                    f = obj(raw_fault)
                    if type(f.get('invalid')) is not bool or type(f.get('hot')) is not bool:
                        raise ValueError('invalid/hot bool requis')
                    valid, heat = not f['invalid'], 1.2 if f['hot'] else 0.18
                except (ValueError, TypeError):
                    pass
            frame = dict(generation=generation,sequence=sequence,valid=valid,
                         temperature=plant.temperature,applied=plant.applied,rpm=plant.rpm,
                         demand=demand,simulation_time=plant.elapsed)
            broker.set({'Frame': dumps(frame), 'Temperature': plant.temperature,
                        'SensorValid': valid, 'FanApplied': plant.applied, 'FanRpm': plant.rpm,
                        'Command': dumps({'demand':demand, 'watchdog_expired':not clock.fresh(now)})})
            sequence += 1
            stop.wait(max(0, period-(time.monotonic()-started)))
    finally:
        try:
            broker.set({'SensorValid': False, 'Frame': dumps(dict(
                generation=generation, sequence=sequence, valid=False,
                temperature=plant.temperature, applied=plant.applied,rpm=plant.rpm))})
        except Exception:
            pass
