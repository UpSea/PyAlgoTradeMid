# -*- coding: utf-8 -*-
from pyalgotrade.technical import ma
from pyalgotrade.technical import cross
import sys,os
import pandas as pd

xpower = os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir,os.pardir))
sys.path.append(xpower)
from midBaseStrategy import midBaseStrategy as midBaseStrategy

class DMACrossOver(midBaseStrategy):
    def initIndicators(self,shortPeriod =  0,longPeriod = 0):
        #mid 3)
        self.__sma = ma.SMA(self.closePrices, shortPeriod,maxLen=self.mid_DEFAULT_MAX_LEN)
        self.__lma = ma.SMA(self.closePrices,longPeriod,maxLen=self.mid_DEFAULT_MAX_LEN)          
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
    def run(self):
        result = midBaseStrategy.run(self)
        
        #mid used to analyzer
        result['short_ema'] = list(self.__sma)
        result['long_ema'] = list(self.__lma)
        return result
    def onBars(self, bars):     
        self.calcSignal()
        self.closePosition()
        self.openPosition()
        self.recordPositions()            