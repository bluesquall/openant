# ANT - Multiple Heart Rate Monitor Example
#
# Copyright (c) 2017, M J Stanway
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

from __future__ import absolute_import, print_function

from ant.easy.node import Node
from ant.easy.channel import Channel
from ant.base.message import Message

import logging
import struct
import threading
import sys

NETWORK_KEY= [0xb9, 0xa5, 0x21, 0xfb, 0xbd, 0x72, 0xc3, 0x45]

def interpret_common_bytes(data, verbosity=0):
    """Decode data common to both current and legacy formats.

    HR was the first device profile defined, and does not use the standard
    ANT+ data page numbered message format. But both legacy and modern devices
    encode event time, heart beat count, and computed heart rate, in the last
    few bytes (4-7).
    """
    et, hb, hr = struct.unpack('!HBB', data[4:8].tobytes())
    if verbosity > 2:
        msg = "raw: {0:08b} {1:08b} {2:08b} {3:08b}"
        print(msg.format(data[4], data[5], data[6], data[7]))
    if verbosity > 1:
        msg = "Event Time: {0:0d}, Heart Beat Count: {1:0d}"
        print(msg.format(et, hb))
    if verbosity > 0:
        msg = "Computed Heart Rate: {0:0d} [BPM]"
        print(msg.format(hr))
    return et, hb, hr

def check_pages(data, verbosity=0):
    """Check page change toggle bit and interpret modern pages if available
    """
    if verbosity > 2:
        msg = "length: {0}, first byte: {1:08b}"
        print(msg.format(len(data), data[0]))

    #TODO# find a more pythonic way to separate the first 7 bits
    hdr = bin(data[0])
    #data_page_number = int(hdr[:-1], 2)
    #page_change_toggle = bool(int(hdr[-1]))
    data_page_number = int(hdr[3:], 2)
    page_change_toggle = bool(int(hdr[2]))
    print("# {0}, toggle {1}".format(data_page_number, page_change_toggle))

    if data_page_number is 2:
        manufacturer, serial_number = struct.unpack('!bH', data[1:4].tobytes())
        msg = "manufacturer: {0:b}, serial number: {1:b}"
        print(msg.format(manufacturer, serial_number))
    else:
        print("data page {0:0d}".format(data_page_number))
    #TODO# Implement more pages



def on_data(data, verbosity=3):
    check_pages(data, verbosity)
    et, hb, hr = interpret_common_bytes(data, verbosity)

def main():
    # logging.basicConfig()

    node = Node()
    node.set_network_key(0x00, NETWORK_KEY)

    channel = node.new_channel(Channel.Type.BIDIRECTIONAL_RECEIVE)

    channel.on_broadcast_data = on_data
    channel.on_burst_data = on_data

    channel.set_period(8070)
    channel.set_search_timeout(12)
    channel.set_rf_freq(57)
    channel.set_id(0, 120, 0)

    try:
        channel.open()
        node.start()
    finally:
        node.stop()

if __name__ == "__main__":
    main()

