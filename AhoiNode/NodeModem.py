'''
Created on Jun 5, 2019

@author: junai
'''

from serial.tools.list_ports import comports

from common import modem2
from common.packet import cmdTypeList

class NodeModem(modem2.Modem2):
    """Child class of Modem2 with additional modem info functionality"""
    
    KEY_SERIAL_PORTS = "serialports"
    KEY_SELECTED_PORT = "selectedport"
    KEY_MODEM_CONNECTED = "modemconnected"
    KEY_MODEM_ID = "modemid"
    KEY_MODEM_VERSION = "modemversion"
    
    def __init__(self, serialDevice=""):
        super().__init__(serialDevice)  # Initialize parent class
        self.serPort = serialDevice
        self.modId = None
        self.modVersion = None
        self.modConnected = False
        
    def updateModemInfo(self, pkt):
        """Update modem "id" and "version" using packet"""
        print("updateModemInfo: pkt:")
#         printPacket(pkt)
        isAlivePacket = False
        if(pkt.header.type == cmdTypeList["id"]):
#             self.modId = pkt.payload.decode('ascii', 'ignore')
            self.modId = str(int.from_bytes(pkt.payload, byteorder='big'))
            self.modConnected = True
            isAlivePacket = True
             
        if(pkt.header.type == cmdTypeList["version"]):
            self.modVersion = pkt.payload.decode('ascii', 'ignore')
            isAlivePacket = True
            
        return isAlivePacket
         
    def queryModemInfo(self):
        """Query modem "id" and "version" from modem"""
        self.id()
#         time.sleep(1)
        self.getVersion()
#         time.sleep(1)
        
    def getModemInfo(self):
        """Returns modem serial port, connection status, id and version in a dictionary object "infoMsg"."""
        infoMsg = {}
        if self.serPort is not None:
            infoMsg[self.KEY_SELECTED_PORT] = self.serPort
        
        if self.modConnected is not None:
            infoMsg[self.KEY_MODEM_CONNECTED] = self.modConnected
            
        if self.modId is not None:
            infoMsg[self.KEY_MODEM_ID] = self.modId
        
        if self.modVersion is not None:
            infoMsg[self.KEY_MODEM_VERSION] = self.modVersion
            
        print("Get Modem Info: ".format(infoMsg))
        
        return infoMsg
    
    
    def send(self, pkt):
        """Send a packet using modem."""
        return self._sendPacket(pkt)
    
    def setModemInfo(self, infoMsg):
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
            
        print("Node set modem info: {}".format(infoMsg))
        
def getComPorts():
    """Returns array of available serial ports on node"""
    ports = []
    for n, (port, desc, hwid) in enumerate(sorted(comports()), 1):
#         availablePorts = availablePorts +"{:2}: {:20} \n".format(n, port)
        ports.append(port)
    return ports    