'''
Created on Jun 18, 2019

@author: junai
'''

from tkinter import Frame, Button, Label, messagebox, LEFT, Menu, W
import threading
from ControlCenter.Node import ControlMosh
from ControlCenter.UserInterfaces import MoshGUI

class NodeUi(Frame):
    '''
    User interface of saved modems in main GUI
    '''

    def __init__(self, master, rootPath, controlModem, ctrlCHandler, funRefreshCallback, funRename, funDelete):
        '''
        Constructor
        '''
        super().__init__(master)
        self.rootPath = rootPath
        self.funRefreshCallBack = funRefreshCallback
        
        self.config(padx=5, pady=5, highlightbackground="skyblue", highlightcolor="skyblue", highlightthickness=1, bd= 0)
        
        self.lblModName = Label(
            master=self , width=12,
             borderwidth=2, anchor=W, font=('Calbri', '12', 'bold'))
        self.lblModName.pack(side=LEFT, padx=5)
        
        self.lblStatus = Label(master=self, width=12, foreground="white", borderwidth=2, anchor=W, relief="groove")
        self.lblStatus.pack(side=LEFT, padx=5)
        
        self.lblModClient = Label(
            master=self , width=20,
             borderwidth=2, relief="groove")
        self.lblModClient.pack(side=LEFT, padx=5)
        
        self.lblModId = Label(master=self, width=10, borderwidth=2, anchor=W, relief="groove")   
        self.lblModId.pack(side=LEFT, padx=5)
        
        
        self.lblModVersion = Label(master=self, width=25, borderwidth=2, anchor=W, relief="groove")
        self.lblModVersion.pack(side=LEFT, padx=5)
        
        self.updateNode(controlModem)
        
        self.ctrlCHandler = ctrlCHandler
        self.btnMosh = Button(
            master=self, text="Mosh", background="Orange",
             width=20, command=self.startMosh, font=('Calbri', '10', 'bold'))
        self.btnMosh.pack(side=LEFT, padx=10)
        
        self.popMenu = Menu(self, tearoff=0)
        self.popMenu.add_command(label="Refresh", command=lambda: self.refreshUi())
        self.popMenu.add_command(label="Rename", command=lambda: funRename(self))
        self.popMenu.add_command(label="Delete", command=lambda: funDelete(self))
        
        self.bind("<Button-3>", self.popup) # Button-2 on Aqua
        
        for iwidget in self.winfo_children():
            iwidget.bind("<Button-3>", self.popup) # Button-2 on Aqua
        
    def updateNode(self, controlModem):
        """Update the fields in node UI"""
#         print("NodeUi: Update: " + controlModem.name)
        self.controlModem = controlModem
        self.lblModName['text'] = controlModem.name
        self.lblModClient['text'] = "Client: "+controlModem.nodeId
        self.lblModId['text'] = self.getModIdStr()
        self.lblModVersion['text'] = self.getModVersionStr()
        self.lblStatus['text'] = self.getModAliveStr()
        
        
    def popup(self, event):
        """Right click event"""
        try:
            self.popMenu.tk_popup(event.x_root, event.y_root, 0)
        finally:
            self.popMenu.grab_release()
    
    def refreshUi(self):
        """Get latest modem status from modem"""
        self.controlModem.refreshStatus()
        self.updateNode(self.controlModem)
        
        
    def promptNodeUnavail(self):
        """Prompt if node is offline when timer after starting Mosh expires"""
        self.timerExpired = True
        self.btnMosh.config(state="normal")
        messagebox.showinfo("Node Offline", self.controlModem.name + " is offline")
        
        
    def getModAliveStr(self):
        """Convert Modem Alive status to representation in field of UI"""
        if self.controlModem.alive:
            self.lblStatus['background'] = 'green'
            return "Status: Online"
        else:
            self.lblStatus['background'] = 'red'
            return "Status: Offline"
        
    def getModIdStr(self):
        """Convert Modem Id to representation in field of UI"""
        strModId = "ID: "
        if self.controlModem.modId is None:
            strModId += "N/A"
        else:
            strModId += str(self.controlModem.modId)
        return strModId
    
    def getModVersionStr(self):
        """Convert Modem Version to representation in field of UI"""
        strModVer = "Version: "
        if self.controlModem.modVersion is None:
            strModVer += "N/A"
        else:
            strModVer += self.controlModem.modVersion
        return strModVer
        
    def startMosh(self):
        """Start Modem Shell for modem when Mosh button clicked"""
        self.controlModem.refreshStatus()
        timer = threading.Timer(5, self.promptNodeUnavail) # Start node availability check timer
        self.btnMosh.config(state="disable")
        self.timerExpired = False
        timer.start()
          
#         print("Timer started")       
        while True:
#             print("Control modem alive: " + str(self.controlModem.alive))
            if self.controlModem.alive:
                timer.cancel()
#                 print("Control modem is alive")
                # Modem is alive
                self.updateNode(self.controlModem)
                break
              
            if self.timerExpired:
                # Modem not alive, timer expired
                self.timerExpired = False
                return

        # Start Mosh in a new thread
        self.moshGUIThread = threading.Thread(target=self.startMoshGUI, name="moshguithread_" + self.controlModem.nodeId, args=[])
        self.moshGUIThread.daemon = True
        self.moshGUIThread.start()
        
    def startMoshGUI(self):
        """Function to run in Mosh Thread"""
        controlMosh = ControlMosh.ControlMosh(self.rootPath, self.ctrlCHandler)
        MoshGUI.MoshGUI(controlMosh, self.controlModem, self.moshClosedCallback)
        
    def moshClosedCallback(self):
        """Called when Mosh is closed"""
        if self.winfo_exists():
            self.btnMosh.config(state="normal")
            self.controlModem.refreshStatus()
            self.updateNode(self.controlModem)
#             print("Mosh button is normal")
            