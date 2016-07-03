# -*- coding: utf-8 -*-
import os,sys
from PyQt4 import QtGui,QtCore
import time as time
import datetime as dt

#mid 3)money
dataRoot = os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir))        
sys.path.append(dataRoot)
import money.moneyFixed  as moneyFixed
import money.moneyFirst  as moneyFirst
import money.moneySecond as moneySecond
import EA.Ea             as Ea
 
class eaController():
    def __init__(self,timeFrom,timeTo,phases):
        self.timeFrom = timeFrom
        self.timeTo = timeTo
        self.phases = phases
        self.ea = self.getEa()
    def run(self):
        self.results = self.runByPhase(self.timeFrom,self.timeTo,self.phases)
        print  "------------------------"
        print self.timeFrom,' to ',self.timeTo
        print  "------------------------"
        for result in self.results:
            print result         
    def runByPhase(self,timeFrom,timeTo,phases):
        #mid str to pyTimeStamp
        timeStampFrom = int(time.mktime(time.strptime(timeFrom, "%Y-%m-%d %H:%M:%S")))
        timeStampTo   = int(time.mktime(time.strptime(timeTo, "%Y-%m-%d %H:%M:%S")))    
        print timeFrom,timeTo
        
        interval = (timeStampTo - timeStampFrom)/phases
        
        startTimeStamp = timeStampFrom
        self.results01 = []
        self.results02 = []
        for index in range(phases):
            endTimeStamp = startTimeStamp + interval
            
            #mid pyTimeStamp to datetime
            timeFromDatetime = dt.datetime.utcfromtimestamp(startTimeStamp)
            timeToDatetime = dt.datetime.utcfromtimestamp(endTimeStamp)
            '''
            #mid pyTimeStamp to datetime to str
            timeFrom = dt.datetime.utcfromtimestamp(startTimeStamp).strftime("%Y-%m-%d %H:%M:%S")
            timeTo = dt.datetime.utcfromtimestamp(endTimeStamp).strftime("%Y-%m-%d %H:%M:%S")
            
            #mid str to datetime
            timeFrom = dt.datetime.strptime(timeFrom,'%Y-%m-%d %H:%M:%S')    
            timeTo = dt.datetime.strptime(timeTo,'%Y-%m-%d %H:%M:%S')              
            
            '''
            result01 = self.ea.run(timeFrom = timeFromDatetime,timeTo = timeToDatetime)
            self.results01.append(result01)
            
            result02 = self.ea.summary() 
            self.results02.append(result02)
            
            startTimeStamp = endTimeStamp
            
        return self.results02
    def getEa(self):    
        instruments = ['XAUUSD']
        money = moneySecond.moneySecond()  
        ea = Ea.Expert(toPlot=True,  shortPeriod=10,longPeriod=20, 
                      dataProvider = 'mt5',storageType = 'csv',period = 'm5',
                      instruments=instruments,money = money)    
        return ea        
if __name__ == "__main__": 
    app = QtGui.QApplication(sys.argv)    
    startRun = time.clock()
    
    eaController('2016-05-20 00:00:00', '2016-05-30 00:00:00', 2).run()
    
    endRun = time.clock()
    print "run time: %f s" % (endRun - startRun)       
    sys.exit(app.exec_())  
