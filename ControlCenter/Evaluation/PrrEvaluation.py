import time
import os
from ControlCenter.Evaluation import ExperimentsHandler
import random

class PrrEvaluation():
    """Run Packet Reception Rate (PRR) evaluation using the provided test configurations"""
    
    simulation = False

    def __init__(self, txmodem, rxmodems, logPath, expName, expInfo, funProgUpdate=None):
        print("PrrEvaluation Initialized: " + expName)
        self.logPath = os.path.join(logPath, expName, "logs")
        self.txModems = txmodem
        self.rxmodems = rxmodems
        self.currTxModem = None
        self.currRxModems = []
        self.currMaxPkts = 0
        self.prrRun = True
        
        # Function to call when packets are received and processed as output
        self.progUpdate = funProgUpdate
        
        # Dictionary with results of one tx modem: rxPkts = {rxModemId:receivedPacketCount, .........} 
        self.rxPkts = dict()
        self.expName = expName
        
        # Test configurations of experiment
        self.expInfo = expInfo
        self.readExpInfo()
        self.setup()
        
        
    def readExpInfo(self):
        self.testAgc = self.expInfo.basic.testAgc
        self.pktCount = int(self.expInfo.basic.pktCount)
        self.txGain = ExperimentsHandler.strToIntList(self.expInfo.basic.txGain)
        self.rxGain = ExperimentsHandler.strToIntList(self.expInfo.basic.rxGain)
        self.sleepTime = float(self.expInfo.basic.sleepTime)
        self.spreadLen = ExperimentsHandler.strToIntList(self.expInfo.basic.spreadLen)
        self.payloadLen = ExperimentsHandler.strToIntList(self.expInfo.payloadLen)
        self.pktType = int(self.expInfo.pktType)


    def byteArray2HexString(self,byteArray):
        return "".join("%02X " % b for b in byteArray)

    def rxCallBack(self, rxNode, pkt):
#         print("rx call back with id: " + rxNode.name)
        for currRxModem in self.currRxModems:
#             print(rxNode.name + " : " + rxModem.name)
            if rxNode.nodeId == currRxModem.nodeId:
#                 print("Source->Dest: " + str(hex(pkt.header.src)) + "->" + str(hex(pkt.header.dst)) + ", Current Mod Id: " + str(self.currTxModem.modId))
                if hex(self.currTxModem.modId) == hex(pkt.header.src):
#                     print(rxNode.name + "->ControlCenter: " +  byteArray2HexString(getBytes(pkt)))
                    self.rxPkts[rxNode.nodeId] = self.rxPkts[rxNode.nodeId] + 1
                    self.progUpdate(
                        totProg = self.waitCount, 
                        nextPlot = False, 
                        txNode = self.currTxModem, 
                        rxNodes = self.currRxModems, 
                        rxData = self.rxPkts, 
                        maxPkts = self.currMaxPkts
                        )
#                     print(self.rxPkts)

    def transmit_packet(self, modem, count, payload, sleepTime, pktType):
        data = bytes(os.urandom(payload))
        modem.send(src=int(modem.modId), dst=0xFF, payload=data, status=0, dsn=(count % 256), type=pktType)
        self.waitCount += 1
#         print("Wait count: " + str(self.waitCount))
        self.progUpdate(
                totProg = self.waitCount, 
                nextPlot = False, 
                txNode = self.currTxModem, 
                rxNodes = self.currRxModems, 
                rxData = self.rxPkts, 
                maxPkts = self.currMaxPkts
                )
        time.sleep(sleepTime * payload)
#         print("TxModem: " + modem.name + "->")
        if self.simulation:
            self.simRxPkt()
        
    def simRxPkt(self):
        """To simulate PRR Test by sending mock packets"""
        for rxNode in self.currRxModems:
            rnd = random.randint(0,7)
            if rnd >= 2:
                self.rxPkts[rxNode.nodeId] = self.rxPkts[rxNode.nodeId] + 1
                
        self.progUpdate(
            totProg = self.waitCount, 
            nextPlot = False, 
            txNode = self.currTxModem, 
            rxNodes = self.currRxModems, 
            rxData = self.rxPkts, 
            maxPkts = self.currMaxPkts
            )
#         print(self.rxPkts)

    def logging_reset_modems(self, modem, role, pktcount, payload, rxg, txGain, spread):
        filename = ""
        # filename += "id{:03d}_".format(src)
        filename += "{}_".format(modem.nodeId)
        filename += "{}_".format(role)
        filename += "pkt-{:04d}_".format(pktcount)
        filename += "pay-{:03d}_".format(payload)
        if rxg is None:
            filename += "rxg-ac_"
        else:
            filename += "rxg-{:02d}_".format(rxg)
        filename += "txg-{:02d}_".format(txGain)
        filename += "fs-{:1d}".format(spread)

        # FIXME wait time in modem calls

        # set up modem
        
        filename = modem.logOn(self.logPath, filename)
        modem.id()
        modem.getVersion()
        modem.getConfig()
        modem.spreadCode(spread)
        # modem.rangeDelay()
        modem.txGain(txGain)
        if rxg is None:
            modem.agc(1)
            modem.rxGain()
        else:
            modem.agc(0)
            # modem.rxGain(0, s0)
            modem.rxGain(1, rxg)  # HACK
        modem.clearPacketStat()
        modem.clearSyncStat()
        modem.clearSfdStat()
        # more stats
        modem.getPowerLevel()
        modem.rxThresh()
        modem.rxLevel()
        
        return filename


    def modem_status_logoff(self, modem):
        modem.getPacketStat()
        modem.getSyncStat()
        modem.getSfdStat()
        modem.getPowerLevel()

        # finalize
        time.sleep(self.sleepTime)
        modem.logOff()


    def setup(self):
        self.paramWait = self.pktCount * len(self.txGain) * len(self.spreadLen) * len(self.payloadLen)
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
                    
#         print("Max wait: " + str(self.maxWait))
        

    def run(self):
        """Run experiment."""
        test_start_time = time.time()
        testIdx = 0
        
        for tx_modem in self.txModems:
            self.currTxModem = tx_modem
            self.currRxModems = [i for i in self.rxmodems if i.nodeId!=tx_modem.nodeId]
            self.rxPkts = dict()
            
            for modem in self.currRxModems:
                self.rxPkts[modem.nodeId] = 0
                modem.addRxCallback(self.rxCallBack)
                    
            if len(self.currRxModems) > 0:
                self.currMaxPkts = self.paramWait
                self.progUpdate(
                    totProg = self.waitCount, 
                    nextPlot = True, 
                    txNode = tx_modem, 
                    rxNodes = self.currRxModems, 
                    rxData = self.rxPkts, 
                    maxPkts = self.currMaxPkts
                    )
                
                for sp in self.spreadLen:
                    for pl in self.payloadLen:
                        for tx in self.txGain:
                            if self.testAgc:
                                self.logging_reset_modems(modem=tx_modem, role="Tx",
                                    pktcount=self.pktCount, payload=pl, rxg=None,
                                    txGain=tx, spread=sp)
    
                                for rxModem in self.currRxModems:
                                    self.logging_reset_modems(modem=rxModem, role="Rx",
                                                                 pktcount=self.pktCount, payload=pl, rxg=None,
                                                                 txGain=tx, spread=sp)
                                for i in range(0, self.pktCount):
                                    if not self.prrRun:
                                        print("Force Closed!")
                                        return
                                    self.transmit_packet(modem=tx_modem, count=i, payload=pl,
                                                             sleepTime=self.sleepTime, pktType=self.pktType)
#                                     time.sleep(self.sleepTime)
    
                                self.modem_status_logoff(tx_modem)
                                for rxModem in self.currRxModems:
                                    self.modem_status_logoff(rxModem)
    
                                testIdx = testIdx + 1
                            for rxg in self.rxGain:
                                if rxg >= 0:
                                    self.logging_reset_modems(modem=tx_modem, role="Tx",
                                                                 pktcount=self.pktCount, payload=pl, rxg=rxg,
                                                                 txGain=tx, spread=sp)
                                    for rxModem in self.currRxModems:
                                        self.logging_reset_modems(modem=rxModem, role="Rx",
                                                                     pktcount=self.pktCount, payload=pl, rxg=rxg,
                                                                     txGain=tx, spread=sp)
                                    for i in range(0, self.pktCount):
                                        if not self.prrRun:
                                            print("Force Closed!")
                                            return
                                        self.transmit_packet(modem=tx_modem, count=i, payload=pl, sleepTime=self.sleepTime, pktType=self.pktType)
#                                         time.sleep(self.sleepTime)
    
                                    self.modem_status_logoff(tx_modem)
                                    for rxModem in self.currRxModems:
                                        self.modem_status_logoff(rxModem)
                                    testIdx = testIdx + 1
                
            time.sleep(self.sleepTime)
            for rxModem in self.currRxModems:
                rxModem.removeRxCallback(self.rxCallBack)
                                
        test_end_time = time.time()
        execution_time = test_end_time - test_start_time
        print(execution_time)
        print("Wait count: " + str(self.waitCount))
