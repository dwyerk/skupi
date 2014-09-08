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

scancodes = {
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

scanner_name = 'WIT Electron Company WIT 122-UFS V2.03'

def main():
    graphiteudp.init('carbon', prefix='humangeo.kitchen.pi')
    dbfile = os.path.join(os.environ.get('HOME'), 'scans.sqlite3')
    dbfile = 'scans.sqlite3'
    need_schema = False
    if not os.path.exists(dbfile):
        need_schema = True

    db = sqlite3.connect(dbfile)

    if need_schema:
        db.execute('create table scans(barcode text, timestamp datetime, event_id text)')

    dev = [InputDevice(device) for device in list_devices()
           if InputDevice(device).name == scanner_name][0]

    def signal_handler(signal, frame):
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
                    db.execute(
                        'insert into scans (barcode, timestamp, event_id) ' +
                        'values (:barcode, :timestamp, :event_id)',
                        [barcode, timestamp, event_id.get_urn()])
                    db.commit()
                    barcode = ""
                else:
                    try:
                        barcode += scancodes[data.scancode]
                    except KeyError:
                        print >>sys.stderr, "Unknown scancode: {0}".format(data.scancode)


if __name__ == '__main__':
    main()
