import unittest
from sameloop_agl.control import Controller
from sameloop_agl.contract import Freshness,dumps

def frame(seq=0,gen='sensor',temperature=32.4,valid=True):
    return dumps(dict(generation=gen,sequence=seq,temperature=temperature,applied=0,rpm=0,valid=valid))

class ControlTests(unittest.TestCase):
    def test_two_frames_required_and_cached_frame_expires(self):
        c=Controller();c.observe(frame(),0);self.assertFalse(c.state(0)['available'])
        c.observe(frame(1),.1);self.assertTrue(c.state(.1)['available'])
        c.observe(frame(1),1.09);self.assertTrue(c.state(1.09)['available'])
        self.assertFalse(c.state(1.1)['available'])
    def test_mode_and_clamp(self):
        c=Controller();c.observe(frame(),0);c.observe(frame(1),.1)
        self.assertEqual(c.state(.1)['demand'],0)
        c.request(dumps(dict(id='a',mode='AUTO',setpoint=25)));self.assertEqual(c.state(.1)['demand'],100)
        c.request(dumps(dict(id='b',mode='AUTO',setpoint=40)));self.assertEqual(c.state(.1)['demand'],0)
    def test_invalid_settings_atomic(self):
        c=Controller()
        for raw in ['{}',dumps(dict(id='bad',mode='AUTO',setpoint=41)),dumps(dict(id='bad',mode='AUTO',setpoint=True)),'{"id":"bad","mode":"AUTO","setpoint":NaN}']:
            self.assertFalse(c.request(raw));self.assertEqual((c.mode,c.setpoint),('OFF',25));self.assertTrue(c.error)
    def test_alarm_independent_off_and_preserved_unknown(self):
        c=Controller();c.observe(frame(0,temperature=55),0);c.observe(frame(1,temperature=55),.1)
        self.assertTrue(c.state(.1)['overheat']);self.assertEqual(c.state(.1)['demand'],0)
        c.observe(frame(2,valid=False),.2)
        self.assertTrue(c.state(.2)['overheat']);self.assertEqual(c.state(.2)['alarm_quality'],'unavailable')
    def test_restart_requires_second_frame(self):
        c=Controller();c.observe(frame(),0);c.observe(frame(1),.1)
        c.observe(frame(0,gen='new'),.2);self.assertFalse(c.state(.2)['available'])
        c.observe(frame(1,gen='new'),.3);self.assertTrue(c.state(.3)['available'])
    def test_old_generation_and_out_of_order_rejected(self):
        f=Freshness();self.assertTrue(f.accept(dict(generation='a',sequence=4),0))
        self.assertFalse(f.accept(dict(generation='a',sequence=3),.2))
        self.assertTrue(f.accept(dict(generation='b',sequence=0),.3))
        self.assertFalse(f.accept(dict(generation='a',sequence=5),.4))
    def test_invalid_frame_inhibits(self):
        c=Controller();c.observe(frame(),0);c.observe(frame(1),.1);c.observe('{}',.2)
        self.assertFalse(c.state(.2)['available'])
if __name__=='__main__':unittest.main()
