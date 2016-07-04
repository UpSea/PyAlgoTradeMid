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
import EA.Dma_crossover  as Dma_crossover
 
class eaController():
    def __init__(self,timeFrom,timeTo,phases,toPlot):
        self.timeFrom = timeFrom
        self.timeTo = timeTo
        self.phases = phases

        self.instruments = ['XAUUSD']        
        self.shortPeriod = 10
        self.longPeriod = 20
        self.dataProvider = 'mt5'
        self.storageType = 'csv'
        self.period = 'm5'
        self.toPlot = toPlot        
        self.money = moneySecond.moneySecond()  
        self.analyzers = []             
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
            
            feeds = self.getFeeds(timeFrom = timeFromDatetime,timeTo = timeToDatetime)
            ea = Dma_crossover.DMACrossOver(toPlot=self.toPlot,  shortPeriod=self.shortPeriod,longPeriod=self.longPeriod, 
                                            dataProvider = self.dataProvider,storageType = self.storageType,period = self.period,
                                            instruments=self.instruments,money = self.money,feeds = feeds)               
            self.results01.append(ea)
            ea.run(timeFrom = timeFromDatetime,timeTo = timeToDatetime)
            
            result02 = ea.summary() 
            self.results02.append(result02)
            
            startTimeStamp = endTimeStamp
            
        return self.results02     
    def getFeeds(self,timeFrom=None,timeTo=None):
        import os,sys        
        xpower = os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir,os.pardir,os.pardir,'midProjects','histdata'))
        sys.path.append(xpower)
        
        import dataCenter as dataCenter            
        self.dataCenter = dataCenter.dataCenter()           
        feeds = self.dataCenter.getFeedsForPAT(dataProvider = self.dataProvider,storageType = self.storageType,instruments = self.instruments,
                                               period=self.period,timeTo = timeTo,timeFrom=timeFrom)        
        return feeds
if __name__ == "__main__": 
    app = QtGui.QApplication(sys.argv)    
    startRun = time.clock()
    
    eaController('2016-05-20 00:00:00', '2016-05-30 00:00:00', 2,False).run()
    
    endRun = time.clock()
    print "run time: %f s" % (endRun - startRun)       
    sys.exit(app.exec_())  
