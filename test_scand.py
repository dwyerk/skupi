"""Test the scand (as best as we can)"""

import mock
from nose.tools import eq_

import scand

@mock.patch("graphiteudp.init")
def test_init_graphite(graphite_init):
    scand.init_graphite("testserver", "testprefix")
    graphite_init.assert_called_with("testserver", prefix="testprefix")

@mock.patch("scand.ConfigParser")
def test_parse_config(config_mock):
    instance = config_mock.return_value
    scand.parse_config()
    instance.read.assert_called_with("scand.cfg")
