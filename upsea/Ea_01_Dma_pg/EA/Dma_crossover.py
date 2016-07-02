# -*- coding: utf-8 -*-
from pyalgotrade import strategy
from pyalgotrade.technical import ma
from pyalgotrade.technical import cross
from pyalgotrade.dataseries import SequenceDataSeries
from pyalgotrade.dataseries import DEFAULT_MAX_LEN
import pandas as pd
import sys,os
xpower = os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir,os.pardir))
sys.path.append(xpower)
from midBaseStrategy import midBaseStrategy as midBaseStrategy

class DMACrossOver(midBaseStrategy):
    #def __init__(self, feeds = None, instrument = '',money = None,longAllowed=True,shortAllowed=True):
        #midBaseStrategy.__init(feeds = feeds, instrument = instrument,money = money,longAllowed=longAllowed,shortAllowed=shortAllowed)
    def initIndicators(self,shortPeriod =  0,longPeriod = 0):
        mid_DEFAULT_MAX_LEN = self.mid_DEFAULT_MAX_LEN
        
        #mid 计算ma将使用当天的收盘价格计算
        #mid 1)
        dataSeries = self.feeds[self.instrument]
        dataSeries.setMaxLen(mid_DEFAULT_MAX_LEN)       
        closeSeries = dataSeries.getOpenDataSeries()
        #mid 2)
        prices = closeSeries
        prices.setMaxLen(mid_DEFAULT_MAX_LEN)
        #mid 3)
        self.__sma = ma.SMA(prices, shortPeriod,maxLen=mid_DEFAULT_MAX_LEN)
        self.__lma = ma.SMA(prices,longPeriod,maxLen=mid_DEFAULT_MAX_LEN)       
    def getSMA(self):
        return self.__sma
    def getLMA(self):
        return self.__lma   
    def closePosition(self):
        if(self.longPosition is not None and self.sellSignal == True):
            self.info("onBars().Status info,before exitMarket(), LONG POSITION to close %.2f" 
                      % (self.longPosition.getShares()))                                    
            self.longPosition.exitMarket()
        if(self.shortPosition is not None and self.buySignal == True):
            self.info("onBars().Status info,before exitMarket(), SHORT POSITION to close %.2f" 
                    % (self.shortPosition.getShares()))  
            self.shortPosition.exitMarket()          
    def getSignal(self):
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
    def openPosition(self):
        '''mid
        此处是onBars，这个和zipline的概念完全不同
        zipline中，需要覆写的是handle_data，这个东西是个tick概念，所以没有OHLC的，只是个price
        PAT中，每次onBars，都会传入一个newbar的OHLC，此时，要如何按这个OHLC决策，全由你
        依据OHLC做完决策后，可以发送交易指令：
        * Order.Type.MARKET
        * Order.Type.LIMIT
        * Order.Type.STOP
        * Order.Type.STOP_LIMIT
        1.市价单，依据下一个bar的openPrice执行命令：
            self.enterLong()
        2.限价单
        3.止损单市价单
        4.止损限价单

        当前似乎没有止盈单

        在均线策略中，应该在每个newbar到来时，按closePrice的均线计算指标值，然后发送市价单
        1.每个newbar按close价格计算指标，并在下一个bar按open成交
        2.每个newbar按open价格计算指标，并在此newbar按open成交
        以上1,2的计算逻辑是一致的。如果当前bar的close和下一个bar的open相差无几时，两种算法的回测结果也应相差无几
        '''         
        # mid 2)open
        if(self.buySignal == True):
            shares = self.money.getShares(strat = self)                    
            self.info("onBars().Status info,before enterLong(), LONG POSITION to open %.2f,need amount: %.2f,available amount: %.2f." % 
                      (shares,shares*self.getLastPrice(self.instrument),self.getBroker().getCash() ))                                    
            self.longPosition = self.enterLong(self.instrument, shares, True)
        if(self.sellSignal == True):
            # Enter a buy market order. The order is good till canceled.
            shares = self.money.getShares(strat = self)
            self.info("onBars().Status info,before enterShort(), SHORT POSITION to open %.2f,need amount: %.2f,available amount: %.2f." % 
                      (shares,shares*self.getLastPrice(self.instrument),self.getBroker().getCash() ))                                    
            self.shortPosition = self.enterShort(self.instrument, shares, True)
    def onBars(self, bars):     
        self.getSignal()
        self.closePosition()
        self.openPosition()
        self.recordPositions()            