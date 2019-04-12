""" Provides the CCMessenger class definition.

Module content
--------------
"""
# The python-cctalk package allows one to send ccTalk messages and decode replies from a ccTalk device.
license_text = "(C) 2011-2019 David Schryer and others GNU GPLv3 or later."
__copyright__ = license_text

__autodoc__ = ['CCMessenger']
__all__ = __autodoc__

import time

from . tools import make_serial_object, send_message_and_get_reply, conv_reply

try:
    basestring
except NameError:
    basestring = str

class CCMessenger(object):
    """This is an object used to talk with ccTalk device.

    It provides functions for requesting and recieving data as
    well as changing the state of the ccTalk device.
    """
    
    messages = dict(
                    reset_device=(1,0,bool),
                    comm_status_vars=(2,3,int),
                    comms_revision=(4,3,int),
                    expansion_0=(100,-1,int),
                    set_accept_limit=(135,0,bool),
                    address_mode=(169,1,int),
                    base_year=(170,4,str),
                    thermistor=(173,1,int),
                    alarm_counter=(176,1,int),
                    bank_select=(178,1,int),
                    coin_id=(184,6,str),
                    modify_coin_id=(185,0,bool),
                    build_code=(192,-1,str),
                    fraud_counter=(193,3,int),
                    reject_counter=(194,3,int),
                    modification_date=(195,2,int),
                    creation_date=(196,2,int),
                    rom_checksum=(197,4,int),
                    teach_status=(201,2,int),
                    teach_mode_control=(202,0,bool),
                    sorter_path=(209,-1,int),
                    coin_position=(212,2,int),
                    option_flags=(213,1,int),
                    data_storage_availability=(216,5,int),
                    sorter_override_status=(221,2,int),
                    accept_counter=(225,3,int),
                    insertion_counter=(226,3,int),
                    master_inhibit_status=(227,1,int),
                    modify_master_inhibit_status=(228,0,bool),
                    read_buffered_credit_or_error_codes=(229,11,int),
                    inhibit_status=(230,2,int),
                    modify_inhibit_status=(231,0,bool),
                    perform_self_check=(232,-1,int),
                    latch_output_lines=(233,0,bool),
                    read_opto_states=(236,2,int),
                    read_input_lines=(237,6,int),
                    test_output_lines=(238,0,bool),
                    test_solenoids=(240,1,int),
                    software_revision=(241,-1,str),
                    serial_number=(242,3,int),
                    database_version=(243,1,int),
                    product_type=(244,-1,str),
                    equipment_category=(245,-1,str),
                    manufacturer_id=(246,-1,str),
                    variable_set=(247,-1,int),
                    status=(248,1,int),
                    polling_priority=(249,2,int),
                    simple_poll=(254,0,bool),
    )

    def _request(self, request, message):

        def __func(data=None, verbose=None, suppress=None):
            if verbose is None:
                verbose = self.verbose

            if suppress is None:
                suppress = self.suppress

            if data is None:
                data = []

            code, expect_body, return_type = message[:3]

            if verbose:
                print('Request: {0} {1}'.format(request, list(data)))

            try:
                head, body = send_message_and_get_reply(self.serial_object, code, data, verbose=int(verbose))
            except IOError as e:
                if not suppress:
                    raise
                else:
                    return None

            if verbose:
                print('Reply: {0} {1}'.format(head, list(body)))

            return conv_reply(head, body, expect_body, return_type)

        return __func
    
    def __init__(self, serial_object, verbose=False, suppress=False):
        if isinstance(serial_object, basestring):
            self.serial_object = make_serial_object(serial_object)
        else:
            self.serial_object = serial_object

        self.requests = {
            r: self._request(r, m) for r,m in self.messages.items()
        }

        self.verbose = verbose
        self.suppress = suppress

    def accept_coins(self, mask=[255,255], **kwargs):
        if len(mask) != 2:
            raise Exception("accept_coins mask must be a 2-ple.")

        return self.requests['modify_inhibit_status'](mask, **kwargs)

    def master_inhibit(self, state=True, **kwargs):
        param = int(not state)
        return self.requests['modify_master_inhibit_status']([param], **kwargs)

    def set_accept_limit(self, coins=1, **kwargs):
        if not isinstance(coins, int):
            raise Exception("The number of coins must be an integer.")

        return self.requests['set_accept_limit']([coins], **kwargs)

    def read_buffer(self, **kwargs):
        return self.requests['read_buffered_credit_or_error_codes'](**kwargs)

    def coin_id(self, slot, **kwargs):
        return self.requests['coin_id']([slot], **kwargs)

    def modify_coin_id(self, slot, text, **kwargs):
        text_raw = list(bytearray('{:.<6}'.format(text).encode()))
        return self.requests['modify_coin_id']([slot] + text_raw, **kwargs)

    def teach_mode_control(self, slot, **kwargs):
        return self.requests['teach_mode_control']([slot], **kwargs)

    def __iter__(self):
        return iter(self.requests)

    def __contains(self, request):
        return request in self.requests

    def __getattr__(self, request):
        try:
            return self.requests[request]
        except KeyError:
            raise NotImplementedError("The `{0}` is not implemented".format(request))

    def __getitem__(self, request):
        return self.__getattr__(request)

    def __call__(self, request, data=None, **kwargs):
        return self[request](data, **kwargs)

    def request(self, request, data=None, **kwargs):
        return self(request, data, **kwargs)
