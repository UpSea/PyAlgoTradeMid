# -*- coding: utf-8 -*-
from pyalgotrade import strategy

from pyalgotrade.broker import backtesting
from pyalgotrade.broker import fillstrategy

from pyalgotrade.technical import ma
from pyalgotrade.technical import cross
from pyalgotrade.dataseries import SequenceDataSeries
from pyalgotrade.dataseries import DEFAULT_MAX_LEN
import pandas as pd
import datetime as dt

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
    
    def getFeedNew(self,timeFrom=None,timeTo=None):
        '''mid should not be named the same with base class'''
        import os,sys        
        xpower = os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir,os.pardir,os.pardir,'midProjects','histdata'))
        sys.path.append(xpower)
        
        import dataCenter as dataCenter            
        self.dataCenter = dataCenter.dataCenter()           
        feed = self.dataCenter.getFeedForPAT(dataProvider = self.dataProvider,storageType = self.storageType,instruments = self.instruments,
                                               period=self.period,timeTo = timeTo,timeFrom=timeFrom)        
        return feed      
    
    
    
    def initEa(self,timeFrom=None,timeTo=None):
        self.results = {}
        feed = self.getFeedNew(timeFrom = timeFrom,timeTo = timeTo)
        self.mid_DEFAULT_MAX_LEN = 10 * DEFAULT_MAX_LEN
        mid_DEFAULT_MAX_LEN = self.mid_DEFAULT_MAX_LEN
        
        #mid set init cash
        cash_or_brk = 1000000
        volumeLimit = 0.5       #mid used to calculate available volume for an order: availableVolume = volumeLeft * volumeLimit
        #mid set fillstrategy
        fillStrategy = fillstrategy.DefaultStrategy(volumeLimit = volumeLimit)
        
        broker = backtesting.Broker(cash_or_brk, feed)
        broker.setFillStrategy(fillStrategy)
        #mid init base
        strategy.BacktestingStrategy.__init__(self, feed,broker)
        
        #mid 计算ma将使用当天的收盘价格计算
        #mid 1)
        self.closePrices = {}
        self.longPosition = {}
        self.shortPosition = {}
        self.buySignal = {}
        self.sellSignal = {}        
        self.timeFrom = timeFrom
        self.timeTo = timeTo        
        #mid follow vars will be used only this class
        self.__portfolio_value = SequenceDataSeries(maxLen = mid_DEFAULT_MAX_LEN)
        self.__available_cash =  SequenceDataSeries(maxLen = mid_DEFAULT_MAX_LEN)
        self.__curLongPositionCost = {}         #mid init position value
        self.__curShortPositionCost = {}        #mid init position value
        
        self.__position_volume = {}         #mid 当前持有头寸数量
        self.__position_cost = {}           #mid 当前持有头寸开仓成本
        self.__position_pnl = {}            #mid 当前持有头寸价值
        self.__position_value = {}
        self.__buy = {}
        self.__sell = {}    
        
        for instrument in self.instruments:
            dataSeries = feed[instrument]
            
            
            dataSeries.setMaxLen(mid_DEFAULT_MAX_LEN)       
            closeSeries = dataSeries.getCloseDataSeries()
            #mid 2)
            prices = closeSeries
            prices.setMaxLen(mid_DEFAULT_MAX_LEN)        
            
            #mid follow vars will be used in subclass
            self.closePrices[instrument] = prices
            self.longPosition[instrument] = None
            self.shortPosition[instrument] = None
            self.buySignal[instrument] = False
            self.sellSignal[instrument] = False

            #mid follow vars will be used only this class
            self.__curLongPositionCost[instrument] = 0                                                      #mid init position value
            self.__curShortPositionCost[instrument] = 0                                                      #mid init position value
            self.__position_volume[instrument] = SequenceDataSeries(maxLen = mid_DEFAULT_MAX_LEN)       #mid 当前持有头寸数量
            self.__position_cost[instrument] = SequenceDataSeries(maxLen = mid_DEFAULT_MAX_LEN)         #mid 当前持有头寸开仓成本
            self.__position_pnl[instrument] = SequenceDataSeries(maxLen = mid_DEFAULT_MAX_LEN)          #mid 当前持有头寸价值
            self.__position_value[instrument] = SequenceDataSeries(maxLen = mid_DEFAULT_MAX_LEN)
            self.__buy[instrument] = SequenceDataSeries(maxLen = mid_DEFAULT_MAX_LEN)
            self.__sell[instrument] = SequenceDataSeries(maxLen = mid_DEFAULT_MAX_LEN) 
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
    def recordAccount(self):
        # record position      
        #######################################################################
        broker = self.getBroker()
        curTime = self.getCurrentDateTime()
        currentTime = self.getCurrentDateTime()
        cash = broker.getCash(includeShort=False)
        portfolio_value = broker.getEquity()               #mid 按close价格计算的权益
        
        
        
        print 
        self.info("onBars().recordAccount().Current time:%s"%(str(currentTime)))
        self.info("onBars().recordAccount().----portfolio value: %.2f" % (portfolio_value))
        self.info("onBars().recordAccount().----cash in portfolio: %.2f" % (cash))
        
        self.__portfolio_value.appendWithDateTime(currentTime,portfolio_value) 
        self.__available_cash.appendWithDateTime(currentTime,cash) 
        for instrument in self.instruments:

            share = broker.getShares(instrument)                #mid position is dict of share
            lastPrice = self.getLastPrice(instrument)  
            if(lastPrice is None):
                continue
            position_value = lastPrice*share
            if(position_value > 0):
                position_cost = self.__curLongPositionCost[instrument] 
            elif(position_value < 0):
                position_cost = self.__curShortPositionCost[instrument]
            else:
                position_cost = 0
                
            position_pnl = (position_value - position_cost)


            self.info("onBars().recordAccount().--------%s" % (instrument))
            self.info("onBars().recordAccount().--------share:%.2f" % (share))
            self.info("onBars().recordAccount().--------lastPrice:%.2f" % (lastPrice))
            
            self.info("onBars().recordAccount().--------mid calculated position value: %.2f" %(position_value))
            self.info("onBars().recordAccount().--------mid position cost: %.2f" %(position_cost))
           
            self.info("onBars().recordAccount().--------mid calculated postion pnl: %.2f" %(position_pnl))

            self.__position_volume[instrument].appendWithDateTime(currentTime,abs(share))  
            self.__position_cost[instrument].appendWithDateTime(currentTime,abs(position_cost))
            self.__position_pnl[instrument].appendWithDateTime(currentTime,position_pnl)
            self.__position_value[instrument].appendWithDateTime(currentTime,abs(position_value))  
            self.__buy[instrument].appendWithDateTime(currentTime,self.buySignal[instrument])              
            self.__sell[instrument].appendWithDateTime(currentTime,self.sellSignal[instrument]) 
            
            
    def getPortfolioValue(self):
        return self.__portfolio_value
    def getAvailableCash(self):
        return self.__available_cash
    def getCurInstrument(self):
        return self.curInstrument
    def getPositionValue(self,instrument):
        return self.__position_value[instrument]
    def getPositionVolume(self,instrument):
        return self.__position_volume[instrument] 
    def getPositionCost(self,instrument):
        return self.__position_cost[instrument]
    def getPositionPnl(self,instrument):
        return self.__position_pnl[instrument]

    def getBuy(self,instrument):
        return self.__buy[instrument]
    def getSell(self,instrument):
        return self.__sell[instrument]
    def onEnterOk(self, position):
        '''mid
        由于getEquity()返回的是依据当日close价格计算出来的权益
        所以，这个值不能作为持仓成本
        持仓成本需要以onEnterOk时bar的open价格计算
        由于经常有跳开现象，所以依据bar(n-1).close发出的market order，
        在bar(n).open执行时通常会有gap出现，表现在position_cost图上时就是持有成本离计划成本会有跳口，
        '''
        #mid 1)record the position cost
        instrument = position.getInstrument()
        feed = self.getFeed()
        bars = feed.getCurrentBars()
        bar = bars.getBar(instrument)
        openPrice = bar.getOpen()   
        closePrice = self.getLastPrice(instrument) #mid lastPrice == closePrice
        if(False):
            '''mid long+short
            计算获取instrument的净头寸
            long = 10,short = -5
            则position = 5
            '''
            share = self.getBroker().getShares(instrument)
        else:
            '''mid only long or short
            计算当前position代表的头寸
            如果当前为long，则求出long头寸并不考虑short
            long = 10,short = -5
            若position == long
            则此处求出 position=10
             '''
            share = position.getShares()
            
        if isinstance(position, strategy.position.LongPosition):
            self.__curLongPositionCost[instrument] = openPrice*share
            
        if isinstance(position, strategy.position.ShortPosition):
            self.__curShortPositionCost[instrument] = openPrice*share

        #mid 1.1) a example to show price gap
        planedCost = 100000
        if(planedCost - abs(self.__curLongPositionCost[instrument]) > 1000):
            '''mid 
            跳开gap导致的n-1 day计划持仓金额和n day实际持仓金额之间的差额
            以n-1day的close价格为依据计算share to open
            n-1 day close = 10
            n day open = 9.8

            如果是要open 100000元
            则原计划持有数量shares = 100000/10 = 10000
            
            实际持有成本 = 计划持有数量 × 实际open价格
               		= 10000 × 9.8 = 980000'''
            pass
                
        #mid 2)log account info after enterOKed.
        execInfo = position.getEntryOrder().getExecutionInfo()   
        portfolio = self.getResult()
        cash = self.getBroker().getCash()     
        print
        self.info("onEnterOk().symbol:%s" % (instrument))        
        self.info("onEnterOk().current available cash: %.2f,portfolio: %.2f." % (cash,portfolio))
        if isinstance(position, strategy.position.LongPosition):
            print str(self.__curLongPositionCost[instrument])+'='+str(share)+'*'+str(openPrice)
            self.info("onEnterOK().ExecutionInfo: %s,OPEN LONG %.2f at $%.2f" 
                      % (execInfo.getDateTime(),execInfo.getQuantity(),execInfo.getPrice())) 
        elif isinstance(position, strategy.position.ShortPosition):
            print str(self.__curShortPositionCost[instrument])+'='+str(share)+'*'+str(openPrice)
            self.info("onEnterOK().ExecutionInfo: %s,OPEN SHORT %.2f at $%.2f" 
                      % (execInfo.getDateTime(),execInfo.getQuantity(),execInfo.getPrice()))     



    def onEnterCanceled(self, position):
        instrument = position.getInstrument()
        
        self.info("onEnterCanceled().current available cash: %.2f." % (self.getBroker().getCash()))
        if isinstance(position, strategy.position.LongPosition):
            self.longPosition[instrument] = None
            self.info("onEnterCanceled().OPEN LONG cancled.")                                
        elif isinstance(position, strategy.position.ShortPosition):
            self.shortPosition[instrument] = None
            self.info("onEnterCanceled().OPEN SHORT cancled.")
    def onExitOk(self, position):        
        execInfo = position.getExitOrder().getExecutionInfo()     
        portfolio = self.getResult()
        cash = self.getBroker().getCash()
        instrument = position.getInstrument()
        
        self.info("onExitOk().instrument:%s." % (instrument))        
        self.info("onExitOk().current available cash: %.2f,portfolio: %.2f." % (cash,portfolio))

        if isinstance(position, strategy.position.LongPosition):
            self.longPosition[instrument] = None
            self.__curLongPositionCost[instrument] = 0
            
            
            
            self.info("onExitOk().ExecutionInfo: %s,CLOSE LONG %.2f at $%.2f" 
                      % (execInfo.getDateTime(),execInfo.getQuantity(),execInfo.getPrice()))                    
        elif isinstance(position, strategy.position.ShortPosition):
            self.shortPosition[instrument] = None
            self.__curShortPositionCost[instrument] = 0           
            self.info("onExitOk().ExecutionInfo: %s,CLOSE SHORT %.2f at $%.2f" 
                      % (execInfo.getDateTime(),execInfo.getQuantity(),execInfo.getPrice()))                    
    def onExitCanceled(self, position):
        # If the exit was canceled, re-submit it.
        if isinstance(position, strategy.position.LongPosition):
            self.longPosition[instrument] = None
        elif isinstance(position, strategy.position.ShortPosition):
            self.shortPosition[instrument] = None
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
        for instrument in self.instruments:
            if(self.longPosition[instrument] is not None and self.sellSignal[instrument] == True
               and not self.longPosition[instrument].exitActive()):
                print
                self.info("onBars().closePosition(), instrument:%s"  % (instrument))                                                    
                self.info("onBars().closePosition(), LONG POSITION to close %.2f"  % (self.longPosition[instrument].getShares()))                                    
                self.longPosition[instrument].exitMarket()
            if(self.shortPosition[instrument] is not None and self.buySignal[instrument] == True
               and not self.shortPosition[instrument].exitActive()):
                print
                self.info("onBars().closePosition(), instrument:%s"  % (instrument))                                                                    
                self.info("onBars().closePosition(), SHORT POSITION to close %.2f"  % (self.shortPosition[instrument].getShares()))  
                self.shortPosition[instrument].exitMarket()          
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
        if(self.shortAllowed):
            for instrument in self.instruments:
                self.curInstrument = instrument
                if(self.sellSignal[instrument] == True):
                    # Enter a buy market order. The order is good till canceled.
                    bar = self.getFeed().getLastBar(instrument)
                    volume = 0
                    lastClose = 0
                    if bar is not None:
                        volume = bar.getVolume() 
                        lastClose = bar.getClose()
                    shares = self.money.getShares(strat = self)
                    print
                    self.info("onBars().openPosition(), instrument %s" % (instrument))   
                    self.info("onBars().openPosition(), SHORT POSITION to open %.2f" % (shares))   
                    self.info("onBars().openPosition(), lastClose: %.2f,%.2f" % (self.getLastPrice(instrument),lastClose))  
                    self.info("onBars().openPosition(), need amount: %.2f" % (shares*self.getLastPrice(instrument)))  
                    self.info("onBars().openPosition(), available amount: %.2f." % (self.getBroker().getCash() ))                  
                    self.info("onBars().openPosition(), available volume: %.2f." % (volume))                  
                    self.shortPosition[instrument] = self.enterShort(instrument, shares, True)            
            
        if(self.longAllowed):
            for instrument in self.instruments:
                self.curInstrument = instrument
                if(self.buySignal[instrument] == True):
                    shares = self.money.getShares(strat = self)              
                    print
                    self.info("onBars().openPosition(), instrument %s" % (instrument))   
                    self.info("onBars().openPosition(), LONG POSITION to open %.2f" % (shares) )                
                    self.info("onBars().openPosition(), need amount: %.2f." % (shares*self.getLastPrice(instrument)))                  
                    self.info("onBars().openPosition(), available amount: %.2f." % (self.getBroker().getCash() ))                                    
                    self.longPosition[instrument] = self.enterLong(instrument, shares, True)
    def __analiseEachSymbol(self,instrument):
        dataForCandle = self.dataCenter.getCandleData(dataProvider = self.dataProvider,dataStorage = self.storageType,dataPeriod = self.period,
                                                 symbol = instrument,dateStart=self.timeFrom,dateEnd = self.timeTo)     
        self.analyzer.analyseEachSymbol(self.results[instrument],dataForCandle,InKLine = self.InKLine)
        
    def __analiseSummary(self):
        dataProvider = self.benchDataProvider
        instrument = self.benchSymbol
        dataForCandle = self.dataCenter.getCandleData(dataProvider = dataProvider,dataStorage = self.storageType,dataPeriod = self.period,
                                                 symbol = instrument,dateStart=self.timeFrom,dateEnd = self.timeTo)          
        self.analyzer.analyseSummary(self.result,dataForCandle)
    def run(self,timeFrom = None,timeTo = None):
        self.initEa(timeFrom = timeFrom,timeTo = timeTo)
        
        self.initIndicators()
        #self.strat.setUseAdjustedValues(False)
        
        self.initAnalyzer()      
        
        strategy.BacktestingStrategy.run(self)
        
        
        for instrument in self.instruments:
            buy = self.getBuy(instrument)
            sell = self.getSell(instrument)

            position_value = self.getPositionValue(instrument)
            position_volume = self.getPositionVolume(instrument)
            position_cost = self.getPositionCost(instrument)
            position_pnl = self.getPositionPnl(instrument)

            self.results[instrument] = pd.DataFrame({'position_volume':list(position_volume),'position_cost':list(position_cost),
                               'position_pnl':list(position_pnl),
                               'buy':list(buy),'sell':list(sell),'position_value':list(position_value)},
                              columns=['position_volume','position_cost','position_pnl','buy','sell','position_value'],
                              index=position_volume.getDateTimes())
            self.addIndicators(instrument)
            #------------------------------------
    
            if(self.toPlotEachSymbol):
                self.__analiseEachSymbol(instrument)
            
        if(self.toPlotSummary):
            portfolio_value = self.getPortfolioValue()
            available_cash = self.getAvailableCash()
            
            self.result = pd.DataFrame({'available_cash':list(available_cash),'portfolio_value':list(portfolio_value)},
                              columns=['available_cash','portfolio_value'],
                              index=portfolio_value.getDateTimes())
            self.__analiseSummary()
        return self.results            
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