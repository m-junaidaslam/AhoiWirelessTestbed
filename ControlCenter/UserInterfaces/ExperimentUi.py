'''
Created on Jun 18, 2019

@author: junai
'''

from tkinter import Frame, Button, Label, messagebox, LEFT, Menu, W

class ExperimentUi(Frame):
    '''
    classdocs
    '''

    def __init__(self, master, expName, expType, expData, expHandler, funParamasDialog, funRunExp, funShowResults):
        '''
        Constructor
        '''
        super().__init__(master)
        self.expHandler = expHandler
        self.paramasDialog = funParamasDialog
        self.runExpCb = funRunExp
        self.showResCb = funShowResults
        
        self.config(padx=5, pady=5, highlightbackground="skyblue", highlightcolor="skyblue", highlightthickness=1, bd= 0)
        
        self.lblExpName = Label(
            master=self , width=20,
             borderwidth=2, anchor=W, font=('Calbri', '10', 'bold'))
        self.lblExpName.pack(side=LEFT, padx=2)
        
        self.lblExpTime = Label(
            master=self, width=23, foreground="black", borderwidth=2, 
            anchor=W, relief="groove", font=('Calbri', '8'))
        self.lblExpTime.pack(side=LEFT, padx=2)
        
        self.lblExpType = Label(
            master=self, width=15, foreground="black", borderwidth=2, 
            anchor=W, relief="groove", font=('Calbri', '8'))
        self.lblExpType.pack(side=LEFT, padx=2)
        
        self.btnRun = Button(
            master=self, text="Run", background="Orange",
             width=5, command=self.runExp, font=('Calbri', '8', 'bold'))
        self.btnRun.pack(side=LEFT, padx=5)
        
        self.updateExp(expName, expType, expData)
        
        self.popMenu = Menu(self, tearoff=0)
        self.popMenu.add_command(label="View Results", command=lambda: self.showResults())
        self.popMenu.add_command(label="Edit", command=lambda: self.editExp())
        self.popMenu.add_command(label="Delete", command=lambda: self.deleteExp())
        
        self.bind("<Button-3>", self.popup) # Button-2 on Aqua
        
        for iwidget in self.winfo_children():
            iwidget.bind("<Button-3>", self.popup) # Button-2 on Aqua
            
        
    def updateExp(self, expName, expType, expData):
        self.expName = expName
        self.expType = expType
        self.expData = expData
        self.lblExpName['text'] = expName
        self.lblExpType['text'] = "Type: " + expType
        self.lblExpTime['text'] = "Time: " + self.expData.basic.time
        
    def popup(self, event):
        try:
            self.popMenu.tk_popup(event.x_root, event.y_root, 0)
        finally:
            self.popMenu.grab_release()
            
    def runExp(self):
#         print("Run Experiment: " + self.expName)
#         print(self.expData)
        self.runExpCb(self.expName, self.expData)
        
    def showResults(self):
        self.showResCb(self.expName)
    
    def editExp(self):
#         print("Edit Experiment: " + self.expName)
#         print(self.expData)
        self.paramasDialog(self.expName, True)
    
    def deleteExp(self):
        #delete file
        messagebox.showinfo("Deleted", "Experiment " + self.expName + " of type " + self.expType + " deleted!")
        self.expHandler.deleteExp(self.expName, self.expType)
        self.destroy()