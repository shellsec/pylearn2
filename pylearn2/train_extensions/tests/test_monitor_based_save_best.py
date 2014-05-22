import os
import tempfile
from pylearn2.models.model import Model
from pylearn2.train_extensions.best_params import MonitorBasedSaveBest


class MockModel(Model):
    """An empty model."""
    pass


class MockChannel(object):
    """A mock object for MonitorChannel."""
    def __init__(self):
        self.val_record = []


class MockMonitor(object):
    """A mock object for Monitor."""
    def __init__(self):
        self.channels = {}


def test_tagging():
    try:
        # TODO: serial.save should be able to take an open file-like object so
        # we can direct its output to a StringIO or something and not need to
        # screw around like this in tests that don't actually need to touch
        # the filesystem. /dev/null would work but the test would fail on
        # Windows.
        fd, fn = tempfile.mkstemp(suffix='.pkl')
        os.close(fd)

        # Test that the default key gets created.
        def_model = MockModel()
        def_model.monitor = MockMonitor()
        def_ext = MonitorBasedSaveBest(channel_name='foobar', save_path=fn)
        def_ext.setup(def_model, None, None)
        assert 'MonitorBasedSaveBest' in def_model.tag

        # Test with a custom key.
        model = MockModel()
        model.monitor = MockMonitor()
        model.monitor.channels['foobar'] = MockChannel()
        ext = MonitorBasedSaveBest(channel_name='foobar', tag_key='test123',
                                   save_path=fn)
        # Best cost is initially infinity.
        ext.setup(model, None, None)
        assert model.tag['test123']['best_cost'] == float("inf")
        # Best cost after one iteration.
        model.monitor.channels['foobar'].val_record.append(5.0)
        ext.on_monitor(model, None, None)
        assert model.tag['test123']['best_cost'] == 5.0
        # Best cost after a second, worse iteration.
        model.monitor.channels['foobar'].val_record.append(7.0)
        ext.on_monitor(model, None, None)
        assert model.tag['test123']['best_cost'] == 5.0
        # Best cost after a third iteration better than 2 but worse than 1.
        model.monitor.channels['foobar'].val_record.append(6.0)
        ext.on_monitor(model, None, None)
        assert model.tag['test123']['best_cost'] == 5.0
        # Best cost after a fourth, better iteration.
        model.monitor.channels['foobar'].val_record.append(3.0)
        ext.on_monitor(model, None, None)
        assert model.tag['test123']['best_cost'] == 3.0
    finally:
        os.remove(fn)
