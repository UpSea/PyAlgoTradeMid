# -*- coding: utf-8 -*-
from pyalgotrade.technical import ma
from pyalgotrade.technical import cross
import sys,os
import pandas as pd

xpower = os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir,os.pardir,'BaseClass'))
sys.path.append(xpower)
from midBaseStrategy import midBaseStrategy as midBaseStrategy
import os,sys        
xpower = os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir,os.pardir,os.pardir,os.pardir,'midProjects','histdata'))
sys.path.append(xpower)

import dataCenter as dataCenter  

class DMACrossOver(midBaseStrategy):
    def __init__(self,toPlot = True,instruments = [],shortPeriod = 20,longPeriod = 40,dataProvider = 'tushare',
                 storageType = 'mongodb',period = 'D',feeds = None,money = None):    
        

        self.instruments = instruments
        self.instrument = instruments[0]
        self.shortPeriod = shortPeriod
        self.longPeriod = longPeriod
        self.dataProvider = dataProvider
        self.storageType = storageType
        self.period = period
        self.toPlot = toPlot        
        self.money = money
        self.analyzers = []     #mid every ea has many windows which should be kept separatly,other wise previous one will be release after new one constructed. 
        
        
        midBaseStrategy.__init__(self,feeds = feeds, instrument = instruments[0],money = money,longAllowed=True,shortAllowed=True)
        
    def initIndicators(self):
        #mid 3)
        shortPeriod=20
        longPeriod=40
        self.__sma = ma.SMA(self.closePrices, shortPeriod,maxLen=self.mid_DEFAULT_MAX_LEN)
        self.__lma = ma.SMA(self.closePrices,longPeriod,maxLen=self.mid_DEFAULT_MAX_LEN)   
    def addIndicators(self):
        #mid used to analyzer
        self.result['short_ema'] = list(self.__sma)
        self.result['long_ema'] = list(self.__lma)
    def analise(self):
        from Analyzer import Analyzer
    
        analyzer = Analyzer(Globals=[]) 
        dataForCandle = dataCenter.getCandleData(dataProvider = self.dataProvider,dataStorage = self.storageType,dataPeriod = self.period,
                                                 symbol = self.instrument,dateStart=self.timeFrom,dateEnd = self.timeTo)     
        analyzer.analyze(self.result,dataForCandle)        
        self.analyzers.append(analyzer)        
    def calcSignal(self):
        self.buySignal,self.sellSignal = False,False
        if(self.longAllowed):
            if self.longPosition is None:
                #mid 无多仓，检查是否需要开多仓
                if cross.cross_above(self.__sma, self.__lma) > 0:
                    self.buySignal = True   
        if(self.shortAllowed):
            if self.shortPosition is None:
                if cross.cross_below(self.__sma, self.__lma) > 0:
                    self.sellSignal = True 
    def onBars(self, bars):     
        self.calcSignal()
        self.closePosition()
        self.openPosition()
        self.recordPositions()      
        


    
      