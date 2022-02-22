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

"""Module for modem."""

from common import packet
from common.packet import makePacket
from common.packet import byteArrayToPacket, byteArray2HexString
import serial
import os
import time
import threading


class Modem2():
    """An Acoustic Underwater Modem."""
    
    def __init__(self, serialDevice=None):
        """Initialize modem."""
        self.txDelay = 0.1
        self.seqNumber = 0
        self.serialDevice = serialDevice
        self.rxCallbacks = []
        self.logFile = None
        if self.serialDevice is not None:
            self._open()
        
    def isSerialConOpen(self):
        """Check if modem is connected through serial interface"""
        return self.serConn.isOpen()

    def __del__(self):
        """Close all files and connections before termination."""
        self.close()

    def addRxCallback(self, cb):
        """Add a function to be called on rx pkt."""
        self.rxCallbacks.append(cb)

    def removeRxCallback(self, cb):
        """Remove a function to be called on rx pkt."""
        if cb in self.rxCallbacks:
            self.rxCallbacks.remove(cb)

    def close(self):
        """Terminate."""
        try:
            self.serConn.close()
        except:
            pass
        if self.logFile is not None:
            self.logFile.close()
        self.rxThread.join()

    def _open(self):
        """Open the serial connection to the modem."""
        self.serConn = serial.Serial(
                port=self.serialDevice,
                baudrate=115200,
                # baudrate=57600,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=0.1
        )
        self.rxThread = threading.Thread(target=self._receivePacket)
        self.rxThread.start()

    def _receivePacket(self):
        """Process packet received from the modem via serial interface"""
        flagDLE = False
        flagInPacket = False
        DLE = 0x10
        STX = 0x02
        ETX = 0x03
        res = bytearray()
        while self.serConn:
            rx = self.serConn.read(1)
            if not self.serConn.isOpen():
                return
            rx += self.serConn.read(self.serConn.in_waiting)
            for b in rx:
                if not flagDLE:
                    # last char was no DLE -> simply
                    if (b == DLE):
                        flagDLE = True
                    elif (flagInPacket):
                        res.append(b)
                else:
                    # found a new packet start
                    # (DLE STX and not inside another packet)
                    if (b == STX and not flagInPacket):
                        flagDLE = False
                        flagInPacket = True

                    # found packet end (DLE ETX and inside packet)
                    elif (b == ETX and flagInPacket):
                        # NOTE check crc here, if added
                        if self.logFile is not None and not self.logFile.closed:
                            self.logFile.write("{:.3f}".format(time.time()) + " " + byteArray2HexString(res) + "\n")
                            self.logFile.flush()
                            os.fsync(self.logFile.fileno())
                        pkt = byteArrayToPacket(res)
                        for f in self.rxCallbacks:
                            f(pkt)
                        flagInPacket = False
                        flagDLE = False
                        del res[:]
                    # stuffed DLE (sent char was a DLE)
                    elif (b == DLE and flagInPacket):
                        flagDLE = False
                        res.append(b)
                    # we ran into something that shouldn't happen
                    # -> abort reception
                    elif (flagInPacket):
                        del res[:]
                        flagInPacket = False
                        flagDLE = False
        return

    def send(self, src, dst, type, payload, status=None, dsn=None):
        """Send a packet."""
        if dsn is None or dsn > 255:
            dsn = self.seqNumber

        pkt = makePacket(src, dst, type, status, dsn, payload)
        return self._sendPacket(pkt)
    
    def _sendPacket(self, pkt):
        """Send a packet."""
#         print("Send Packet to modem")
        #merge header and payload to bytearray
        pktbytes = packet.getHeaderBytes(pkt)
        pktbytes += pkt.payload

        #add start, stuffing and end sequence
        tx = bytearray([0x10, 0x02]) # start Packet
        for b in pktbytes:
            tx.append(b)
            if b == 0x10:
                tx.append(b) # stuffing
        tx.extend([0x10, 0x03])  # end packet

        self.seqNumber += 1
        self.seqNumber = (self.seqNumber % 256)

        output = "TX@"
        output += "{:.3f}".format(time.time())
        output += " "
        output += byteArray2HexString(pktbytes)
        
#         if self.logFile is not None and not self.logFile.closed:
#             self.logFile.write(output + "\n")
#             self.logFile.flush()
#             os.fsync(self.logFile.fileno())
        print(output)
        # packet.printPacket(pkt)

        self.serConn.write(tx)

        time.sleep( self.txDelay )

        return 0

    def getVersion(self):
        """Get firmware version."""
        pkt = makePacket(type=0x80)
        return self._sendPacket(pkt)

    def getCpuSpeed(self):
        """Get CPU speed."""
        pkt = makePacket(type=0x82)
        return self._sendPacket(pkt)

    def getBatVoltage(self):
        """Get Battery Voltage."""
        pkt = makePacket(type=0x85)
        return self._sendPacket(pkt)

    def getConfig(self):
        """Get modem config."""
        pkt = makePacket(type=0x83)
        return self._sendPacket(pkt)

    def getDistanceTo(self, id):
        """Get stored distance to another modem."""
        data = bytearray()
        if id is not None:
            data = id.to_bytes(1, 'big')
        pkt = makePacket(type=0xA9, payload=data)
        return self._sendPacket(pkt)

    def getPowerLevel(self):
        """Get power level."""
        pkt = makePacket(type=0xB8)
        return self._sendPacket(pkt)

    def getPacketStat(self):
        """Get packet statistics."""
        pkt = makePacket(type=0xC0)
        return self._sendPacket(pkt)

    def clearPacketStat(self):
        """Clear packet statistics."""
        pkt = makePacket(type=0xC1)
        return self._sendPacket(pkt)

    def getSyncStat(self):
        """Get sync statistics."""
        pkt = makePacket(type=0xC2)
        return self._sendPacket(pkt)

    def clearSyncStat(self):
        """Clear sync statistics."""
        pkt = makePacket(type=0xC3)
        return self._sendPacket(pkt)

    def getSfdStat(self):
        """Get sfd statistics."""
        pkt = makePacket(type=0xC4)
        return self._sendPacket(pkt)

    def clearSfdStat(self):
        """Clear sfd statistics."""
        pkt = makePacket(type=0xC5)
        return self._sendPacket(pkt)

    def getAllStat(self):
        """Get all TX/RX statistics."""
        pkt = makePacket(type=0xC6)
        return  self._sendPacket(pkt)

    def clearAllStat(self):
        """Clear all TX/RX statistics."""
        pkt = makePacket(type=0xC7)
        return self._sendPacket(pkt)

    def freqBandsNum(self, num=None):
        """Get or Set number of freq bands."""
        data = bytearray()
        if num is not None:
            data = num.to_bytes(1, 'big')
        pkt = makePacket(type=0x90, payload=data)
        return self._sendPacket(pkt)

    def freqBands(self):
        """Get or Set freq bands."""
        print("WARNING: No setter for freqBands implemented.")
        data = bytearray()
        pkt = makePacket(type=0x91, payload=data)
        return self._sendPacket(pkt)

    def freqCarrierNum(self, num=None):
        """Get or Set number of carriers."""
        data = bytearray()
        if num is not None:
            data = num.to_bytes(1, 'big')
        pkt = makePacket(type=0x90, payload=data)
        return self._sendPacket(pkt)

    def freqCarriers(self):
        """Get or Set carriers."""
        print("WARNING: No setter for freqCarriers implemented.")
        data = bytearray()
        pkt = makePacket(type=0x93, payload=data)
        return self._sendPacket(pkt)

    def rangeDelay(self, delay=None):
        """Set delay for ranging answer."""
        data = bytearray()
        if delay is not None:
            data = delay.to_bytes(4, 'big')
        pkt = makePacket(type=0xA8, payload=data)
        return self._sendPacket(pkt)

    def rxThresh(self, thresh=None):
        """Get or Set rx threshold."""
        data = bytearray()
        if thresh is not None:
            data = thresh.to_bytes(1, 'big')
        pkt = makePacket(type=0x94, payload=data)
        return self._sendPacket(pkt)

    def rxLevel(self):
        """Get rx level."""
        pkt = makePacket(type=0xB9)
        return self._sendPacket(pkt)

    def spreadCode(self, length=None):
        """Get or Set spread code length."""
        data = bytearray()
        if length is not None:
            data = length.to_bytes(1, 'big')
        pkt = makePacket(type=0x95, payload=data)
        return self._sendPacket(pkt)

    def filterRaw(self, stage=None, level=None):
        """Get or Set gain of RX board."""
        data = bytearray()
        if stage is not None and level is not None:
            data += stage.to_bytes(1, 'big')
            # data += level.to_bytes(1, 'big')
            data += bytearray.fromhex(level)
        pkt = makePacket(type=0x96, payload=data)
        return self._sendPacket(pkt)

    def syncLen(self, length=None):
        """Get or Set length of sync."""
        data = bytearray()
        if length is not None:
            data += length.to_bytes(1, 'big')
        pkt = makePacket(type=0x96, payload=data)
        return self._sendPacket(pkt)

    def startBootloader(self):
        """Restart uC and load bootloader."""
        pkt = makePacket(type=0x86)
        return self._sendPacket(pkt)

    def agc(self, status=None):
        """Get AGC status, and turn on or off."""
        data = bytearray()
        if status is not None:
            data += status.to_bytes(1, 'big')
        pkt = makePacket(type=0x98, payload=data)
        return self._sendPacket(pkt)

    def sniffingMode(self, status=None):
        """Get/set status of sniffing mode."""
        data = bytearray()
        if status is not None:
            data += status.to_bytes(1,'big')
        pkt = makePacket(type=0xA1, payload=data)
        return self._sendPacket(pkt)

    def rxGain(self, stage=None, level=None):
        """Get or Set gain level of RX board."""
        data = bytearray()
        if stage is not None and level is not None:
            data += stage.to_bytes(1, 'big')
            # data += level.to_bytes(1, 'big')
            data += level.to_bytes(1, 'big')
        pkt = makePacket(type=0x99, payload=data)
        return self._sendPacket(pkt)

    def peakWinLen(self, winlen=None):
        """Get or Set window length for peak detection."""
        data = bytearray()
        if winlen is not None:
            data += winlen.to_bytes(2, 'big')
        pkt = makePacket(type=0x9B, payload=data)
        return self._sendPacket(pkt)
      
    def transducer(self, t=None):
        """Get or Set transducer type."""
        data = bytearray()
        if t is not None:
            data += t.to_bytes(1, 'big')
        pkt = makePacket(type=0x9C, payload=data)
        return self._sendPacket(pkt)

    def id(self, id=None):
        """Get or Set id of the modem."""
        data = bytearray()
        if id is not None:
            data = id.to_bytes(1, 'big')
        pkt = makePacket(type=0x84, payload=data)
        return self._sendPacket(pkt)

    def testFreq(self, freqIdx=None, freqLvl=0):
        """Test freq."""
        data = bytearray()
        if freqIdx is not None:
            data  = freqIdx.to_bytes(1, 'big')
            data += freqLvl.to_bytes(1, 'big')
        pkt = makePacket(type=0xB1, payload=data)
        return self._sendPacket(pkt)

    def testSweep(self, gc=False, gap=0):
        """Test sweep."""
        data = bytearray()
        data += gc.to_bytes(1, 'big')
        data += gap.to_bytes(1, 'big')
        pkt = makePacket(type=0xB2, payload=data)
        return self._sendPacket(pkt)

    def testNoise(self, gc=False, step=1, dur=1):
        """Test noise."""
        data = bytearray()
        if step < 1 or dur < 1 :
            return -1
        data += gc.to_bytes(1, 'big')
        data += step.to_bytes(1, 'big')
        data += dur.to_bytes(1, 'big')
        pkt = makePacket(type=0xB3, payload=data)
        return self._sendPacket(pkt)

    def txGain(self, value=None):
        """Get or Set TX gain."""
        data = bytearray()
        if value is not None:
            data += value.to_bytes(1, 'big')
        pkt = makePacket(type=0x9A, payload=data)
        return self._sendPacket(pkt)

    def reset(self):
        """Reset the MCU of the modem."""
        pkt = makePacket(type=0x87)
        return self._sendPacket(pkt)

    def sample(self, trigger=None, num=None, post=None):
        """Get samples of oscilloscope."""
        if trigger is None or num is None or post is None:
            return -1
        data = trigger.to_bytes(1, 'big')
        data += num.to_bytes(2, 'big')
        data += post.to_bytes(2, 'big')
        pkt = makePacket(type=0xA0, payload=data)
        return self._sendPacket(pkt)

    def logOn(self, file_name=None):
        """Turn logging to file on."""
        if self.logFile is not None:
            if not self.logFile.closed:
                self.logOff()
            
        try:
            self.logFile = open(file_name, 'w', buffering=1)
        except OSError as e:
            print("Failed to open {}: {}".format(file_name, str(e)))

    def logOff(self):
        """Turn logging to file off."""
        if self.logFile is not None:
            if not self.logFile.closed:
                self.logFile.flush()
                print("Closed logfile {}".format(self.logFile.name))
                self.logFile.close()
