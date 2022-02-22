'''
Created on Jun 10, 2019

@author: junai
'''

"""Handler to handle Ctrl+C event"""

import signal

class CtrlCHandler():
    '''
    Handle event when user exits program using by pressing "Ctrl+C"
    '''

    def __init__(self, handlerMethod):
        '''
        Constructor
        '''
        self.sigIntEn = True
        self.gIrq = False
        self.signal = signal.signal(signal.SIGINT, handlerMethod)
        
    
    def sigInt_enable(self):
        """Enable handler"""
        self.sigIntEn = True
        self.gIrq = False
    
    
    def sigInt_disable(self):
        """Disable handler"""
        self.sigIntEn = False
        self.gIrq = False
    
    
    def sigInt_check(self):
        """Check for Ctrl+C signal"""
        if self.gIrq:
            self.sigInt_enable()
            return True
        return False