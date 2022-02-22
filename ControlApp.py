'''
Created on May 25, 2019

@author: junai
'''
#!/usr/bin/env python

import string
import random
import threading
import os
from ControlCenter.Node import NodesManager
from common import AhoiMqttClient
from common import CtrlCHandler
from ControlCenter.UserInterfaces import NodesListFrame
from ControlCenter.UserInterfaces import ExperimentsListFrame
import tkinter
from ControlCenter.Evaluation import ExperimentsHandler
import configparser
from ControlCenter.UserInterfaces.Mousewheel_Support import Mousewheel_Support


BROKER_ADDRESS = "192.168.57.100"   # IP of the device on which MQTT broker is running
KEY_BKR_ADDR = "brokerAddress"
KEY_INIT_SECTION = "INIT"

TOP_CMND = "cmnd"
TOP_RESP = "resp"

TOP_ALIVE = "alive"
TOP_MODEM = "modem"

mqttConnected = False
nodesManager = None
ctrlCHandler = None
moshWindow = None

moshGUIThread = None

ROOT_PATH = os.path.dirname(__file__)

# NODE_142 = "00000000a69dbc81"
# NODE_141 = "0000000089006771"

def main():
    """Main function to start Control Center application."""
    global ctrlCHandler
    global mqttConnected
    global mqttClient
    global nodesManager
    
    ctrlCHandler = CtrlCHandler.CtrlCHandler(handleCtrlC)
    
    brokerAddress = readInitConfig(KEY_INIT_SECTION, KEY_BKR_ADDR)
    if brokerAddress is None:
        brokerAddress = BROKER_ADDRESS
    
    print("Waiting for MQTT Connection to: " + brokerAddress)
    
    # Initialize mqtt client in a thread
    mqttClient = AhoiMqttClient.AhoiMqttClient(getRandomClientId(), brokerAddress)
    mqttClient.setOnConnectMethod(onMqttConnect)
    mqttClient.setOnDisconnectMethod(onMqttDisconnect)
    mqttClient.setOnMessageMethod(onMqttMessage)
    startMqttClientThread(mqttClient);
    
    while not mqttConnected:    # Wait until MQTT broker is not connected
        pass
        
    nodesManager = NodesManager.NodesManager(mqttClient, ROOT_PATH)
    
    expHandler = ExperimentsHandler.ExperimentsHandler(ROOT_PATH)    
    
    win = tkinter.Tk()
    w, h = win.winfo_screenwidth(), win.winfo_screenheight()
    win.geometry("%dx%d+0+0" % (w, h))
    win.state('zoomed')
    win.title("Ahoi Modem Testbed")
    win.configure(background='purple')
    win.rowconfigure(0, weight=1)
    win.rowconfigure(1, weight=1)
    win.columnconfigure(0, weight=4)
    win.columnconfigure(1, weight=1)
    mwSupport = Mousewheel_Support(win)
    
    NodesListFrame.NodesListFrame(win, ROOT_PATH, nodesManager, ctrlCHandler, mwSupport).grid(row=0, column=0, rowspan=2, sticky=tkinter.NSEW, padx=1, pady=2)
    ExperimentsListFrame.ExperimentsListFrame(win, ROOT_PATH, expHandler.KEY_PRR_TEST, expHandler, nodesManager, mwSupport).grid(row=0, column=1, sticky=tkinter.NSEW, padx=1, pady=2)
    ExperimentsListFrame.ExperimentsListFrame(win, ROOT_PATH, expHandler.KEY_RNG_TEST, expHandler, nodesManager, mwSupport).grid(row=1, column=1, sticky=tkinter.NSEW, padx=1, pady=2)
    
    win.mainloop()
    
def readInitConfig(section, option):
    iniConf = configparser.ConfigParser()
    iniConf.read(os.path.join("common", "config.ini"))
    if iniConf.has_option(section, option):
        return str(iniConf[section][option])
    else:
        return None
        
def handleCtrlC(signal, frame):
    """Handle SIGINT (Ctrl+C)."""
    global ctrlCHandler, mqttClient, nodesManager, moshWindow, moshGUIThread
    
    if ctrlCHandler.sigIntEn:
        print('Received SIGINT, closing control application.')
        moshWindow.moshEnabled = False
        nodesManager.close()
        mqttClient.disconnect()
        
        exit()
    else:
        ctrlCHandler.gIrq = True
        #sigIntEn = True

def startMqttClientThread(mqttClient):
    """Start MQTT client in a separate thread from main. Main thread is being used to run command line for modem shell for now."""
    lifePublishThread = threading.Thread(target=startMqttClient, name="alive_publisher", args=[mqttClient])
    lifePublishThread.daemon = True
    lifePublishThread.start()

def startMqttClient(mqttClient):
    """Method to run as a thread for Control Center MQTT Client forever loop."""
#     global mqttClient
    mqttClient.loop_forever()

def onMqttConnect(client, userdata, flags, rc):
    """Method to be called when Control Center MQTT client is connected with MQTT broker."""
    print("Connected with result code: " + str(rc))
    global mqttConnected
    global mqttClient
    mqttConnected = True
    mqttClient.subMsg(TOP_RESP + "/+/+")    # Subscribe to response from all nodes


def onMqttDisconnect(client, userdata, rc):
    """Method to be called when Control Center MQTT client is disconnected with MQTT broker."""
    print("Mqtt client disconnected")

def onMqttMessage(client, userdata, msg):
    """Method to be called when Control Center MQTT client receives message from MQTT broker on any subscribed topic."""
#     print("onMqttMessage: topic: {}, payload: {}".format(msg.topic, str(msg.payload)))
#     print("onMqttMessage: topic: " + msg.topic)
    global nodesManager
    nodesManager.handleMqttMsg(msg)

def getRandomClientId():
    """Generate random client id for connection with MQTT broker."""
    SERIAL_SIZE = 16
    cpuSerial = "".join(random.sample(string.ascii_uppercase + string.digits, k=SERIAL_SIZE))
    return cpuSerial


if __name__ == '__main__':
    main()