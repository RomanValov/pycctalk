#!/usr/bin/python
# -*- mode: python -*-

# The python-cctalk package allows one to send ccTalk messages and decode replies from a ccTalk device.
license_text = "(C) 2011-2019 David Schryer and others GNU GPLv3 or later."
__copyright__ = license_text

from collections import namedtuple
import time

from cctalk.messenger import CCMessenger


CoinStruct = namedtuple('CoinStruct', ['index', 'value', 'label', 'error'])


class CoinDevice(object):
    def __init__(self, serial_object, timeout=0.1, verbose=0, suppress=None):
        self.cc_messenger = CCMessenger(serial_object, verbose, suppress)
        self.timeout = timeout

        self.coin_id = [0] * 17

        for _ in range(1,17):
            self.coin_id[_] = self.cc_messenger.coin_id(_)

    def __iter__(self):
        self.cc_messenger.reset_device()
        self.cc_messenger.master_inhibit(False)
        self.cc_messenger.accept_coins()

        last_event = 0
        capa_event = 5

        while True:
            time.sleep(self.timeout)

            buff_event = self.cc_messenger.read_buffer()
            coin_event = buff_event.pop(0)

            if last_event > coin_event:
                last_event -= 255

            last_index = coin_event - last_event
            if last_index > capa_event:
                last_index = capa_event

            if not last_index:
                continue

            for _ in range(last_index, 0, -1):
                coin_index = coin_event - _ + 1
                coin_value = buff_event[2*_-2]
                coin_error = buff_event[2*_-1]
                coin_label = self.coin_id[coin_value]

                yield CoinStruct(
                    coin_index,
                    coin_value,
                    coin_label,
                    coin_error
                )

            last_event = coin_event
