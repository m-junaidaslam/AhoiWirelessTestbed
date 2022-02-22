'''
Created on Jun 12, 2019

@author: junai
'''

from ControlCenter.Node import ControlModem
import pickle
import os

class NodesManager:
    '''
    Manage all the nodes connected to the control center.
    '''
    
     
    TOP_CMND = "cmnd"
    TOP_RESP = "resp"
    
    KEY_MODEM_NAME = "modemname"
    KEY_SELECTED_PORT = "selectedport"
    KEY_MODEM_ID = "modemid"
    KEY_MODEM_VERSION = "modemversion"
    KEY_MODEM_CONNECTED = "modemconnected"
    
#     KEY_NAME_SERIAL = "modemnameserial"
    
#     modemNameSerial = 1 # To assign incremental names to added modems if name not provided

    def __init__(self, mqttClient, rootPath):
        '''
        Constructor
        '''
        self.dataFileDir = os.path.join(rootPath, "data")
        self.dataFile = os.path.join(self.dataFileDir, "nodes.pkl")
        
        if not os.path.exists(self.dataFileDir):
            os.makedirs(self.dataFileDir)
        
        self.nodes = []
        self.mqttClient = mqttClient
        self.loadNodesFromFile()
        self.refreshCallBack = None
        
    def setNodeUpdateCb(self, funNodeUpdateCb):
        """Callback when a node has updated its status"""
        self.nodeUpdateCb = funNodeUpdateCb
        
    def updateNode(self, currNode):
        """Update node values when update from node is received"""
        self.dumpNodesToFile()
        if self.nodeUpdateCb is not None:
            self.nodeUpdateCb(currNode)
        
    def close(self):
        '''Save all the current nodes and their values before deleting object.'''
        self.dumpNodesToFile()
        
        
    def getNodeById(self, nodeId):
        """ Get node by its id as input."""
#         print(self.nodes)
        resNode = None
        if self.nodes:
            for n in self.nodes:
                if n.nodeId == nodeId:
                    resNode = n
                
        return resNode
    
    def getNodesByIds(self, nodeIds):
        """ Get multiple nodes by their id array as input."""
        resNodes = []
        for inpId in nodeIds:
            for n in self.nodes:
                if n.nodeId == inpId:
                    resNodes.append(n)
                    
        return resNodes
        
    def handleMqttMsg(self, msg):
        '''Forward received msg to respective nodes.'''
#         print("Handle Mqtt Msg")
        msgTopic = msg.topic.split('/')
        rxNodeId = msgTopic[1]
        rxMsgType = msgTopic[2]
        
        rxNode = self.getNodeById(rxNodeId)
        if rxNode is not None:
            rxNode._receivePacket(rxMsgType, msg.payload)
            
        if rxMsgType == rxNode.TOP_ALIVE:
            self.dumpNodesToFile()
    
    def publishMqttPkt(self, topic, pkt=None):
        '''To be used by nodes, nodes can use it to send packets over MQTT to
        their respective nodes.'''
         
        cmndTopic = self.TOP_CMND + "/" + topic
        if pkt is not None:
#             print("NodesManager: publishMqttPkt")
#             print(str(pkt))
            self.mqttClient.pubMsg(cmndTopic, pkt)
        else:
            self.mqttClient.pubMsg(cmndTopic, "empty")
        
    def __getNodesDict(self):
        '''Get dictionary of saved nodes from file in the directory.'''
        dictNodes = None
        if os.path.isfile(self.dataFile):
            openDf = open(self.dataFile, 'rb')
            dictNodes = pickle.load(openDf)
            openDf.close()
        return dictNodes
    
    def __dumpNodesDict(self, dictNodes):
        '''Save dictionary with current nodes to file in the directory.'''
        openDf = open(self.dataFile, 'wb')
        pickle.dump(dictNodes, openDf)
        openDf.close()
        
    
    def loadNodesFromFile(self):
        '''Get all saved nodes from the file in directory.'''
        dictNodes = self.__getNodesDict()
        if dictNodes is not None:
#             print(dictNodes)

            for key, value in dictNodes.items():
                newNode = self.getNodeById(key)
                newNodeName = value[self.KEY_MODEM_NAME]
                if newNode is None:
                    newNode = ControlModem.ControlModem(key, newNodeName, self.publishMqttPkt, self.updateNode)
                newNode.serPort = value[self.KEY_SELECTED_PORT]
                newNode.modId = value[self.KEY_MODEM_ID]
                newNode.modVersion = value[self.KEY_MODEM_VERSION]
                newNode.modConnected = value[self.KEY_MODEM_CONNECTED]
                self.nodes.append(newNode)
                newNode.refreshStatus()
                
                
    def dumpNodesToFile(self):
        '''Save all nodes to the file in directory.'''
        dictNodes = {}
        for iNode in self.nodes:
            value = {}
            value[self.KEY_MODEM_NAME] = iNode.name
#             print("Dump Node name: " + iNode.name)
            value[self.KEY_SELECTED_PORT] = iNode.serPort
            value[self.KEY_MODEM_ID] = iNode.modId
            value[self.KEY_MODEM_VERSION] = iNode.modVersion
            value[self.KEY_MODEM_CONNECTED] = iNode.modConnected
            dictNodes[iNode.nodeId] = value
        
        self.__dumpNodesDict(dictNodes)
        
        
    def addNode(self, newNodeId, name=None):
        '''
        Add a node modem to available nodes
        '''
        
        self.loadNodesFromFile()
        for iNode in self.nodes:
            if newNodeId == iNode.nodeId:
                print("Node already present with id: " + newNodeId)
                return -1
        
        newNodeName = name
        
        if newNodeName is None:
            alreadyPresent = False
            modNameSerial = 1
            while True:
                newNodeName = "Modem" + str(modNameSerial)
                for iNode in self.nodes:
                    if iNode.name == newNodeName:
                        alreadyPresent = True
                        modNameSerial += 1
                        break
                if alreadyPresent:
                    alreadyPresent = False
                else:
                    break
        elif len(newNodeName) > 10:
            newNodeName = newNodeName[0:10]
        
#         if newNodeName is None:
#             newNodeName = "Modem" + str(self.modemNameSerial)
#             self.modemNameSerial += 1
        
        self.nodes.append(ControlModem.ControlModem(newNodeId, newNodeName, self.publishMqttPkt, self.updateNode))
        self.dumpNodesToFile()
        self.loadNodesFromFile()
        self.getNodeById(newNodeId).refreshStatus()
        return 0
        
    def removeNode(self, nodeModem):
        '''
        Remove a node from available nodes
        '''
        rmNode = None
        for iNode in self.nodes:
            if nodeModem.nodeId == iNode.nodeId:
                rmNode = iNode
        
        if rmNode is not None:
            self.nodes.remove(rmNode)
            self.dumpNodesToFile()
            self.loadNodesFromFile()
        else:
            print("Node to be removed not found")