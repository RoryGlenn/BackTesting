from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
import datetime
import os
from time import time
from color import Color
import talib as ta
from base_strategy import BaseStrategies, print_time_elapsed


on_or_off = []
rand_num  = []
histogram_set  = set()
histogram_list = list()

ema_short = 0
ema_long  = 0


class EthereumStrategy(BaseStrategies):
    
    def __init__(self):
        super(EthereumStrategy, self).__init__()
        self.prev_ema_short = 0


    # region [blue]
    def rsi_strategy(self):
        # Simply log the closing price of the series from the reference

        current_price = self.dataclose[0]

        if not self.order:
            if not self.position:
                if self.rsi <= 35:
                    self.order         = self.buy()
                    self.buyprice      = self.dataclose[0]
                    self.price_to_sell = self.buyprice + (self.buyprice * 0.05)
            else:
                if self.rsi >= 65:
                    self.order = self.sell(exectype=bt.Order.StopTrail, trailamount=0.02)
    # end region


    # region [blue]
    def macd_day_strategy(self):
        if not self.order:
            if not self.position:
                if self.macd_histogram[0] >= 0:
                    self.order    = self.buy()
            else:
                if self.macd_histogram[0] < 0:
                    self.order = self.sell(exectype=bt.Order.StopTrail, trailamount=0.02)

    # end region

   
    # region [blue]
    def exponential_averages(self):
        if not self.order:
            if not self.position:
                if self.ema_short[0] > self.ema_long[0] + (self.ema_long[0] * 0.005):
                    self.order         = self.buy()
                    self.buyprice      = self.dataclose[0]
            else:
                if self.ema_short[0] < self.ema_long[0]:
                    self.order = self.sell(exectype=bt.Order.StopTrail, trailamount=0.02) 
    # end region



    # region [blue]
    def hybrid_strategy(self):

        # current_price = self.dataclose[0]
        global histogram_list
        
        histogram_list.append(self.macd_histogram[0])

        if not self.order:
            if not self.position:
                # if self.ema_very_short[0] > self.ema_short[0]:
                    if self.ema_short[0] > self.ema_long[0] + self.ema_long[0] * 0.004 or self.rsi < 21:
                        self.order    = self.buy()
                        self.buyprice = self.dataclose[0]
            else:
                if self.macd_histogram[0] < -3.6 or self.macd_histogram[0] > 5:
                    global histogram_set
                    histogram_set.add(self.macd_histogram[0])
                    self.order = self.sell(exectype=bt.Order.StopTrail, trailamount=0.02)

        self.prev_ema_short = self.ema_short[0]
    # end region






    # region [red]
    def next(self):
        
        """
        Possible strategies
            self.buy_and_hold()
            self.macd_strategy()
            self.rsi_strategy()
            self.ppsr()
            self.hybrid_strategy()
            self.exponential_averages()
            self.hybrid_strategy_optimizer()
        """

        # self.buy_and_hold()
        # self.macd_strategy()
        # self.rsi_strategy()
        # self.exponential_averages()
        self.hybrid_strategy()
        # self.hybrid_strategy_optimizer()
    # end region


def print_header():
    os.system("cls")
    print("\n\n")
    print("#"*60)
    print(" "*20 + "START OF PROGRAM")
    print("#"*60)
    print()


def run_backtesting():
    cerebro = bt.Cerebro()
    cerebro.addstrategy(EthereumStrategy)

    data = bt.feeds.YahooFinanceCSVData(
            dataname="data/MRNA.csv",

            # Everything
            # fromdate=datetime.datetime(2015, 8, 7),
            # todate=datetime.datetime(2021, 3, 19),

            # normalized
            fromdate=datetime.datetime(2017, 8, 7),
            todate=datetime.datetime(2021, 3, 19),

            # slice 1
            # fromdate=datetime.datetime(2017, 5, 30),
            # todate=datetime.datetime(2018, 5, 30),

            # slice 2
            # fromdate=datetime.datetime(2018, 5, 30),
            # todate=datetime.datetime(2019, 5, 30),

            # slice 3
            # fromdate=datetime.datetime(2019, 5, 30),
            # todate=datetime.datetime(2020, 5, 30),

            # slice 4
            # fromdate=datetime.datetime(2020, 5, 30),
            # todate=datetime.datetime(2021, 5, 30),

            # small test slice
            # fromdate=datetime.datetime(2021, 1, 1),
            # todate=datetime.datetime(2021, 3, 27),
            
            reverse=False)

    starting_cash           = 1000.0
    binance_fixed_trade_fee = 0.00075

    cerebro.adddata(data)
    cerebro.broker.setcash(starting_cash)
    cerebro.addsizer(bt.sizers.AllInSizer)

    relative_trade_fee = cerebro.broker.getvalue() * binance_fixed_trade_fee
    cerebro.broker.setcommission(commission=relative_trade_fee, margin=True)    
    cerebro.run()


    # Print out the final result
    print()
    print(Color.WARNING + "Starting Portfolio Value:    ${:,.2f}".format(starting_cash) + Color.ENDC)
    print(Color.OKGREEN + Color.UNDERLINE + 'Final Portfolio Value:       ${:,.2f}'.format(cerebro.broker.getvalue()) + Color.ENDC)

    cerebro.plot()






if __name__ == '__main__':
    print_header()
    run_backtesting()
