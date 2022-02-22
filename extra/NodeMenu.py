'''
Created on Jun 23, 2019

@author: junai
'''

from tkinter import Listbox, Menu

class NodeMenu(Listbox):
    '''
    classdocs
    '''


    def __init__(self, master, nodesManager):
        '''
        Constructor
        '''
        super().__init__(master)
        
        self.nodesManager = nodesManager
        self.nodeUi = master
        
        self.popMenu = Menu(self, tearoff=0)
        
        self.popMenu.add_command(label="Refresh", command=lambda: self.nodeUi.refreshUi())
        self.popMenu.add_command(label="Rename", command=lambda: self.rename())
        self.popMenu.add_command(label="Delete", command=lambda: nodesManager)
        
        self.bind("<Button-3>", self.popup) # Button-2 on Aqua
        
        
        
    def popup(self, event):
        try:
            self.popMenu.tk_popup(event.x_root, event.y_root, 0)
        finally:
            self.popup_menu.grab_release()
            
        
    def rename(self):
        self.nodesManager.renameNode(self.nodeUi.controlModem)
        self.nodeUi.refreshUi()
        
    def delete(self):
        self.nodesManager.removeNode(self.nodeUi.controlModem)
        self.nodeUi.refreshUi()
        
    
        