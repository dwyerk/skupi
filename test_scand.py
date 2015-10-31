"""Test the scand (as best as we can)"""

# pylint: disable=missing-docstring,invalid-name,unnecessary-lambda

from collections import namedtuple
import mock
from nose.tools import eq_, raises

import scand

InputDeviceMock = namedtuple("InputDeviceMock", "name")
EventMock = namedtuple("EventMock", "type keystate scancode")
EventMock.__new__.__defaults__ = (0, 0, 42)

@mock.patch("graphiteudp.init")
def test_init_graphite(graphite_init):
    scand.init_graphite("testserver", "testprefix")
    graphite_init.assert_called_with("testserver", prefix="testprefix")

@mock.patch("scand.ConfigParser")
def test_parse_config(config_mock):
    instance = config_mock.return_value
    scand.parse_config()
    instance.read.assert_called_with("scand.cfg")

@mock.patch("os.path.exists")
@mock.patch("sqlite3.connect")
def test_init_database_default_exists(connect_function, path_exists):
    conn_mock = connect_function.return_value
    path_exists.return_value = True
    scand.init_database()
    path_exists.assert_called_with('scans.sqlite3')
    connect_function.assert_called_with('scans.sqlite3')
    eq_(conn_mock.execute.called, False)

@mock.patch("os.path.exists")
@mock.patch("sqlite3.connect")
def test_init_database_default_missing(connect_function, path_exists):
    conn_mock = connect_function.return_value
    path_exists.return_value = False
    scand.init_database()
    path_exists.assert_called_with('scans.sqlite3')
    connect_function.assert_called_with('scans.sqlite3')
    eq_(conn_mock.execute.called, True)

@mock.patch("os.path.exists")
@mock.patch("sqlite3.connect")
def test_init_database_custom(connect_function, path_exists):
    conn_mock = connect_function.return_value
    path_exists.return_value = False
    scand.init_database('TESTSCAN')
    path_exists.assert_called_with('TESTSCAN')
    connect_function.assert_called_with('TESTSCAN')
    eq_(conn_mock.execute.called, True)

@mock.patch("scand.list_devices")
@mock.patch("scand.InputDevice")
def test_get_input_device_default_present(input_device, list_devices_function):
    list_devices_function.return_value = ['TEST1', scand.SCANNER_NAME]
    input_device.side_effect = lambda name: InputDeviceMock(name)
    device = scand.get_input_device()
    assert isinstance(device, InputDeviceMock)
    eq_(device.name, scand.SCANNER_NAME)

@raises(IndexError)
@mock.patch("scand.list_devices")
@mock.patch("scand.InputDevice")
def test_get_input_device_default_missing(input_device, list_devices_function):
    list_devices_function.return_value = ['TEST1', 'TEST2']
    input_device.side_effect = lambda name: InputDeviceMock(name)
    scand.get_input_device()

@mock.patch("scand.list_devices")
@mock.patch("scand.InputDevice")
def test_get_input_device_nondefault_present(input_device, list_devices_function):
    list_devices_function.return_value = ['TEST1', 'TEST2', scand.SCANNER_NAME]
    input_device.side_effect = lambda name: InputDeviceMock(name)
    device = scand.get_input_device('TEST2')
    assert isinstance(device, InputDeviceMock)
    eq_(device.name, 'TEST2')

@mock.patch("scand.init_graphite")
@mock.patch("scand.init_database")
@mock.patch("scand.get_input_device")
@mock.patch("scand.categorize")
def test_main_no_input(categorize, get_input, init_db, init_graphite):
    SAMPLE_CONFIG = {"graphite": None} # Doesn't emulate the config, but gets the job done
    dev = get_input.return_value
    dev.read_loop.return_value = [EventMock(0), EventMock(0)]
    scand.main(SAMPLE_CONFIG)
    eq_(dev.grab.called, True)
    eq_(dev.read_loop.called, True)
    eq_(categorize.called, False)

@mock.patch("scand.init_graphite")
@mock.patch("scand.init_database")
@mock.patch("scand.get_input_device")
@mock.patch("scand.categorize")
def test_main_input_invalid_keystate(categorize, get_input, init_db, init_graphite):
    SAMPLE_CONFIG = {"graphite": None} # Doesn't emulate the config, but gets the job done
    dev = get_input.return_value
    dev.read_loop.return_value = [EventMock(scand.ecodes.EV_KEY, 0), EventMock(scand.ecodes.EV_KEY)]
    data = categorize.return_value
    data.keystate.return_val
    scand.main(SAMPLE_CONFIG)
    eq_(dev.grab.called, True)
    eq_(dev.read_loop.called, True)
    eq_(categorize.called, True)
