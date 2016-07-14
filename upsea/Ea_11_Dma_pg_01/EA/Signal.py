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
        self.__shortPeriod = 5
        self.__longPeriod = 20        
        #mid 2)signal 计算指标图形化输出控制
        #self.toPlot = True   
        self.analyzer  = Analyzer(Globals=[])   
        #mid 3)money 风险策略控制
        #self.money = moneySecond.moneySecond()  
        self.money = moneyFixed.moneyFixed()  
        
    def __initDataCenter(self):
        #mid 数据中心存取参数定义，决定当前被回测数据的储存属性，用于获取candledata，feeds 
        self.period = 'D'
        if(False):
            self.dataProvider = 'tushare'
            self.storageType = 'mongodb'
            self.instruments = ['000096','000099','600839','600449']#,'600839']        
        else:
            self.dataProvider = 'mt5'
            self.storageType = 'csv'            
            self.instruments = ['XAUUSD','EURUSD'] 
            #self.instruments = ['EURUSD'] 

    def initIndicators(self):
        #mid 3)
        self.__sma = {}
        self.__lma = {}        
        for instrument in self.instruments:
            self.__sma[instrument] = ma.SMA(self.closePrices[instrument], self.__shortPeriod,maxLen=self.mid_DEFAULT_MAX_LEN)
            self.__lma[instrument] = ma.SMA(self.closePrices[instrument],self.__longPeriod,maxLen=self.mid_DEFAULT_MAX_LEN)
    def addIndicators(self,instrument):
        #mid 此处生成的数据仅由Analyzer消费
        short_ema = pd.DataFrame(data=list(self.__sma[instrument]),index=self.__sma[instrument].getDateTimes(),columns = ['short_ema'])
        long_ema = pd.DataFrame(data=list(self.__lma[instrument]),index=self.__lma[instrument].getDateTimes(),columns = ['long_ema'])
        
        self.results[instrument] = self.results[instrument].join(short_ema)
        self.results[instrument] = self.results[instrument].join(long_ema)
        #self.results[instrument]['short_ema'] = e['short_ema']
        #self.results[instrument]['long_ema'] = list(self.__lma[instrument])
    def calcSignal(self):
        self.buySignal,self.sellSignal = {},{}
        for instrument in self.instruments:
            self.buySignal[instrument],self.sellSignal[instrument] = False,False
            #if(self.longAllowed):
            if self.longPosition[instrument] is None:
                #mid 无多仓，检查是否需要开多仓
                if cross.cross_above(self.__sma[instrument], self.__lma[instrument]) > 0:
                    self.buySignal[instrument] = True   
            #if(self.shortAllowed ):
            if self.shortPosition[instrument] is None:
                if cross.cross_below(self.__sma[instrument], self.__lma[instrument]) > 0:
                    self.sellSignal[instrument] = True 
    def onBars(self, bars):     
        self.calcSignal()
        self.closePosition()
        self.openPosition()
        self.recordAccount()      