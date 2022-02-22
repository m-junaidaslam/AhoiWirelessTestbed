'''
Created on May 25, 2019

@author: junai
'''
#!/usr/bin/env python

import string
import random
import json
from datetime import datetime
from AhoiNode import NodeModem
from common.packet import byteArrayToPacket, byteArray2HexString, printRxRaw
from common import AhoiMqttClient
from common import CtrlCHandler
import configparser
 
BROKER_ADDRESS = "192.168.57.100"   # IP of the device on which MQTT broker is running
KEY_BKR_ADDR = "brokerAddress"
KEY_INIT_SECTION = "INIT"

TOP_CMND = "cmnd"
TOP_RESP = "resp"

TOP_ALIVE = "alive"
TOP_MODEM = "modem"

mqttClient = None   # MQTT client of Node to connect with MQTT broker
nodeModem = None    # Modem connected with Node
ctrlCHandler = None

# alivePending = 2: Modem info to be sent to control center, query modem for current id
# alivePending = 1: Received current modem id from modem,
#                     waiting for modem version to send both id and version as info message to Control Center
# alivePending = 0: Sending of modem info to Control Center is not required
alivePending = 0


def main():
    """Main function to start node application."""
    brokerAddress = readInitConfig(KEY_INIT_SECTION, KEY_BKR_ADDR)
    if brokerAddress is None:
        brokerAddress = BROKER_ADDRESS
        print("Broker address is None")
    print("BrokerAddress = ", brokerAddress)
    startNode(brokerAddress);

def readInitConfig(section, option):
    """Read particular initial configuration from "config.ini" file"""
    iniConf = configparser.ConfigParser()
    iniConf.read('config.ini')
    if iniConf.has_option(section, option):
        return str(iniConf[section][option])
    else:
        return None

def startNode(brokerAddress):
    """Start connection with MQTT broker and modem."""
    global mqttClient
    global ctrlCHandler
    
    ctrlCHandler = CtrlCHandler.CtrlCHandler(handleCtrlC)
    
    # Initialize MQTT Node client
    mqttClient = AhoiMqttClient.AhoiMqttClient(getCpuSerial(), brokerAddress)
    mqttClient.setOnConnectMethod(onMqttConnect)
    mqttClient.setOnDisconnectMethod(onMqttDisconnect)
    mqttClient.setOnMessageMethod(onMqttMessage)
    
    # Connect modem before starting mqttClient forever loop
    connectModem() 
    
    # This loop is meant to run until program runs and client tries to reconnect when disconnected
    mqttClient.loop_forever()   
    
def handleCtrlC(signal, frame):
    """Handle SIGINT (Ctrl+C)."""
    global ctrlCHandler, mqttClient, nodeModem
    
    if ctrlCHandler.sigIntEn:
        print('Received SIGINT, closing Node application.')
        nodeModem.close()
        mqttClient.disconnect()
        exit()
    else:
        ctrlCHandler.gIrq = True

    
def connectModem(serialDevice=""):
    """Start serial connection of node with modem using serial port"""
    serPort = None
    global nodeModem
    if serialDevice:
        serPort = serialDevice
    else:
        # If serial port is not provided, connect to first available port
        comPorts = NodeModem.getComPorts()
        if(len(comPorts) > 0):
            serPort = comPorts[0]
            
    if serPort:
        print("connectModem: Serial Port:" + serPort)
        nodeModem = NodeModem.NodeModem(serPort)
        if nodeModem.isSerialConOpen():
            # Add callback method to be called when packet received from modem
            nodeModem.addRxCallback(onModemMsgReceived) 
            nodeModem.logOn("log_packets_" + str(datetime.now().strftime("%Y%m%d")))
    else:
        print("No serial Port found")

def onMqttConnect(client, userdata, flags, rc):
    """Method to be called when Node MQTT client is connected with MQTT broker."""
    print("Connected with result code: " + str(rc))
    global mqttClient, nodeModem, alivePending
    alivePending = 2
    mqttClient.subMsg(TOP_CMND + "/" + mqttClient.clientId + "/+")
    # Query modem's info as soon as MQTT broker is connected
    nodeModem.queryModemInfo()


def onMqttDisconnect(client, userdata, rc):
    """Method to be called when Node MQTT client is disconnected with MQTT broker."""
    print("Mqtt client disconnected")

def onMqttMessage(client, userdata, msg):
    """Method to be called when Node MQTT client receives message from MQTT broker on any subscribed topic."""
    print("onMqttMessage: topic: {}, payload: {}".format(msg.topic, str(msg.payload)))
    
    global mqttClient
    global nodeModem
    print(byteArray2HexString(msg.payload))
    
    if TOP_MODEM in msg.topic:  # If the received message is to be forwarded to modem as byte array
        print("Mqtt Modem command: ")
        pkt = byteArrayToPacket(msg.payload)    # Convert received byte array payload to modem packet
        
#         printPacket(pkt)
        print("Modem connected: {}".format(nodeModem.isSerialConOpen()))
        
        nodeModem.send(pkt) # Send received packet to Node Modem
        
    if TOP_ALIVE in msg.topic:  # If the received message is query to publish Node Alive message
        global alivePending
        alivePending = 2
        print("Mqtt alive command: Alive pending = " + str(alivePending))
        nodeModem.queryModemInfo()  # Query modem to send latest info
        
def onModemMsgReceived(pkt):
    """Method to be called when Node receives message from modem."""
    print("ModemMsgReceived:")
    printRxRaw(pkt)
#     printPacket(pkt)
    #     print("ModemMsgReceived: " + printPacket(pkt))
    global mqttClient
    global nodeModem
    global alivePending
    isInfoPkt = nodeModem.updateModemInfo(pkt)  # Update modem info if packet contains info
    print("Alive pending = " + str(alivePending)) 
    
    print("isInfoPkt: " + str(isInfoPkt))
    
    if alivePending == 0:
        pubTopic = TOP_RESP + "/" + mqttClient.clientId + "/" + TOP_MODEM
        mqttClient.pubPacket(pubTopic, pkt) # Publish received packet from modem to MQTT broker
        
    elif alivePending == 1 and isInfoPkt:
        print("Publish alive message")
        pubTopic = TOP_RESP + "/" + mqttClient.clientId + "/" + TOP_ALIVE
        mqttClient.pubMsg(pubTopic, json.dumps(nodeModem.getModemInfo()))
        alivePending -= 1
        
    elif isInfoPkt:
        alivePending -= 1
        

def getCpuSerial():
    """Extract serial from cpuinfo file or generate random serial if not found in cupinfo file."""
    SERIAL_SIZE = 16
    cpuSerial = ""
    try:
        f = open('/proc/cpuinfo','r')
        for line in f:
            if line[0:6]=='Serial':
                cpuSerial = line[10:26]
        f.close()
    except:
        cpuSerial.join(random.sample(string.ascii_uppercase + string.digits, k=SERIAL_SIZE))   
    print("Cpu Serial: " + cpuSerial)
    return cpuSerial


if __name__ == '__main__':
    main()