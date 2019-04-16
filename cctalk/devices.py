#!/usr/bin/python
# -*- mode: python -*-

# The python-cctalk package allows one to send ccTalk messages and decode replies from a ccTalk device.
license_text = "(C) 2011-2019 David Schryer and others GNU GPLv3 or later."
__copyright__ = license_text

from collections import namedtuple
import time

from cctalk.messenger import CCMessenger


CoinStruct = namedtuple('CoinStruct', ['index', 'value', 'worth', 'error'])


class CoinDevice(object):
    def __init__(self, serial_object, worths=None, timeout=0.1, verbose=0, suppress=None):
        self.cc_messenger = CCMessenger(serial_object, verbose=verbose, suppress=suppress)
        self.timeout = timeout

        self.worths = worths
        self.values = dict()

        self.pmasks = []
        for _ in range(1,17):
            label = self.cc_messenger.coin_id(_)

            if self.worths is None:
                worth = label
            else:
                worth = self.worths.get(label, None)

            if worth:
                self.pmasks.append(self.cc_messenger.coin_position([_]))
                self.values[_] = worth

        # assuming coin positions are orthogonal sum is `or`-equivalent
        # also reversing pmask probably due to emp-specific order issue
        self.pmask = list(reversed([sum(_) for _ in zip(*self.pmasks)]))

        self.cc_messenger.reset_device()
        self.cc_messenger.master_inhibit(False)
        self.cc_messenger.accept_coins(self.pmask)

    def __iter__(self):
        last_event = None
        capa_index = 5

        while self.cc_messenger.simple_poll():
            time.sleep(self.timeout)

            buff_event = self.cc_messenger.read_buffer()
            coin_event = buff_event.pop(0)

            if not coin_event or last_event is None:
                last_event = coin_event
                continue

            if last_event > coin_event:
                last_event -= 255

            last_index = coin_event - last_event
            if last_index > capa_index:
                last_index = capa_index

            if not last_index:
                continue

            for _ in range(last_index, 0, -1):
                coin_index = coin_event - _ + 1
                coin_value = buff_event[2*_-2]
                coin_error = buff_event[2*_-1]

                if coin_value:
                    coin_worth = self.values[coin_value]
                else:
                    coin_worth = ''

                yield CoinStruct(
                    coin_index,
                    coin_value,
                    coin_worth,
                    coin_error,
                )

            last_event = coin_event
