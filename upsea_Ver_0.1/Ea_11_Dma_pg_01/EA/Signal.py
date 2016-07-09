# -*- coding: utf-8 -*-
from pyalgotrade.technical import ma
from pyalgotrade.technical import cross
import sys,os
import pandas as pd
import time as time
import datetime as dt

xpower = os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir,os.pardir,'Ea_00_BaseClass'))
sys.path.append(xpower)
from midBaseStrategy import midBaseStrategy as midBaseStrategy

#mid graphic result output
from Analyzer import Analyzer

#mid money
dataRoot = os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir,os.pardir))        
sys.path.append(dataRoot)
import Ea_02_money.moneyFixed  as moneyFixed
import Ea_02_money.moneyFirst  as moneyFirst
import Ea_02_money.moneySecond as moneySecond
  
class DMACrossOver(midBaseStrategy):
    def __init__(self):    
        self.__initDataCenter()
        self.__initEa()
    def __initEa(self):
        #mid 1)signal 控制参数
        self.InKLine = True
        self.longAllowed = True
        self.shortAllowed = True         
        self.__shortPeriod = 10
        self.__longPeriod = 20        
        #mid 2)signal 计算指标图形化输出控制
        #self.toPlot = True   
        self.analyzer  = Analyzer(Globals=[])   
        #mid 3)money 风险策略控制
        #self.money = moneySecond.moneySecond()  
        self.money = moneyFixed.moneyFixed()  
        
    def __initDataCenter(self):
        #mid 数据中心存取参数定义，决定当前被回测数据的储存属性，用于获取candledata，feeds 
        self.dataProvider = 'tushare'
        self.storageType = 'mongodb'
        self.period = 'D'
        self.instruments = ['000096']        
        self.instrument = self.instruments[0]   
    def initIndicators(self):
        #mid 3)
        self.__sma = ma.SMA(self.closePrices, self.__shortPeriod,maxLen=self.mid_DEFAULT_MAX_LEN)
        self.__lma = ma.SMA(self.closePrices,self.__longPeriod,maxLen=self.mid_DEFAULT_MAX_LEN)   
    def addIndicators(self):
        #mid 此处生成的数据仅由Analyzer消费
        self.result['short_ema'] = list(self.__sma)
        self.result['long_ema'] = list(self.__lma)
    
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