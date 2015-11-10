#!/usr/bin/env python
"""
skupi scanning daemon

Run me with supervisord!
"""

from evdev import InputDevice, ecodes, list_devices, categorize
import signal, sys
import sqlite3
import os
import uuid
import time
import graphiteudp
from ConfigParser import ConfigParser

SCANCODES = {
    # Scancode: ASCIICode
    0: None, 1: u'ESC', 2: u'1', 3: u'2', 4: u'3', 5: u'4', 6: u'5', 7: u'6',
    8: u'7', 9: u'8', 10: u'9', 11: u'0', 12: u'-', 13: u'=', 14: u'BKSP',
    15: u'TAB', 16: u'Q', 17: u'W', 18: u'E', 19: u'R', 20: u'T', 21: u'Y',
    22: u'U', 23: u'I', 24: u'O', 25: u'P', 26: u'[', 27: u']', 28: u'CRLF',
    29: u'LCTRL', 30: u'A', 31: u'S', 32: u'D', 33: u'F', 34: u'G', 35: u'H',
    36: u'J', 37: u'K', 38: u'L', 39: u';', 40: u'"', 41: u'`', 42: u'LSHFT',
    43: u'\\', 44: u'Z', 45: u'X', 46: u'C', 47: u'V', 48: u'B', 49: u'N',
    50: u'M', 51: u',', 52: u'.', 53: u'/', 54: u'RSHFT', 56: u'LALT',
    57: ' ', 100: u'RALT'
}

SCANNER_NAME = 'WIT Electron Company WIT 122-UFS V2.03'

def init_graphite(server, prefix):
    """Initializes the graphite settings

    :param server: The graphite server to connect to
    :param prefix: The prefix to prepend to sent data

    """
    print "Initializing graphiteudp, server: {}, prefix: {}".format(server, prefix)
    graphiteudp.init(server, prefix=prefix)

def init_database(dbfile='scans.sqlite3'):
    """Initialize the database

    :param dbfile: The database file to base on
    :returns: The database connnection

    """
    need_schema = False
    if not os.path.exists(dbfile):
        need_schema = True

    connection = sqlite3.connect(dbfile)

    if need_schema:
        connection.execute('create table scans(barcode text, timestamp datetime, event_id text)')
    return connection

def get_input_device(name=SCANNER_NAME):
    """Get the scanner

    :param name: The (reported) name of the scanner
    :returns: The scanning device

    """
    dev = [InputDevice(device) for device in list_devices()
           if InputDevice(device).name == name][0]
    return dev

def main(config):
    """Initializes the scanner and runs the main event loop.

    :param config: Scanner configuration object

    """
    init_graphite(config.get("graphite", "server"), config.get("graphite", "prefix"))

    connection = init_database()
    dev = get_input_device()

    def signal_handler(incoming_signal, dataframe): # pylint: disable=unused-argument
        """Handle SIGINTs

        :param incoming_signal: The signal
        :param dataframe: The data associated with the signal.

        """
        print 'Stopping'
        dev.ungrab()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    dev.grab()

    barcode = ""
    last_event_time = 0
    last_event_id = None

    for event in dev.read_loop():
        if event.type == ecodes.EV_KEY:
            data = categorize(event)
            # Catch only keydown, and not Enter
            if data.keystate == 1 and data.scancode != 42:
                if data.scancode == 28:
                    timestamp = time.time()

                    if timestamp - last_event_time < 10:
                        event_id = last_event_id
                    else:
                        event_id = uuid.uuid1()
                        last_event_id = event_id

                    last_event_time = timestamp

                    graphiteudp.send('event.scan', 1)
                    connection.execute(
                        'insert into scans (barcode, timestamp, event_id) ' +
                        'values (:barcode, :timestamp, :event_id)',
                        [barcode, timestamp, event_id.get_urn()])
                    connection.commit()
                    barcode = ""
                else:
                    try:
                        barcode += SCANCODES[data.scancode]
                    except KeyError:
                        print >>sys.stderr, "Unknown scancode: {0}".format(data.scancode)

def parse_config():
    """Parse out the scand configuration settings.

    :returns: The parsed configuration

    """
    config_parser = ConfigParser()
    config_parser.read("scand.cfg")
    return config_parser

if __name__ == '__main__':
    CONFIG = parse_config()
    main(CONFIG)
