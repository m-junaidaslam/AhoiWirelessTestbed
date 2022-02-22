'''
Created on Jun 18, 2019

@author: junai
'''

from tkinter import Frame, Scrollbar, VERTICAL, RIGHT, LEFT, X, Y, Canvas, BOTH, NW, Button, TOP, SUNKEN
from ControlCenter.UserInterfaces import NodeUi
from ControlCenter.UserInterfaces.DialogUtilities import AddNodeDialog, askNewNodeName, showInfoMessage


class NodesListFrame(Frame):
    """
    Frame to populate with user interfaces of modems
    """
    
    def __init__(self, master, rootPath, nodesManager, ctrlCHandler, mWhSupport):
        super().__init__(master=master)
        
        self.rootPath = rootPath
        self.config(background="gray", width=500, height=2, bd=2, relief=SUNKEN)
        
        frameButtons = Frame(self)
        
        self.btnAddNode = Button(
            master=frameButtons, text="Add Node", foreground="white", background='cadetblue',
             command=self.addNode, font=('Helvetica', '16', 'bold'), borderwidth=4, relief="raised")
        self.btnAddNode.pack(side=LEFT, fill=X, expand=True, padx=3, pady=3)
        
        self.btnRefreshList = Button(
            master=frameButtons, text="Refresh", foreground="white", background='cadetblue',
             command=self.refreshList, font=('Helvetica', '16', 'bold'), borderwidth=4, relief="raised")
        self.btnRefreshList.pack(side=RIGHT, fill=X, expand=True, padx=3, pady=3)
        
        frameButtons.pack(side=TOP, fill=X, padx=1, pady=5)
        
        yscroll = Scrollbar(self, orient=VERTICAL)
        yscroll.pack(side=RIGHT, fill=Y)
         
        self.canvas = Canvas(self, bg='gray')
        self.canvas.pack(side=RIGHT, fill=BOTH, expand=True)
        self.canvas['yscrollcommand'] = yscroll.set
#         self.canvas.bind("<MouseWheel>", self._onMousewheel)
        yscroll['command'] = self.canvas.yview
        
        mWhSupport.add_support_to(self.canvas, yscrollbar=yscroll, what="pages")
        
        self.listFrame = Frame(self.canvas, background="#b22222")
        self.listFrameId = self.canvas.create_window((0, 0), window=self.listFrame, anchor=NW) # Canvas equivalent of pack()
        
        self.listFrame.bind("<Configure>", self._onFrameConfigure)
        self.canvas.bind('<Configure>', self._onFrameSize)
        
        self.nodeUis = []
        self.ctrlCHandler = ctrlCHandler
        self.nodesManager = nodesManager
        self.nodesManager.setNodeUpdateCb(self.updateNode)
        
        self.createList()
        
        
    def _onFrameConfigure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
    def _onMousewheel(self, event):
        self.canvas.yview_scroll(-1*(int(event.delta/120)), "units")
        
    def _onFrameSize(self, event):
        canvasWidth = event.width
        self.canvas.itemconfig(self.listFrameId, width=canvasWidth)
            
    def addNode(self):
        """Add new node"""
        tmpClientId = None
        tmpName = None
        
        while True:
            addDialog = AddNodeDialog(self, "Add Node")
            if addDialog.result is None:
                break
            else:
                tmpClientId = addDialog.result[addDialog.KEY_CLIENT_ID]
                tmpName = addDialog.result[addDialog.KEY_NAME]
                
                if len(tmpClientId) <= 0 or len(tmpClientId) > 16:
                    showInfoMessage("Operation Failed", "Client ID should have 1 to 16 characters!")
                else:
                    if not tmpName:
                        tmpName = None
                    break
        if tmpClientId:
            res = self.nodesManager.addNode(tmpClientId, tmpName)
            if res == 0:
                self.appendList(self.nodesManager.getNodeById(tmpClientId))
            elif res == -1:
                showInfoMessage("Operation Failed", "Node with id " + tmpClientId + " already exists!")
    
    def createList(self):
        """Populate list when program is started"""
#         print("Create NodesListFrame")
        self.destroyList()
        if self.nodesManager.nodes:
            self.nodeUis = []
            for iNode in self.nodesManager.nodes:
                self.appendList(iNode)
                
        else:
            showInfoMessage("Nodes not found", "No saved nodes")
            
    def appendList(self, newNode):
        """Load new modem into list, called recursively to populate list"""
        nodeUi = NodeUi.NodeUi(self.listFrame, self.rootPath, newNode, self.ctrlCHandler, self.refreshList, self.rename, self.delete)
        nodeUi.pack(fill='x', expand=True, padx=2, pady=2)
        self.nodeUis.append(nodeUi)
            
    def refreshList(self):
        """Refresh status of all nodes"""
        if self.nodesManager.nodes:
            for iNode in self.nodesManager.nodes:
                iNode.refreshStatus()
                self.updateNode(iNode)
        else:
            showInfoMessage("Nodes not found", "No nodes saved")
            
    def updateNode(self, currNode):
        """Update fields of single modem's user interface"""
        for nodeUi in self.nodeUis:
            if currNode.nodeId == nodeUi.controlModem.nodeId:
                nodeUi.updateNode(currNode)
            
    def destroyList(self):
        """Remove interface of all nodes"""
        for nodeUi in self.nodeUis:
            nodeUi.destroy()
            
    def rename(self, nodeUi):
        """Rename single node"""
        newName = None
        while True:
            newName = askNewNodeName(nodeUi.controlModem.name)
            if newName is not None:
                if len(newName) <= 0 or len(newName) > 10:
                    showInfoMessage("Operation Failed", "Name should have 1 to 10 characters!")
                else:
                    break
            
                if newName:
                    nodeUi.controlModem.name = newName
                    self.nodesManager.dumpNodesToFile()
                    nodeUi.refreshUi()
            else:
                break
        
    def delete(self, nodeUi):
        """Delete single node"""
        nodeUi.destroy()
        self.nodesManager.removeNode(nodeUi.controlModem)