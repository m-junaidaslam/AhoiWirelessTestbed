#! /usr/bin/env python3
"""A."""
import time
import os
from ControlCenter.Evaluation import ExperimentsHandler
import statistics
from collections import defaultdict
from common.packet import byteArray2HexString
import random
import math


class RangeEvaluation():
    simulation = False
#     logPath=os.path.join(os.path.dirname(os.getcwd()),"data", "range")
   
    PKT_TYPE_POS = 3
    PKT_TYPE_ACK = 0x7f
    PKT_TIME_POS  = 0
    PKT_SRC_POS  = 1
    PKT_SEQ_POS  = 5
    PKT_DIST_POS = 7
    PKT_DIST_LEN = 4
    PKT_STATUS_RANGING = '02'
    soundSpeed = 1426.4
    
    def __init__(self, txModems, rxModems, logPath, expName, expInfo, funProgUpdate):
        print("RangeEvaluation Initialized: " + expName)
        
        self.logPath = os.path.join(logPath, expName, "logs")
        self.txModems = txModems
        self.rxModems = rxModems
        self.currTxModem = None
        self.currRxModems = []
        self.rangeRun = True
        self.dictDist = defaultdict(list)
        self.expInfo = expInfo
        self.expName = expName
        self.progUpdate = funProgUpdate
        self.readExpInfo()
        self.setup()
#         self.distance = dict()
#         self.rxActModIds = []
        
        
        
    def readExpInfo(self):
        self.testAgc = self.expInfo.basic.testAgc
        self.pktCount = int(self.expInfo.basic.pktCount)
        self.txGain = ExperimentsHandler.strToIntList(self.expInfo.basic.txGain)
        self.rxGain = ExperimentsHandler.strToIntList(self.expInfo.basic.rxGain)
        self.sleepTime = float(self.expInfo.basic.sleepTime)
        self.spreadLen = ExperimentsHandler.strToIntList(self.expInfo.basic.spreadLen)
        self.rangeDelay = int(self.expInfo.rangeDelay)
        self.soundSpeed = float(self.expInfo.soundSpeed)
        
    def rxCallBack(self, rxNode, pkt):
#         print("rx call back with modem:{}, pkttype:{}".format(rxNode.name, hex(pkt.header.type)))
        
        if rxNode.nodeId == self.currTxModem.nodeId:
#             print("Node Id matched")
            if hex(pkt.header.type) == hex(self.PKT_TYPE_ACK):
#                 print("Type matched") 
                for srcNode in self.currRxModems:
                    if hex(srcNode.modId) == hex(pkt.header.src):
                        print("Mod Id matched, rxMod:{}, pkt header src:{}".format(srcNode.modId, pkt.header.src))

                        payload = byteArray2HexString(pkt.payload)
                        plWord = payload.split()
                        dist = 0
                        for i in range(0 , self.PKT_DIST_LEN):
                            dist = dist * 256 + int(plWord[i], 16)
                        
                        floatDist = (dist - 34) * 0.000001 * self.soundSpeed
                        strDist = "%.4f" %floatDist
                        floatDist = float(strDist)
                        
                        self.dictDist[srcNode.nodeId].append(floatDist)
                        self.progUpdate(
                            totProg = self.waitCount, 
                            nextPlot = False, 
                            txNode = self.currTxModem, 
                            rxNodes = self.currRxModems, 
                            rxData = self.dictDist, 
                            maxPkts = self.currMaxPkts
                            )
#                         for key, value in self.dictDist.items():
#                             print("key:{}, value{}".format(key, value))
                        
                        print("Distance {}->{}: {}".format(rxNode.name, srcNode.name, strDist))       
        

    def startTest(self, modem, rxg, txg, spread):
        #"""Start a single test."""
        
        # prepare file name
        
        filename = ""
        filename += "{}_".format(modem.nodeId)
        filename += "{}_".format("Tx")
        filename += "pkt-{:04d}_".format(self.pktCount)
        if rxg is None:
            filename += "rxg-ac_"
        else:
            filename += "rxg-{:02d}_".format(rxg)
        filename += "txg-{:02d}_".format(txg)
        filename += "fs-{:1d}".format(spread)
        
        # FIXME wait time in modem calls
    
        self.filename = modem.logOn(self.logPath, filename)
        
        modem.id()
        modem.getVersion()
        modem.getConfig()
        modem.spreadCode(spread)
        modem.rangeDelay()
        modem.txGain(txg)
        
        if rxg is None:
            modem.agc(1)
            modem.rxGain()
        else:
            modem.agc(0)
            #modem.rxGain(0, s0)
            modem.rxGain(1, rxg)  # HACK
            
        modem.clearPacketStat()
        modem.clearSyncStat()
        modem.clearSfdStat()
        # more stats
        modem.getPowerLevel()
        modem.rxThresh()
        modem.rxLevel()
        
        for i in range(0, self.pktCount):
            if not self.rangeRun:
                print("Force Closed!")
                return
            data = bytes(os.urandom(0))
            modem.send(src=0x00, dst=0xFF, payload=data, status=0x02, dsn= (i % 256), type=0x00)
            self.waitCount += 1
            print("Wait count: " + str(self.waitCount))
            self.progUpdate(
                totProg = self.waitCount, 
                nextPlot = False, 
                txNode = self.currTxModem, 
                rxNodes = self.currRxModems, 
                rxData = self.dictDist, 
                maxPkts = self.currMaxPkts
                )
            
            if self.simulation:
                self.simRxPkt()
            time.sleep(self.sleepTime)
#         print("TX DONE!")
        
        # stats
        modem.getPacketStat()
        modem.getSyncStat()
        modem.getSfdStat()
        modem.getPowerLevel()
    
        # finalize
        time.sleep(self.sleepTime)
        modem.logOff()
        
    def simRxPkt(self):
        """To simulate Range Test by sending mock packets"""
        mu = 5
        for rxNode in self.currRxModems:
            variance = 2
            sigma = math.sqrt(variance)
            rnd = random.gauss(mu, sigma)
            self.dictDist[rxNode.nodeId].append(rnd)
            mu +=3
                
        self.progUpdate(
            totProg = self.waitCount, 
            nextPlot = False, 
            txNode = self.currTxModem, 
            rxNodes = self.currRxModems, 
            rxData = self.dictDist, 
            maxPkts = self.currMaxPkts
            )
#         print(self.dictDist)
    
    
    def readDistance(self, nodeModem, fileName):
        node = nodeModem.name + "(" + nodeModem.nodeId + ")"
        name = os.path.join(self.logPath, node, fileName)
        self.distance.update(self.calcDistance(name, nodeModem, self.rxActMods, self.rxActModIds)) 


    def calcDistance(self, fileName, nodeModem=None, rxMods=None, rxModIds=None):        
        f = open(fileName, "r")
        distance = dict()
        for x in f:
            dist=0
            floatDist = 0
            source = None
            words=x.split()
            if (words[3] == self.PKT_TYPE_ACK):
                source = str(int(words[1], 16))
                dist=int(words[self.PKT_DIST_POS], 16)
                for i in range(1 , self.PKT_DIST_LEN):
                    dist = dist * 256 + int(words[self.PKT_DIST_POS + i], 16)
                
                floatDist = (dist - 34) * 0.000001 * self.soundSpeed
                strDist = "%.4f" %floatDist
            
            if source is not None:
                modName = source
                if nodeModem is not None:
                    modName = nodeModem.name
                    
                if rxModIds is not None:
                    if source in rxModIds:
                        rxIndex = rxModIds.index(source)
                        modName = modName + "->" + rxMods[rxIndex].name + "(" + source + ")"
                    
                if modName in distance:
                    distance[modName] = distance[modName] + ", " + strDist
                else:   
                    distance[modName] = strDist
                    
        return distance
     
#     def rxCallBack(self, nodeModem, pkt):
#         for txModem in self.txModems:
#             if nodeModem.nodeId == txModem.nodeId:
                
    def getMeanDistances(self, distance):
        dictMeanS = dict()
        for key in distance:
            strValues = distance[key]
            listValues = ExperimentsHandler.strToFloatList(strValues)
            meanValue = statistics.mean(listValues)
            dictMeanS[key] = meanValue        
        return dictMeanS

    def printDistanceDict(self, inpDict):
        for key in inpDict:
            print(key + ": " + str(inpDict[key]))
            
            
            
    def setup(self):
        self.paramWait = self.pktCount * len(self.txGain) * len(self.spreadLen)
        agcCount = 0
        if self.testAgc:
            agcCount = self.paramWait
        self.paramWait = agcCount + (self.paramWait * len(self.rxGain))
        
        txModId = 0x20
        for tx_modem in self.txModems:
            tx_modem.id(txModId)
            tx_modem.modId = txModId
            txModId += 1

        self.nodeWait = len(self.txModems)          
        self.maxWait = self.paramWait * self.nodeWait
        self.waitCount = 0
                    
        print("Max wait: " + str(self.maxWait))

    def run(self):
#         for txModem in self.txModems:
#             txModem.addRxCallback(self.rxCallBack)
        test_start_time = time.time()
        
        testIdx = 0
        for txModem in self.txModems:
            self.dictDist = defaultdict(list)
            txModem.addRxCallback(self.rxCallBack)
            self.currTxModem = txModem
            self.currRxModems = [i for i in self.rxModems if i.nodeId != txModem.nodeId]
            maxRngDelay = 0
            
            if len(self.currRxModems) > 0:
                self.currMaxPkts = self.paramWait
                self.progUpdate(
                    totProg = self.waitCount, 
                    nextPlot = True, 
                    txNode = txModem, 
                    rxNodes = self.currRxModems, 
                    rxData = self.dictDist, 
                    maxPkts = self.currMaxPkts
                    )
                
                modId = 50
                sleepScalar = 0
                for rxModem in self.currRxModems:
                    maxRngDelay = sleepScalar * self.rangeDelay
                    rxModem.rangeDelay(maxRngDelay)
                    rxModem.id(modId)
                    rxModem.modId = modId
                    sleepScalar += 1
                    modId += 1
                
                for sp in self.spreadLen:
                    for tx in self.txGain:
                        if self.testAgc:
                            if not self.rangeRun:
                                print("Force Closed!")
                                return
                            self.startTest(modem=txModem, rxg=None, txg=tx, spread=sp)
                            testIdx = testIdx + 1
                        for rxg in self.rxGain:
                            if not self.rangeRun:
                                print("Force Closed!")
                                return
                            if rxg >= 0:
                                self.startTest(modem=txModem, rxg=rxg, txg=tx, spread=sp)
                                testIdx = testIdx + 1
            
            time.sleep(maxRngDelay)
            txModem.removeRxCallback(self.rxCallBack)                                       
#             self.readDistance(txModem, self.filename)
            
        test_end_time = time.time()
        execution_time = test_end_time - test_start_time
        print(execution_time)
            
        print("\nDistance")
        self.printDistanceDict(self.dictDist)
        
#         print("\nMean Distance")
#         self.printDistanceDict(self.getMeanDistances(self.distance))    
            
        
