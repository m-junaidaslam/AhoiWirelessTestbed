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

from common import packet
from common.packet import byteArray2HexString, byteArrayToPacket
import time
from common import modem2
import json
import os


class ControlModem(modem2.Modem2):
    """Child class of Modem2 with additional functionality to communicate with control center MQTT client."""
    
    TOP_ALIVE = "alive"
    TOP_MODEM = "modem"
    
    KEY_SERIAL_PORTS = "serialports"
    KEY_SELECTED_PORT = "selectedport"
    KEY_MODEM_ID = "modemid"
    KEY_MODEM_CONNECTED = "modemconnected"
    KEY_MODEM_VERSION = "modemversion"

    def __init__(self, nodeId, name, pubMethod, funUpdateCb):
        """Initialize modem."""
        super().__init__()
        self.nodeId = nodeId
        self.publish = pubMethod
        self.alive = False
        self.pubTopicAlive = self.nodeId + "/" + self.TOP_ALIVE
        self.pubTopicModem = self.nodeId + "/" + self.TOP_MODEM
        self.name = name
        self.serPort = None
        self.modConnected = False
        self.modId = None
        self.modVersion = None
        self.updateCb = funUpdateCb
#         print("Initialized Control modem: " + self.name)

    def __del__(self):
        """Close all files and connections before termination."""
        self.close()
    
    def _open(self):
        pass
    
    def close(self):
        """Terminate."""
#         print("Closing Modem" + self.name)
        if self.logFile is not None:
            self.logFile.close()

    def _sendPacket(self, pkt):
        """Send a packet to modem using MQTT client via MQTT broker."""
                
#         if pkt.header.dsn is None or pkt.header.dsn > 255:
#             pkt.header.dsn = self.seqNumber
#         
        #merge header and payload to bytearray
        pktbytes = packet.getHeaderBytes(pkt)
        pktbytes += pkt.payload

        #add start, stuffing and end sequence
        tx = bytearray() # start Packet
        for b in pktbytes:
            tx.append(b)
#             if b == 0x10:
#                 tx.append(b) # stuffing
        # end packet

        self.seqNumber += 1
        self.seqNumber = (self.seqNumber % 256)

        output = "TX@"
        output += "{:.3f}".format(time.time())
        output += " "
        output += byteArray2HexString(pktbytes)
        print(output)
        
#         packet.printPacket(pkt)
#         print(tx)
        self.publish(self.pubTopicModem, tx)
        return 0
    
    def logOn(self, logPath, file_name):
#         print("Logon {}, path: {}, file: {}".format(self.name, logPath, file_name))
        nodeLogPath = os.path.join(logPath, self.name + "(" + self.nodeId + ")")
        
        if not os.path.exists(nodeLogPath):
            os.makedirs(nodeLogPath)
        
        nodeLogFile = os.path.join(nodeLogPath, file_name)
        nodeLogFile += "_{}".format(time.strftime("%Y%m%d-%H%M%S"))
        nodeLogFile += ".log"
        super().logOn(file_name=nodeLogFile)
        return nodeLogFile
        
    
    def logEntry(self, pkt):
        if self.logFile is not None and not self.logFile.closed:
            #merge header and payload to bytearray
            pktbytes = packet.getHeaderBytes(pkt)
            pktbytes += pkt.payload
            output = "{:.3f}".format(time.time())
            output += " "
            output += byteArray2HexString(pktbytes)
            self.logFile.write(output + "\n")
            self.logFile.flush()
            os.fsync(self.logFile.fileno())
            return 0
        else:
            return -1
        
    
    def refreshStatus(self):
        self.alive = False
        self.publish(self.pubTopicAlive)
    
    def _receivePacket(self, msgType, msgPayload):
#         print("Control Modem packet received: " + msgType)
        if self.TOP_ALIVE == msgType:   # If the received message is response to publish Node Alive query
#             print("Mqtt alive response control: id: " + self.nodeId)
            modInfoMsg = json.loads(msgPayload)
            self.__setInfo(modInfoMsg)
            for f in self.rxCallbacks:
                f(self, modInfoMsg)
            
        if self.TOP_MODEM == msgType:  # If the received message is response from modem as byte array
#             print("Mqtt response modem: " + msgType)
            pkt = byteArrayToPacket(msgPayload)    # Convert received byte array payload to modem packet
#             print("TOP_MODEM packet: ")
            self.logEntry(pkt)
            for f in self.rxCallbacks:
                f(self, pkt)
                
    
    def __setInfo(self, infoMsg):
        """Updates modem serial port, connection status, id and version in using dictionary argument "infoMsg"."""
        
        serPort = infoMsg[self.KEY_SELECTED_PORT]
        modConnected = infoMsg[self.KEY_MODEM_CONNECTED]
        modId = infoMsg[self.KEY_MODEM_ID]
        modVersion = infoMsg[self.KEY_MODEM_VERSION]
        
        if serPort is not None:
            self.serPort = serPort
        
        if modConnected is not None:
            self.modConnected = modConnected
            
        if modId is not None:
            self.modId = modId
        
        if modVersion is not None:
            self.modVersion = modVersion
            
        self.alive = True
        
        self.updateCb(self)
        
#         print("Alive in set modem: " + str(self.alive))