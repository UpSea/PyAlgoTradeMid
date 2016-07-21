# -*- coding: utf-8 -*-
import baseMoney
class moneyFixedRatio(baseMoney.baseMoney):
    def __init__(self):
        self.lastAllocatedCash = 0
    def getShares(self,strat = None):   
        curPrice = strat.getLastPrice(strat.getCurInstrument())        
        allocatedCash = strat.getResult() * 0.15
        if(allocatedCash > self.lastAllocatedCash):
            self.lastAllocatedCash = allocatedCash
        print str(strat.getResult())
        shares = (self.lastAllocatedCash/curPrice)
        print
        strat.info("onBars().openPosition().moneyFixedRatio().getShares().curPrice:%.3f"%(curPrice))           
        strat.info("onBars().openPosition().moneyFixedRatio().getShares().money to invest:%.3f"%(allocatedCash))           
        strat.info("onBars().openPosition().moneyFixedRatio().getShares().shares to invest:%.3f"%(shares))           
        return shares