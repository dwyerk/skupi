"""Test the scand (as best as we can)"""

# pylint: disable=missing-docstring,invalid-name,unnecessary-lambda

import mock
from nose.tools import eq_, raises

import scand

class InputDeviceMock(object):
    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name

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

