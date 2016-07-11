# -*- coding: utf-8 -*-
import baseMoney
class moneyFixed(baseMoney.baseMoney):
    def __init__(self):
        self.initCash = 0
        self.openIndex = 0
    def getShares(self,strat = None):   
        curPrice = strat.getLastPrice(strat.getCurInstrument())        
        if(self.openIndex == 0):
            self.initCash = strat.getBroker().getCash()*0.2
            self.openIndex = self.openIndex + 1
            
        #shares = int(self.initCash/curPrice)
        shares = (self.initCash/curPrice)
        print
        strat.info("onBars().openPosition().moneyFixed().getShares().curPrice:%.3f"%(curPrice))           
        strat.info("onBars().openPosition().moneyFixed().getShares().money to invest:%.3f"%(self.initCash))           
        strat.info("onBars().openPosition().moneyFixed().getShares().shares to invest:%.3f"%(shares))           
        return shares