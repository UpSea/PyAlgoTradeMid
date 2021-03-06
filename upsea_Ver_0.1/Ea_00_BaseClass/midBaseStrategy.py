# -*- coding: utf-8 -*-
from pyalgotrade import strategy
from pyalgotrade.technical import ma
from pyalgotrade.technical import cross
from pyalgotrade.dataseries import SequenceDataSeries
from pyalgotrade.dataseries import DEFAULT_MAX_LEN
import pandas as pd

class midBaseStrategy(strategy.BacktestingStrategy):
    def getFeeds(self,timeFrom=None,timeTo=None):
        import os,sys        
        xpower = os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir,os.pardir,os.pardir,'midProjects','histdata'))
        sys.path.append(xpower)
        
        import dataCenter as dataCenter            
        self.dataCenter = dataCenter.dataCenter()           
        feeds = self.dataCenter.getFeedsForPAT(dataProvider = self.dataProvider,storageType = self.storageType,instruments = self.instruments,
                                               period=self.period,timeTo = timeTo,timeFrom=timeFrom)        
        return feeds       
    def initEa(self,timeFrom=None,timeTo=None):
        
        feeds = self.getFeeds(timeFrom = timeFrom,timeTo = timeTo)
        
        instrument = self.instrument
        
        strategy.BacktestingStrategy.__init__(self, feeds[instrument])
        self.mid_DEFAULT_MAX_LEN = 10 * DEFAULT_MAX_LEN
        
        
        mid_DEFAULT_MAX_LEN = self.mid_DEFAULT_MAX_LEN
    
        #mid 计算ma将使用当天的收盘价格计算
        #mid 1)
        feed = feeds[instrument] 
        dataSeries = feed[instrument]
        dataSeries.setMaxLen(mid_DEFAULT_MAX_LEN)       
        closeSeries = dataSeries.getCloseDataSeries()
        #mid 2)
        prices = closeSeries
        prices.setMaxLen(mid_DEFAULT_MAX_LEN)        
        self.closePrices = prices

        #mid follow vars will be used in subclass
        self.timeFrom = timeFrom
        self.timeTo = timeTo
        
        self.instrument = instrument
        self.longPosition = None
        self.shortPosition = None
        self.buySignal = False
        self.sellSignal = False

        #mid follow vars will be used only this class
        self.__curPositionCost = 0  #mid init position value
        mid_DEFAULT_MAX_LEN = self.mid_DEFAULT_MAX_LEN
        self.__position_volume = SequenceDataSeries(maxLen = mid_DEFAULT_MAX_LEN)       #mid 当前持有头寸数量
        self.__position_cost = SequenceDataSeries(maxLen = mid_DEFAULT_MAX_LEN)  #mid 当前持有头寸开仓成本
        self.__position_pnl = SequenceDataSeries(maxLen = mid_DEFAULT_MAX_LEN)   #mid 当前持有头寸价值
        self.__portfolio_value = SequenceDataSeries(maxLen = mid_DEFAULT_MAX_LEN)
        self.__buy = SequenceDataSeries(maxLen = mid_DEFAULT_MAX_LEN)
        self.__sell = SequenceDataSeries(maxLen = mid_DEFAULT_MAX_LEN)        
    def getAssetStructure(self):
        #mid --------------------------------
        #mid 当前账户资产结构如下方式获取
        #mid Long 和 Short不会同时存在
        #mid 在开仓前，若有反向持仓，则此过程查询并输出已持有的反向持仓
        broker = self.getBroker()
        portfolio_value = broker.getEquity()
        cash = broker.getCash()
        if self.shortPosition is not None or self.longPosition is not None:
            bars = self.getFeed().getCurrentBars()  

            positions = broker.getPositions()

            positionsOpenValue = {}
            positionsCloseValue = {}
            for key,value in positions.items():
                print "key:"+key+",value:"+str(value)
                bar = bars.getBar(key)
                openPrice = bar.getOpen() 
                closePrice = bar.getClose()
                share = broker.getShares(key)
                positionsOpenValue[key] = openPrice*share
                positionsCloseValue[key] = closePrice*share

            print 
            print 'current bar asset structure'
            print 'open cash %2.f.' % (cash)
            for key,value in positionsOpenValue.items():
                print "key:"+key+",value:"+str(value)
            print 'close cash %2.f.' % (cash)
            for key,value in positionsCloseValue.items():
                print "key:"+key+",value:"+str(value)    
            print 'portfolio:%2.f' % (portfolio_value)

            return portfolio_value,cash,sum(positionsCloseValue.values())
        return portfolio_value,cash,0
    def recordPositions(self):
        # record position      
        #######################################################################
        broker = self.getBroker()
        position = broker.getPositions()                   #mid position is dict of share
        share = broker.getShares(self.instrument)        #mid position is dict of share
        lastPrice = self.getLastPrice(self.instrument)  
        portfolio_value = broker.getEquity()               #mid 按close价格计算的权益
        cash = broker.getCash()

        position_value = portfolio_value - cash

        position_pnl = position_value - self.__curPositionCost

        print
        print 'cash: %.2f' %(cash)
        print 'position value: %.2f' % (portfolio_value - cash)
        print 'mid calc: %.2f' %(lastPrice*share+cash)
        print 'broker returned: %.2f' %(portfolio_value)


        curTime = self.getCurrentDateTime()
        currentTime = self.getCurrentDateTime()

        self.__position_volume.appendWithDateTime(currentTime,abs(share))  

        self.__position_cost.appendWithDateTime(currentTime,abs(self.__curPositionCost))

        self.__position_pnl.appendWithDateTime(currentTime,position_pnl)

        self.__portfolio_value.appendWithDateTime(currentTime,portfolio_value)  
        self.__buy.appendWithDateTime(currentTime,self.buySignal)              
        self.__sell.appendWithDateTime(currentTime,self.sellSignal) 
    def getInstrument(self):
        return self.instrument
    def getPortfolio(self):
        return self.__portfolio_value
    def getPositionVolume(self):
        return self.__position_volume    
    def getPositionCost(self):
        return self.__position_cost
    def getPositionPnl(self):
        return self.__position_pnl 

    def getBuy(self):
        return self.__buy
    def getSell(self):
        return self.__sell
    def onEnterOk(self, position):
        execInfo = position.getEntryOrder().getExecutionInfo()   
        portfolio = self.getResult()
        cash = self.getBroker().getCash() 

        '''mid
  以下两种方法都是为了计算持仓成本
  由于getEquity()返回的是依据当日close价格计算出来的权益
  所以，这个值不能作为持仓成本
  持仓成本需要以onEnterOk时bar的open价格计算
  所以应使用第二种算法
  由于经常有跳开现象，所以依据bar(n-1).close发出的market order，
  在bar(n).open执行时通常会有gap出现，表现在position_cost图上时就是持有成本离计划成本会有跳口，
  '''
        if(False):#mid two methods to cacl cost.
            portfolio_value = self.getBroker().getEquity()
            self.__curPositionCost = portfolio_value - cash  
        else:
            feed = self.getFeed()
            bars = feed.getCurrentBars()
            bar = bars.getBar(self.instrument)
            openPrice = bar.getOpen()   
            closePrice = self.getLastPrice(self.instrument) #mid lastPrice == closePrice
            share = self.getBroker().getShares(self.instrument)
            self.__curPositionCost = openPrice*share

        self.info("onEnterOk().current available cash: %.2f,portfolio: %.2f." % (cash,portfolio))
        if isinstance(position, strategy.position.LongPosition):
            self.info("onEnterOK().ExecutionInfo: %s,OPEN LONG %.2f at $%.2f" 
                      % (execInfo.getDateTime(),execInfo.getQuantity(),execInfo.getPrice())) 
        elif isinstance(position, strategy.position.ShortPosition):
            self.info("onEnterOK().ExecutionInfo: %s,OPEN SHORT %.2f at $%.2f" 
                      % (execInfo.getDateTime(),execInfo.getQuantity(),execInfo.getPrice()))     



    def onEnterCanceled(self, position):
        self.info("onEnterCanceled().current available cash: %.2f." % (self.getBroker().getCash()))
        if isinstance(position, strategy.position.LongPosition):
            self.longPosition = None
            self.info("onEnterCanceled().OPEN LONG cancled.")                                
        elif isinstance(position, strategy.position.ShortPosition):
            self.shortPosition = None
            self.info("onEnterCanceled().OPEN SHORT cancled.")
    def onExitOk(self, position):        
        execInfo = position.getExitOrder().getExecutionInfo()     
        portfolio = self.getResult()
        cash = self.getBroker().getCash()
        self.info("onExitOk().current available cash: %.2f,portfolio: %.2f." % (cash,portfolio))

        if isinstance(position, strategy.position.LongPosition):
            self.longPosition = None
            self.info("onExitOk().ExecutionInfo: %s,CLOSE LONG %.2f at $%.2f" 
                      % (execInfo.getDateTime(),execInfo.getQuantity(),execInfo.getPrice()))                    
        elif isinstance(position, strategy.position.ShortPosition):
            self.shortPosition = None
            self.info("onExitOk().ExecutionInfo: %s,CLOSE SHORT %.2f at $%.2f" 
                      % (execInfo.getDateTime(),execInfo.getQuantity(),execInfo.getPrice()))                    
    def onExitCanceled(self, position):
        # If the exit was canceled, re-submit it.
        if isinstance(position, strategy.position.LongPosition):
            self.longPosition = None
        elif isinstance(position, strategy.position.ShortPosition):
            self.shortPosition = None
    def logInfo(self,bars = None):
        pLong,pShort = 0,0
        if(self.longPosition is not None):
            pLong = self.longPosition.getShares()
        if(self.shortPosition is not None):
            pShort = self.shortPosition.getShares()


        bar = bars[self.instrument]
        pOpen = bar.getOpen()
        pHigh = bar.getHigh()
        pLow = bar.getLow()
        pClose = bar.getClose()
        pPrice = bar.getPrice()

        self.info('logInfo().price:%.3f,open:%.2f,high:%.2f,low:%.2f,close:%.2f'%(pPrice,pOpen,pHigh,pLow,pClose))
        #self.info('long:%.2f#short:%.2f'%(pLong,pShort)) 
    def closePosition(self):
        if(self.longPosition is not None and self.sellSignal == True):
            self.info("onBars().Status info,before exitMarket(), LONG POSITION to close %.2f" 
                      % (self.longPosition.getShares()))                                    
            self.longPosition.exitMarket()
        if(self.shortPosition is not None and self.buySignal == True):
            self.info("onBars().Status info,before exitMarket(), SHORT POSITION to close %.2f" 
                    % (self.shortPosition.getShares()))  
            self.shortPosition.exitMarket()          
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
    def __analise(self):
        dataForCandle = self.dataCenter.getCandleData(dataProvider = self.dataProvider,dataStorage = self.storageType,dataPeriod = self.period,
                                                 symbol = self.instrument,dateStart=self.timeFrom,dateEnd = self.timeTo)     
        self.analyzer.analyze(self.result,dataForCandle,InKLine = self.InKLine)            
    def run(self,timeFrom = None,timeTo = None):
        self.initEa(timeFrom = timeFrom,timeTo = timeTo)
        
        self.initIndicators()
        #self.strat.setUseAdjustedValues(False)
        
        self.initAnalyzer()      
        
        strategy.BacktestingStrategy.run(self)
        
        buy = self.getBuy()
        sell = self.getSell()

        portfolio_value = self.getPortfolio()
        position_volume = self.getPositionVolume()
        position_cost = self.getPositionCost()
        position_pnl = self.getPositionPnl()

        self.result = pd.DataFrame({'position_volume':list(position_volume),'position_cost':list(position_cost),
                               'position_pnl':list(position_pnl),
                               'buy':list(buy),'sell':list(sell),'portfolio_value':list(portfolio_value)},
                              columns=['position_volume','position_cost','position_pnl','buy','sell','portfolio_value'],
                              index=position_volume.getDateTimes())
        
        
        
        self.addIndicators()
        #------------------------------------
    
        if(self.toPlot):
            self.__analise()
            
            
        return self.result            
    #mid from ea
    #----------------------------------------------------------------------
    def summary(self):
        return "from %s to %s:returns:%.2f%%,sharpe:%.2f,MaxDrawdown:%.2f%%,Longest drawdown duration:(%s)" % (str(self.timeFrom),str(self.timeTo),
                                                                                                               self.returnsAnalyzer.getCumulativeReturns()[-1] * 100,
                                                                                                               self.sharpeRatioAnalyzer.getSharpeRatio(0.05),
                                                                                                               self.drawdownAnalyzer.getMaxDrawDown() * 100,
                                                                                                               self.drawdownAnalyzer.getLongestDrawDownDuration())
    def detail(self):
        """"""        
        print "-------------------------------------------------------------------------"
        print "Final portfolio value: $%.2f" % self.getResult()
        print "Cumulative returns: %.2f %%" % (self.returnsAnalyzer.getCumulativeReturns()[-1] * 100)
        print "Sharpe ratio: %.2f" % (self.sharpeRatioAnalyzer.getSharpeRatio(0.05))
        print "Max. drawdown: %.2f %%" % (self.drawdownAnalyzer.getMaxDrawDown() * 100)
        print "Longest drawdown duration: (%s)" % (self.drawdownAnalyzer.getLongestDrawDownDuration())

        print
        print "Total trades: %d" % (self.tradesAnalyzer.getCount())
        if self.tradesAnalyzer.getCount() > 0:
            profits = self.tradesAnalyzer.getAll()
            print "Avg. profit: $%2.f" % (profits.mean())
            print "Profits std. dev.: $%2.f" % (profits.std())
            print "Max. profit: $%2.f" % (profits.max())
            print "Min. profit: $%2.f" % (profits.min())
            returns = self.tradesAnalyzer.getAllReturns()
            print "Avg. return: %2.f %%" % (returns.mean() * 100)
            print "Returns std. dev.: %2.f %%" % (returns.std() * 100)
            print "Max. return: %2.f %%" % (returns.max() * 100)
            print "Min. return: %2.f %%" % (returns.min() * 100)

        print
        print "Profitable trades: %d" % (self.tradesAnalyzer.getProfitableCount())
        if self.tradesAnalyzer.getProfitableCount() > 0:
            profits = self.tradesAnalyzer.getProfits()
            print "Avg. profit: $%2.f" % (profits.mean())
            print "Profits std. dev.: $%2.f" % (profits.std())
            print "Max. profit: $%2.f" % (profits.max())
            print "Min. profit: $%2.f" % (profits.min())
            returns = self.tradesAnalyzer.getPositiveReturns()
            print "Avg. return: %2.f %%" % (returns.mean() * 100)
            print "Returns std. dev.: %2.f %%" % (returns.std() * 100)
            print "Max. return: %2.f %%" % (returns.max() * 100)
            print "Min. return: %2.f %%" % (returns.min() * 100)

        print
        print "Unprofitable trades: %d" % (self.tradesAnalyzer.getUnprofitableCount())
        if self.tradesAnalyzer.getUnprofitableCount() > 0:
            losses = self.tradesAnalyzer.getLosses()
            print "Avg. loss: $%2.f" % (losses.mean())
            print "Losses std. dev.: $%2.f" % (losses.std())
            print "Max. loss: $%2.f" % (losses.min())
            print "Min. loss: $%2.f" % (losses.max())
            returns = self.tradesAnalyzer.getNegativeReturns()
            print "Avg. return: %2.f %%" % (returns.mean() * 100)
            print "Returns std. dev.: %2.f %%" % (returns.std() * 100)
            print "Max. return: %2.f %%" % (returns.max() * 100)
            print "Min. return: %2.f %%" % (returns.min() * 100)    
        print "-------------------------------------------------------------------------"
    def initAnalyzer(self):
        from pyalgotrade.stratanalyzer import sharpe
        from pyalgotrade.stratanalyzer import returns
        from pyalgotrade.stratanalyzer import drawdown
        from pyalgotrade.stratanalyzer import trades        
        # 1.0) 策略结果
        self.returnsAnalyzer = returns.Returns()
        # 1.1) 夏普比率 
        self.sharpeRatioAnalyzer = sharpe.SharpeRatio()
        # 1.2) 
        self.drawdownAnalyzer = drawdown.DrawDown()
        # 1.3)
        self.tradesAnalyzer = trades.Trades()     
        
        self.attachAnalyzer(self.sharpeRatioAnalyzer)
        self.attachAnalyzer(self.returnsAnalyzer)    
        self.attachAnalyzer(self.tradesAnalyzer)   
        self.attachAnalyzer(self.drawdownAnalyzer)    