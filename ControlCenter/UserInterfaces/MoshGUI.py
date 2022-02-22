#!/usr/bin/env python
import tkinter as tk
import time
import re
from common.packet import getRxRaw

class MoshGUI(tk.Toplevel):
    
    def __init__(self, mosh, controlModem, closeCallBackFun):
        super().__init__()
        self.mosh = mosh
        self.nodeId = controlModem.nodeId
        self.nodeName = controlModem.name
        
        self.closeCallBackFun = closeCallBackFun
        
        self.title("Modem Shell: " + self.nodeName + " (" + self.nodeId + ")")
        
        consoleFrame = tk.Frame(self)
        
        scrollY = tk.Scrollbar(master=consoleFrame)
        scrollY.pack(side=tk.RIGHT, fill=tk.Y, expand=False)
        
        scrollX = tk.Scrollbar(master=consoleFrame, orient=tk.HORIZONTAL)
        scrollX.pack(side=tk.BOTTOM, fill=tk.X, expand=False)
        
        self.console = tk.Text(master=consoleFrame, wrap=tk.NONE, yscrollcommand=scrollY.set, xscrollcommand=scrollX.set)
        self.console.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.insertConsoleText(self.nodeName + " shell started")
        scrollY.config(command=self.console.yview)
        scrollX.config(command=self.console.xview)

        self.console.bind("<FocusIn>", lambda event: self.consoleClicked(event))
        
        cmdFrame = tk.Frame(self)
        
        self.cmdLabel = tk.Label(master=cmdFrame, text=self.getCurrStStr()+"<<")
        self.cmdLabel.pack(side=tk.LEFT, anchor=tk.N)
                
        self.cmdEntry = tk.Entry(master=cmdFrame)
        self.cmdEntry.pack(anchor=tk.S, fill=tk.X)
        self.cmdEntry.bind("<KeyRelease-Return>", lambda event: self.cmdEntered(event))
        self.cmdEntry.focus()
        
        consoleFrame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        cmdFrame.pack(side=tk.BOTTOM, fill=tk.X, expand=False)
        
        self.mosh.start(controlModem)
        self.mosh.setRxForward(self.respReceived)
        
        self.bind("<Destroy>", self._destroy)
        
        
        
    def _destroy(self, event):
        if event.widget is self:
            print("Mosh window closed: " + self.nodeName)
            self.mosh.stop()
            self.closeCallBackFun()
        
        
    def insertConsoleText(self, cmdText):
        self.console.insert(tk.END, cmdText + "\n")
        self.console.see(tk.END)
        
    def clearConsole(self):
        self.console.delete("1.0", "end")
        self.insertConsoleText(self.nodeName + " shell started")
        
    def consoleClicked(self, event):
        self.cmdEntry.focus()
    
    def cmdEntered(self, event):
        self.insertConsoleText(self.getCurrStStr() + "<<" + self.cmdEntry.get())
        inp = self.cmdEntry.get()
        self.cmdEntry.delete(0, tk.END)
        self.processInp(inp)
        
        
    def processInp(self, inp):
        # split input into command and params
        inp = inp.strip()  # strip leading/trailing spaces
        inp = re.sub("\s{2,}", " ", inp)  # remove multiple spaces (make one)
        inp = inp.split(' ', 1)
        cmd = inp[0]
        
        if (len(cmd) > 0 and cmd[0] != '#'):
            if cmd == 'exit' or cmd == 'quit':
                # rxThread.join()
                self.destroy()
    
            elif cmd == 'help':
                if len(inp) == 1:
                    self.insertConsoleText("Available commands:")
#                     print("\nAvailable commands:\n")
                    for c in sorted(self.mosh.cmdList):
                        self.insertConsoleText(c)
#                         print("  " + c)
                elif len(inp) == 2:
                    self.printUsage(inp[1])
                else:
                    self.insertConsoleText("ERROR: invalid call of \"help\"")
#                     print("\nERROR: invalid call of \"help\"")
    
            elif cmd == 'logon':
                if len(inp) > 1:
                    self.insertConsoleText("Logged on file: " + inp[1])
#                     print(inp)
                    self.mosh.doLogOpen(inp)
                else:
                    self.insertConsoleText("Error: filename not given")
    
            elif cmd == 'logoff':
                self.mosh.doLogClose()
                self.insertConsoleText("Logged off")
    
            elif cmd == 'run':
                self.mosh.doRun(inp)
    
            elif cmd == 'pause':
                self.mosh.doPause(inp)
    
            elif cmd == 'waitkey':
                self.mosh.doWaitKey(inp)
            
            elif cmd == 'clear' or cmd == 'clc' or cmd == 'clean':
                self.clearConsole()
    
            else:
                if cmd in self.mosh.cmdList:
                    try:
                        ret = self.mosh.evalCmd(cmd, inp)
#                         ret = eval("self." + self.mosh.cmdList[cmd]['func'])(inp)
                    except ValueError:
                        # not the best error handling but better than what we had before
                        # (at least no crash)
                        self.insertConsoleText("ERROR: Could not parse one of the parameters")
#                         print("ERROR: Could not parse one of the parameters")
    
                    if ret != 0:
                        self.insertConsoleText("ERROR: improper parameter list!")
#                         print("ERROR: improper parameter list!")
                        self.printUsage(inp[0])
    
                    
                    # HACK sleep shortly to show rx
                    # after rx without new prompt
                    time.sleep(0.01)
                else:
                    self.insertConsoleText("ERROR: unknown command ")
#                     print("ERROR: unknown command ")
        
    
    def printUsage(self, cmd):
        """Print usage of mosh."""
        useStr = None
        if cmd in self.mosh.cmdList:
            useStr = "USAGE: %s %s" % (cmd, self.mosh.cmdList[cmd]['param'])
            self.insertConsoleText(useStr)
#             print(useStr)
        else:
            useStr = "ERROR: no help available for unknown command"
            self.insertConsoleText(useStr)
#             print(useStr)
    
    def respReceived(self, nodeId, rxPkt):
        if nodeId == self.nodeId:
#             self.insertConsoleText(self.getCurrStStr() + ">>" + byteArray2HexString(getBytes(rxPkt)))
            consoleText = self.getCurrStStr() + ">>" + getRxRaw(rxPkt)
            consoleText = '\n'.join(consoleText[i:i+150] for i in range(0,len(consoleText), 150))
            self.insertConsoleText(consoleText)
            self.printPktConsole(rxPkt)
            
    
    def getCurrStStr(self):
        return self.nodeName + "@" + time.strftime("%H:%M:%S")
    
    def printPktConsole(self, pkt):
        self.insertConsoleText("src: ", pkt.header.src, " => dst:", pkt.header.dst)
#         print("src: ", pkt.header.src, " => dst:", pkt.header.dst)
        
        self.insertConsoleText("\ntype: ", hex(pkt.header.type), "seq: ", pkt.header.dsn)
#         print("type: ", hex(pkt.header.type), "seq: ", pkt.header.dsn)

        self.insertConsoleText("\nstatus: {:08b}".format(pkt.header.status))
#         print("status: {:08b}".format(pkt.header.status))

        self.insertConsoleText("\n  ack: ", (pkt.header.status & 0x01))
#         print("  ack: ", (pkt.header.status & 0x01))

        self.insertConsoleText("\n  rangeack: ", (pkt.header.status & 0x02))
#         print("  rangeack: ", (pkt.header.status & 0x02))

        self.insertConsoleText("\npayload: ", pkt.payload)
#         print("payload: ", pkt.payload)
