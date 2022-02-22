from tkinter import Toplevel, Frame, Button, ACTIVE, LEFT, IntVar, Listbox, SINGLE

class Dialog(Toplevel):

    def __init__(self, parent, title = None):

        Toplevel.__init__(self, parent)
        self.transient(parent)

        if title:
            self.title(title)

        self.parent = parent

        self.result = None

        body = Frame(self)
        self.initial_focus = self.body(body)
        body.pack(padx=5, pady=5)

        self.buttonbox()

        self.grab_set()

        self.initial_focus = self

        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self.geometry("+%d+%d" % (parent.winfo_rootx()+50,
                                  parent.winfo_rooty()+50))

        if self.initial_focus is not None:
            self.initial_focus.focus_set()

        self.wait_window(self)

    #
    # construction hooks

    def body(self, master):
        # create dialog body.  return widget that should have
        # initial focus.  this method should be overridden

        pass

    def buttonbox(self):
        # add standard button box. override if you don't want the
        # standard buttons

        box = Frame(self)

        w = Button(box, text="OK", width=10, command=self.ok, default=ACTIVE)
        w.pack(side=LEFT, padx=5, pady=5)
        w = Button(box, text="Cancel", width=10, command=self.cancel)
        w.pack(side=LEFT, padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack()

    #
    # standard button semantics

    def ok(self, event=None):

        if not self.validate():
            self.initial_focus.focus_set() # put focus back
            return

        self.withdraw()
        self.update_idletasks()

        self.apply()

        self.cancel()

    def cancel(self, event=None):

        # put focus back to the parent window
        self.parent.focus_set()
        self.destroy()

    #
    # command hooks

    def validate(self):

        return 1 # override

    def apply(self):

        pass # override
    
from tkinter import Label, Entry

class AddNodeDialog(Dialog):
    
    KEY_CLIENT_ID = "clientid"
    KEY_NAME = "name"

    def body(self, master):

        Label(master, text="Client ID:[maximum 16 characters]").grid(row=0)
        Label(master, text="Name:[maximum 10 characters]").grid(row=1)

        self.e1 = Entry(master)
        self.e2 = Entry(master)

        self.e1.grid(row=0, column=1)
        self.e1.insert(0, "00000000")
        self.e1.select_range(0, "end")
        self.e2.grid(row=1, column=1)
        return self.e1 # initial focus

    def apply(self):
        self.result = {}
        clientId = self.e1.get()
        name = self.e2.get()
        self.result[self.KEY_CLIENT_ID] = clientId
        self.result[self.KEY_NAME] = name
        

from tkinter import Checkbutton, Scrollbar, VERTICAL, RIGHT, Canvas, BOTH, Y, NW, W, E
        
class SelTxRxDialog(Dialog):
    
    def __init__(self, parent, title, nodes, mWhSupport):
        self.nodes = nodes
        self.resTxNodes = []
        self.resRxNodes = []
        self.mWhSupport = mWhSupport
        super().__init__(parent, title)
        
 
    def body(self, master):
        yscroll = Scrollbar(self, orient=VERTICAL)
        yscroll.pack(side=RIGHT, fill=Y)
        
        self.canvas = Canvas(master, bg='gray')
        self.canvas.pack(side=RIGHT, fill=BOTH, expand=True)
        self.canvas['yscrollcommand'] = yscroll.set
        
        self.mWhSupport.add_support_to(self.canvas, yscrollbar=yscroll, what="pages")

        yscroll['command'] = self.canvas.yview
        
        self.listFrame = Frame(self.canvas)
        self.listFrameId = self.canvas.create_window((0, 0), window=self.listFrame, anchor=NW) # Canvas equivalent of pack()
        
        self.listFrame.bind("<Configure>", self._onFrameConfigure)
        self.canvas.bind('<Configure>', self._onFrameSize)

        self.lbl1 = Label(self.listFrame, text="Transmitter")
        self.lbl1.grid(row=0, column=1)
        
        self.lbl2 = Label(self.listFrame, text="Receiver")
        self.lbl2.grid(row=0, column=2)
        
        currRow = 1
        self.txVar = dict()
        self.rxVar = dict()
        
        actNodeCount = 0
        for iNode in self.nodes:
#             if iNode.alive:
                nodeId = iNode.nodeId
                Label(self.listFrame, text=iNode.name+"("+nodeId+")", anchor=W).grid(row=currRow, column=0)
                self.txVar[nodeId] = IntVar()
                self.rxVar[nodeId] = IntVar()
                Checkbutton(self.listFrame, text="", variable=self.txVar[nodeId]).grid(row=currRow, column=1)
                Checkbutton(self.listFrame, text="", variable=self.rxVar[nodeId]).grid(row=currRow, column=2)
                currRow += 1
                actNodeCount += 1
        
        if actNodeCount == 0:
            Label(self.listFrame, text="No active modems not found!", anchor=W).grid(row=currRow, column=0)
            self.lbl1.destroy()
            self.lbl2.destroy()
            return self.listFrame
        elif actNodeCount == 1:
            Label(self.listFrame, text="Only one active modem found, running experiment is not possible.", anchor=W).grid(row=currRow, column=0)
            self.lbl1.destroy()
            self.lbl2.destroy()
            return self.listFrame
            
        return self.lbl1 # initial focus
    
    def _onFrameConfigure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
    def _onFrameSize(self, event):
        canvasWidth = event.width
        self.canvas.itemconfig(self.listFrameId, width=canvasWidth)

    def apply(self):
        for key, value in self.txVar.items():
            if value.get() == 1:
                self.resTxNodes.append(key)
                 
        for key, value in self.rxVar.items():
            if value.get() == 1:
                self.resRxNodes.append(key)
        self.canvas.delete("all")
                
#         print(self.resTxNodes)
#         print(self.resRxNodes)

 
class SelExpParams(Dialog):
    def __init__(self, parent, title, expHandler, lastExpName=None, editExp=False):
        self.lastExpName = lastExpName
        self.lastExp = None
        self.name = None
        self.expHandler = expHandler
        self.editExp = editExp
        self.currRow = 0
        super().__init__(parent, title)
        
    def body(self, master):
        
        self.varAgc = IntVar()
        Checkbutton(master, text="Auto Gain Control", variable=self.varAgc).grid(row=self.currRow, column=1, sticky=W, padx=5, pady=5)
        self.currRow += 1
        
        self.varSave = IntVar()
        self.checkSave = Checkbutton(master, text="Save Configuration", variable=self.varSave)
        self.checkSave.grid(row=self.currRow, column=1, sticky=W, padx=5, pady=5)
        self.currRow += 1
        
        self.varOverwrite = IntVar()
        self.varOverwrite.set(0)
        if self.editExp:
            self.checkOverwrite = Checkbutton(master, text="Overwrite "+self.lastExpName , variable=self.varOverwrite)
            self.checkOverwrite.grid(row=self.currRow, column=1, sticky=W, padx=5, pady=5)
            self.currRow += 1
        
        
        Label(master, text="Name [maximum 20 characters]:").grid(row=self.currRow, sticky=E)
        self.eName = Entry(master, width=50)
        self.eName.grid(row=self.currRow, column=1, sticky=W, padx=5, pady=5)
        self.currRow += 1
        
        Label(master, text="Packet Count:").grid(row=self.currRow, sticky=E)
        self.ePktCnt = Entry(master, width=50)
        self.ePktCnt.grid(row=self.currRow, column=1, sticky=W, padx=5, pady=5)
        self.currRow += 1
        
        Label(master, text="Tx Gain (comma separated):").grid(row=self.currRow, sticky=E)
        self.eTxGain = Entry(master, width=50)
        self.eTxGain.grid(row=self.currRow, column=1, sticky=W, padx=5, pady=5)
        self.currRow += 1
        
        Label(master, text="Rx Gain (comma separated):").grid(row=self.currRow, sticky=E)
        self.eRxGain = Entry(master, width=50)
        self.eRxGain.grid(row=self.currRow, column=1, sticky=W, padx=5, pady=5)
        self.currRow += 1
        
        Label(master, text="Sleep Time (seconds):").grid(row=self.currRow, sticky=E)
        self.eSleepTime = Entry(master, width=50)
        self.eSleepTime.grid(row=self.currRow, column=1, sticky=W, padx=5, pady=5)
        self.currRow += 1
        
        Label(master, text="Spread Length (comma separated):").grid(row=self.currRow, sticky=E)
        self.eSpreadLen = Entry(master, width=50)
        self.eSpreadLen.grid(row=self.currRow, column=1, sticky=W, padx=5, pady=5)
        self.currRow += 1
        
        if self.editExp:
            self.varSave.set(1)
            self.varOverwrite.set(1)
            self.checkSave.config(state='disabled', variable=None) 
        
        
        
#         self.eName.insert(0, self.lastExpName)
        if self.lastExp is not None:
            self.varAgc.set(self.lastExp.basic.testAgc)
            self.ePktCnt.insert(0, self.lastExp.basic.pktCount)
            self.eTxGain.insert(0, self.lastExp.basic.txGain)
            self.eRxGain.insert(0, self.lastExp.basic.rxGain)
            self.eSleepTime.insert(0, self.lastExp.basic.sleepTime)
            self.eSpreadLen.insert(0, self.lastExp.basic.spreadLen)
            if self.editExp:
                self.eName.insert(0, self.lastExpName)
                self.eName.select_range(0, "end")
        
        return self.eName
    
    def cancel(self, event=None):
        super().cancel(self)
#         self.result = None
        
    def apply(self):
        pass
    

class SelPrrParams(SelExpParams):
         
    def body(self, master):
        if self.lastExpName is not None:
            self.lastExp = self.expHandler.readExperiment(self.lastExpName, self.expHandler.KEY_PRR_TEST)
        super().body(master)
        
        Label(master, text="Payload Length (comma separated):").grid(row=self.currRow, sticky=E)
        self.ePayloadLen = Entry(master, width=50)
        self.ePayloadLen.grid(row=self.currRow, column=1, sticky=W, padx=5, pady=5)
        self.currRow += 1
        
        
        Label(master, text="Packet Type:").grid(row=self.currRow, sticky=E)
        self.ePktType = Entry(master, width=50)
        self.ePktType.grid(row=self.currRow, column=1, sticky=W, padx=5, pady=5)
        
        if self.lastExp is not None:
            self.ePayloadLen.insert(0, self.lastExp.payloadLen)
            self.ePktType.insert(0, self.lastExp.pktType)
        
    def apply(self):
        super().apply()
        if bool(self.varOverwrite.get()):
            self.expHandler.deleteExp(self.lastExpName, self.expHandler.KEY_PRR_TEST)
        name = self.eName.get()
        if name:
            self.name = name
        else:
            self.name = None
                
        self.result = self.expHandler.createPrrTest(
            self.varAgc.get(), self.ePktCnt.get(), 
            self.eTxGain.get(), self.eRxGain.get(), self.eSleepTime.get(), 
            self.eSpreadLen.get(), self.ePayloadLen.get(), self.ePktType.get()
            )    
        if bool(self.varSave.get()):
            self.name = self.expHandler.saveExperiment(self.result, self.expHandler.KEY_PRR_TEST, self.name)    
        
class SelRangeParams(SelExpParams):
        
    def body(self, master):
        if self.lastExpName is not None:
            self.lastExp = self.expHandler.readExperiment(self.lastExpName, self.expHandler.KEY_RNG_TEST)
        super().body(master)
        
        Label(master, text="Range Delay (seconds):").grid(row=self.currRow, sticky=E)
        self.eRangeDelay = Entry(master, width=50)
        self.eRangeDelay.grid(row=self.currRow, column=1, sticky=W, padx=5, pady=5)
        self.currRow += 1
        
        Label(master, text="Speed of Sound:").grid(row=self.currRow, sticky=E)
        self.eSoundSpeed = Entry(master, width=50)
        self.eSoundSpeed.grid(row=self.currRow, column=1, sticky=W, padx=5, pady=5)
        
        if self.lastExp is not None:
            self.eRangeDelay.insert(0, self.lastExp.rangeDelay)
            self.eSoundSpeed.insert(0, self.lastExp.soundSpeed)
        
    def apply(self):
        if bool(self.varOverwrite.get()):
            self.expHandler.deleteExp(self.lastExpName, self.expHandler.KEY_RNG_TEST)
        name = self.eName.get()
        if name:
            self.name = name
        else:
            self.name = None
        super().apply()
        self.result = self.expHandler.createRangeTest(
            self.varAgc.get(), self.ePktCnt.get(), 
            self.eTxGain.get(), self.eRxGain.get(), self.eSleepTime.get(), 
            self.eSpreadLen.get(), self.eRangeDelay.get(), self.eSoundSpeed.get()
            )
        if bool(self.varSave.get()):
            self.expHandler.saveExperiment(self.result, self.expHandler.KEY_RNG_TEST, self.name)


import tkinter.ttk as ttk

class ExpProgressDialog(Dialog):
    
    def __init__(self, parent, title, maxValue: int):
        self.maxValue = maxValue
        super().__init__(parent, title)

    def body(self, master):
        self.pb = ttk.Progressbar(master, orient='horizontal', length=400, mode='determinate')
        self.pb['value'] = 0
        self.pb['maximum'] = self.maxValue
        self.pb.pack()
        
        return self.pb # initial focus

    def update(self, value: int):
        self.pb['value'] = value
        
from tkinter import Menu
        
class SelResultDialog(Dialog):
    
    def __init__(self, parent, resList, expName, funDelRes, funRenameRes):
        self.resList = resList
        self.expName = expName
        self.deleteResCb = funDelRes
        self.renameResCb = funRenameRes
        
        super().__init__(parent, "{}: Select Result".format(expName))

    def body(self, master):
        
        frame = Frame(master)
        frame.pack(fill=BOTH, expand=True)
        
        self.listBox = Listbox(frame, selectmode=SINGLE, font="Halvetica 12")
        self.listBox.pack(side=LEFT, fill=BOTH, expand=True)
        
        scrollbar = Scrollbar(frame, orient="vertical")
        scrollbar.config(command=self.listBox.yview)
        scrollbar.pack(side="right", fill="y")

        self.listBox.config(yscrollcommand=scrollbar.set)
        
        for res in self.resList:
            self.listBox.insert('end', res)
            
        self.listBox.select_set(0, 0)
        
        self.popup_menu = Menu(self, tearoff=0)
        self.popup_menu.add_command(label="Rename",
                                    command=self.renameSelected)
        self.popup_menu.add_command(label="Delete",
                                    command=self.deleteSelected)

        self.listBox.bind("<Button-3>", self.popup) # Button-2 on Aqua

        return self.listBox # initial focus
    
    def popup(self, event):
        try:
            self.popup_menu.tk_popup(event.x_root, event.y_root, 0)
        finally:
            self.popup_menu.grab_release()

    def apply(self):
        self.result = self.listBox.get(self.listBox.curselection())
        
    def renameSelected(self):
#         print(self.listBox.get(self.listBox.curselection()))
        
        currName = self.listBox.get(ACTIVE)
        saveName = simpledialog.askstring("Rename Result", "New Name", initialvalue=currName)
        if saveName is not None:
            if saveName:
                self.renameResCb(self.expName, currName, saveName)
                self.listBox.delete(ACTIVE)
                self.listBox.insert("end", saveName)
    
    def deleteSelected(self):
        deleted = self.deleteResCb(self.expName, self.listBox.get(self.listBox.curselection()))
        if deleted:
            self.listBox.delete(self.listBox.curselection())
        if self.listBox.size() <= 0:
            self.cancel()
        
from tkinter import simpledialog, messagebox
        
def askNewNodeName(oldName):
    return simpledialog.askstring("Rename " + oldName, "New name:[maximum 10 characters]")

def showInfoMessage(title, msg):
    messagebox.showinfo(title, msg)
    