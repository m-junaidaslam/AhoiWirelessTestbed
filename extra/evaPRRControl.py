#! /usr/bin/env python3
"""A."""
import time
import configparser
import re
import os
from packet import getBytes, printPacket
from serial.tools.list_ports import comports
import time
import sys
import string
import re

# from packet import getBytes
from packet import getHeaderBytes
from packet import getFooterBytes


class evaPRRControl():

    def __init__(self, txmodem, rxmodems):
        print("")
        self.received_pkt_count = 0
        self.i = 0
        # self.txModem = txmodem
        self.txModems = txmodem
        self.rxmodems = rxmodems
        self.file = []
        self.prr_count = []
        self.rxForward = None
        self.testConfig = configparser.ConfigParser()
        self.testConfig.read('config.ini')

        self.testAgc = self.testConfig['PARAMETERS'].getboolean('testAgc')
        self.pktCount = self.testConfig['PARAMETERS'].getint('pktCount')
        self.pktType = int(self.testConfig['PARAMETERS']['pktType'], 16)
        self.sleepTime = self.testConfig['PARAMETERS'].getfloat('sleepTime')
        self.payloadLen = list(map(int, self.testConfig['PARAMETERS']['payloadLength']
                                   .split(',')))
        # filterS0   = testConfig['PARAMETERS']['filterS0'].split(',')
        self.rxGain = list(map(int, self.testConfig['PARAMETERS']['rxGain'].split(',')))
        self.txGain = list(map(int, self.testConfig['PARAMETERS']['txGain'].split(',')))
        self.spreadLen = list(map(int, self.testConfig['PARAMETERS']['spreadLength'].split(',')))

    def setRxForward(self, rxF):
        self.rxForward = rxF

    def byteArray2HexString(self, byteArray):
        return "".join("%02X " % b for b in byteArray)

    def rxCallBack(self, rxNode, pkt):
        print("I am a call back *********************************************************************************")
        print("rx call back with id: " + rxNode.name)
        for rxModem in self.rxmodems:
            if rxNode.nodeId == rxModem.nodeId:
                print("packet received: " + rxNode.name)
                printPacket(pkt)

    #                 self.rxForward(rxNode.nodeId, evaPRRControl.byteArray2HexString(getBytes(pkt)))

    def transmit_packet(self, modem, count, payload, sleepTime, pktType):
        data = bytes(os.urandom(payload))
        modem.send(src=0x00, dst=0xFF, payload=data, status=0, dsn=(count % 256), type=pktType)
        time.sleep(sleepTime)
        print("TX DONE!")

    def logging_reset_modems(self, modem, role, pktcount, payload, rxg, txGain, spread):
        logpath = os.path.join(os.path.dirname(__file__), "data", "logs", "prr")
        filename = ""
        # filename += "id{:03d}_".format(src)
        filename += "{}_".format(role)
        filename += "pkt-{:04d}_".format(pktcount)
        filename += "pay-{:03d}_".format(payload)
        if rxg is None:
            filename += "rxg-ac_"
        else:
            filename += "rxg-{:02d}_".format(rxg)
        filename += "txg-{:02d}_".format(txGain)
        filename += "fs-{:1d}".format(spread)
        current_time = time.strftime("%Y%m%d-%H%M%S")
        # filename += ".{}".format(current_time)
        filename += ".log"

        # FIXME wait time in modem calls

        # set up modem
        modem.logOn(logpath, filename)
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
        time.sleep(1)
        modem.logOff()

    def sent_pkt_count(self):
        # pktCount = testConfig['PARAMETERS'].getint('pktCount')
        no_of_pkt_sent = evaPRRControl.main.pktCount
        return no_of_pkt_sent

    """def received_pkt_count(self, file_name):
        with open(file_name) as f:
            for line in f.readlines():
                if 'FF' in line:
                    no_of_pkt_received = no_of_pkt_received + 1
        return no_of_pkt_received"""

    def received_pkt_count(self, file_name, modem_name):
        no_of_pkt_received = 0
        path = os.path.join(os.path.dirname(__file__), "data", "logs", "prr", file_name)
        f = open(path, 'r')
        for line in f:
            if 'FF' in line:
                no_of_pkt_received = no_of_pkt_received + 1
        return (print("packet_count" + modem_name + no_of_pkt_received))

    def packet_transmission_reception(self):
        """Main."""

        # dev = evaPRRControl.askForComPort()
        # myModem = modem.Modem(dev)
        # myModem = modem.Modem()
        #         self.rxmodems.addRxCallback(evaPRRControl.rxCallBack)

        for modem in self.rxmodems:
            modem.addRxCallback(self.rxCallBack)

        test_start_time = time.time()
        testIdx = 0
        # for rxmodem in self.rxmodems:
        for tx_modem in self.txModems:
            for sp in self.spreadLen:
                for pl in self.payloadLen:
                    for tx in self.txGain:
                        if self.testAgc:
                            self.logging_reset_modems(modem=tx_modem, role=tx_modem.nodeId,
                                                      pktcount=self.pktCount, payload=pl, rxg=None,
                                                      txGain=tx, spread=sp)

                            for rxModem in self.rxmodems:
                                self.logging_reset_modems(modem=rxModem, role=rxModem.nodeId,
                                                          pktcount=self.pktCount, payload=pl, rxg=None,
                                                          txGain=tx, spread=sp)

                            for i in range(0, self.pktCount):
                                self.transmit_packet(modem=tx_modem, count=i, payload=pl,
                                                     sleepTime=self.sleepTime, pktType=self.pktType)
                                time.sleep(self.sleepTime)

                            self.modem_status_logoff(tx_modem)
                            for rxModem in self.rxmodems:
                                self.modem_status_logoff(rxModem)

                            testIdx = testIdx + 1
                        for rxg in self.rxGain:
                            if rxg >= 0:
                                self.logging_reset_modems(modem=tx_modem, role=tx_modem.nodeId,
                                                          pktcount=self.pktCount, payload=pl, rxg=None,
                                                          txGain=tx, spread=sp)
                                for rxModem in self.rxmodems:
                                    self.file.append(self.logging_reset_modems(modem=rxModem, role=rxModem.nodeId,
                                                                               pktcount=self.pktCount, payload=pl,
                                                                               rxg=None,
                                                                               txGain=tx, spread=sp))
                                    """evaPRRControl.logging_reset_modems(modem=rxModem, role='rx',
                                                                   pktcount=self.pktCount, payload=pl, rxg=None,
                                                                   sleepTime=self.sleepTime, pktType=self.pktType,
                                                                   txGain=tx, spread=sp)"""
                                for i in self.pktCount:
                                    self.transmit_packet(modem=tx_modem, count=i, payload=pl, sleepTime=self.sleepTime,
                                                         pktType=self.pktType)
                                    time.sleep(self.sleepTime)

                                self.modem_status_logoff(tx_modem)
                                for rxModem in self.rxmodems:
                                    self.modem_status_logoff(rxModem)
                                testIdx = testIdx + 1
            length = len(self.file)
            # for rxModem in self.rxmodems:
            for i in range(0, length):
                self.prr_count.append(self.received_pkt_count(self.file[i]), self.rxmodems[i].nodeId)

        test_end_time = time.time()
        execution_time = test_end_time - test_start_time
        print(execution_time)

        return self.file, self.prr_count

"""if __name__ == "__main__":
    myevaPRR = evaPRRControl()
    myevaPRR.packet_transmission_reception()"""
