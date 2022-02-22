#
# Copyright 2016-2019
# 
# Bernd-Christian Renner, Jan Heitmann, and
# Hamburg University of Technology (TUHH).
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

import struct
import collections
import time
import string

HEADER_FORMAT = 'BBBBBB'
FOOTER_FORMAT = 'BBBBBB'


# PAYLOAD_MAXLEN = 2**LENGTH_SIZE
TYPE_SIZE = 8
ADDRESS_SIZE = 8
MM_TYPE_ACK = (2**TYPE_SIZE) - 1
MM_ADDR_BCAST = (2**ADDRESS_SIZE) - 1

# ACK_TYPE
ACK_NONE = 0
ACK_PLAIN = 1
ACK_RANGE = 2


Header = collections.namedtuple('Header', ['src', 'dst', 'type', 'status', 'dsn', 'len'])
Packet = collections.namedtuple('Packet', ['header', 'payload', 'footer'])
Footer = collections.namedtuple('Footer', ['power', 'rssi', 'biterrors', 'agcMean', 'agcMin', 'agcMax'])


def byteArrayToPacket(rxBytes):
    """Convert received byte array to packet."""
    headLen = len(HEADER_FORMAT)
    headerBytes = rxBytes[0:headLen]
    header = Header(*struct.unpack(HEADER_FORMAT, headerBytes))
    paylen = header.len
    payload = rxBytes[headLen:(headLen+paylen)]
    if(header.type < 0x80 and
       ((len(rxBytes) - headLen - paylen) == len(FOOTER_FORMAT))):
            footerBytes = rxBytes[(headLen+paylen):]
            footer = Footer(*struct.unpack(FOOTER_FORMAT, footerBytes))
    else:
        footer = Footer(0, 0, 0, 0, 0, 0)
    return Packet(header, payload, footer)


def makePacket(src=0, dst=MM_ADDR_BCAST, type=0, ack=ACK_NONE, dsn=0, payload=bytes()):
    status = ack
    paylen = len(payload)
    header = Header(src, dst, type, status, dsn, paylen)
    footer = Footer(0, 0, 0, 0, 0, 0)
    pkt = Packet(header, payload, footer)
    return pkt


def getHeaderBytes(pkt):
    headerBytes = bytearray()
    headerBytes += struct.pack(HEADER_FORMAT, *pkt.header)
    return headerBytes


def getFooterBytes(pkt):
    footerBytes = bytearray()
    footerBytes += struct.pack(FOOTER_FORMAT, *pkt.footer)
    return footerBytes


def getBytes(pkt):
    pktbytes = bytearray()
    pktbytes += struct.pack(HEADER_FORMAT, *pkt.header)
    pktbytes += pkt.payload
    pktbytes += struct.pack(FOOTER_FORMAT, *pkt.footer)
    return pktbytes


def printPacket(pkt):
    print("src: ", pkt.header.src, " => dst:", pkt.header.dst)
    print("type: ", hex(pkt.header.type), "seq: ", pkt.header.dsn)
    print("status: {:08b}".format(pkt.header.status))
    print("  ack: ", (pkt.header.status & 0x01))
    print("  rangeack: ", (pkt.header.status & 0x02))
    print("payload: ", pkt.payload)
    
    
def byteArray2HexString(byteArray):
    return "".join("%02X " % b for b in byteArray)

def printRxRaw(pkt):
    output = getRxRaw(pkt)
    print("")
    print(output)
    
def getRxRaw(pkt):
    res = getHeaderBytes(pkt)
    res += pkt.payload
    if(pkt.header.type < 0x80):
        res += getFooterBytes(pkt)
    output = "RX@"
    output += "{:.3f}".format(time.time())
    output += " "
    output += byteArray2HexString(res)
    output += "("
    output += "".join(filter(
                 lambda x: x in string.printable,
                 pkt.payload.decode('ascii', 'ignore')))
    output += ")"
    return output

cmdTypeList = {
    "version" : 0x80,
    "cpuspeed" : 0x82,
    "config" : 0x83,
    "id" : 0x84,
    "batvoltage" : 0x85,
    "startbootloader" : 0x86,
    "reset" : 0x87,
    "freqbandsnum" : 0x90,
    "freqbands" : 0x91,
    "freqcarriersnum" : 0x90,
    "freqcarriers" : 0x93,
    "rxthresh" : 0x94,
    "spreadcode" : 0x95,
    "filterraw" : 0x96,
    "synclen" : 0x96,
    "agc" : 0x98,
    "rxgain" : 0x99,
    "distanceto" : 0xA9,
    "powerlevel" : 0xB8,
    "packetstat" : 0xC0,
    "packetstatclear" : 0xC1,
    "syncstat" : 0xC2,
    "syncstatclear" : 0xC3,
    "sfdstat" : 0xC4,
    "sfdstatclear" : 0xC5,
    "allstat" : 0xC6,
    "allstatclear" : 0xC7,
    "rangedelay" : 0xA8,
    "rxlevel" : 0xB9,
    "sniffingmode" : 0xA1,
    "peakwinlen" : 0x9B,
    "transducer" : 0x9C,
    "testfreq" : 0xB1,
    "testsweep" : 0xB2,
    "testnoise" : 0xB3,
    "txgain" : 0x9A
    }
