""" Provides tools for general use.

Module content
--------------
"""
# The python-cctalk package allows one to send ccTalk messages and decode replies from a ccTalk device.
license_text = "(C) 2011-2019 David Schryer and others GNU GPLv3 or later."
__copyright__ = license_text

__autodoc__ = ['make_serial_object', 'drop_to_ipython', 'make_msg', 'send_message_and_get_reply', 'interpret_reply']
__all__ = __autodoc__

import os
import serial
import time
import subprocess
from struct import unpack


def make_msg(code, data=None, to_slave_addr=None, from_host_addr=None):
    if not data:
        seq = [to_slave_addr, 0, from_host_addr, code]
    else:
        seq = [to_slave_addr, len(data), from_host_addr, code] + data
    message_sum = 0
    for i in seq:
        message_sum += i
    end_byte = 256 - (message_sum%256)
    message = seq + [end_byte]
    return message


def _write_message(serial_object, message, data, slave, host, verbose):
    data = bytearray(make_msg(message, data, slave, host))
    data_length = len(data)

    if verbose > 1:
        print("Send {0} bytes: {1}".format(len(data), list(data)))

    sent = serial_object.write(data)

    if sent != data_length:
        raise IOError("Sent only {0} bytes of total {1} bytes.".format(sent, data_length))

    echo = bytearray(serial_object.read(sent))

    if verbose > 2:
        print("Echo {0} bytes: {1}".format(len(echo), list(echo)))

    if not echo == data:
        raise IOError("Unexpected echo output.")

    return sent


def _read_message(serial_object, slave, host, verbose):

    head = bytearray(serial_object.read(4))

    # header: destination, length, source, message_id

    try:
        read_length = head[1]+1
    except IndexError:
        read_length = 0

    body = bytearray(serial_object.read(read_length))
    recv = head + body

    if verbose > 1:
        print("Recv {0} bytes: {1}".format(len(recv), list(recv)))

    if len(recv) < 5:
        return IOError("Reply head is too short.")

    if head[0] != host or head[2] != slave:
        raise IOError("Unexpected addresses.")

    if len(body) < read_length:
        return IOError("Reply body is too short.")

    # TODO: check checksum

    return head[3], body[:-1]


def send_message_and_get_reply(serial_object, code, data=None, slave=2, host=1, verbose=False):
    if not serial_object.isOpen():
        raise RuntimeError("The serial port is not open.")

    serial_object.timeout = 1
    serial_object.inter_byte_timeout = 0.1 # should be 0.05 but linux doesn't support it
    serial_object.reset_input_buffer()
    serial_object.reset_output_buffer()

    # send
    sent = _write_message(serial_object, code, data, slave, host, verbose)

    # recv
    return _read_message(serial_object, slave, host, verbose)

def conv_reply(head, body, expect_body, return_type):
    if expect_body != -1 and len(body) != expect_body:
        raise ValueError("Received {0} bytes but expected {1} bytes".format(len(body), expect_body))
    if return_type is not bool and head:
        raise ValueError("Device error: {0}.".format(head))

    if return_type is str:
        return body.decode()
    elif return_type is int:
        return list(body)
    elif return_type is bool:
        return not bool(head)
    else:
        return return_type(recv)

def make_serial_object(tty_port):
    """Makes a serial object that can be used for talking with the ccTalk device.

    port_type is a string that can currently only be equal to 'coin_validator'.

    Paramters
    ---------
    port_type : str
      Type of port to connect to.  Currently only 'coin_validator is valid.'

    Returns
    -------
    serial_object : object made by :py:class:`serial.Serial`
    """
    
    return serial.Serial(port=tty_port,
                         baudrate=9600,
                         parity=serial.PARITY_NONE,
                         stopbits=serial.STOPBITS_ONE,
                         bytesize=serial.EIGHTBITS,
                         )

def drop_to_ipython(local_variables, *variables_to_inspect):
    '''
    Drops to ipython at the point in the code where it is called to inspect the variables passed to it.

    Parameters
    ----------
    local_variables : list
      Usually one would pass the output of locals().
    variables_to_inspect: tuple
      All variables passed to this routine are wrapped into a tuple.
    '''

    from IPython.terminal.embed import InteractiveShellEmbed

    try:
        call_name = local_variables['self'].__module__
    except Exception:
        call_name = "Module"

    b = 'Dropping into IPython'
    em = 'Leaving Interpreter, back to program.'
    msg = '***Called from %s. Hit Ctrl-D to exit interpreter and continue program.'
    ipshell = InteractiveShellEmbed([], banner1=b, exit_msg=em)
    ipshell(msg %(call_name))

