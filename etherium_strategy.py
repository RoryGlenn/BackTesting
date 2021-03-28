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



class EthereumStrategy(BaseStrategies):
    
    def __init__(self):
        super(EthereumStrategy, self).__init__()
        self.prev_ema_short = 0


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



    # TIMM ![(1 == F) and (2 == T)]
    def hybrid_strategy_optimizer(self):
        global on_or_off
        global rand_num

        macd_lower_threshold = rand_num[0]
        macd_upper_threshold = rand_num[1]

        if not self.order:
            if not self.position:
                if self.ema_short[0] > self.ema_long[0] + self.ema_long[0] * 0.04 or self.rsi < 21:
                        self.order    = self.buy()
                        self.buyprice = self.dataclose[0]
                else:
                    if not ((not (self.macd_histogram[0] < macd_lower_threshold) ) and (on_or_off[0])) and \
                       not ( not (self.macd_histogram[0] > macd_upper_threshold) ) and (on_or_off[1]):
                       self.order = self.sell(exectype=bt.Order.StopTrail, trailamount=0.02)


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
        # self.ppsr()
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
            dataname="data/ETH-USD.csv",

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

            # test slice
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
    # histogram_list = sorted(histogram_set)



    # cerebro.plot()
    return cerebro.broker.getvalue()



def run_hybrid_optimizer():
    global rand_num
    global on_or_off
    start_time = time()
    optimized_list = list()
    max = 0

    #  LOWER_THRESHOLD (-3.6),                     HIGHER_THRESHOLD (5)
    # if self.macd_histogram[0] < -3.6 or self.macd_histogram[0] > 5:

    # lower_threshold: -10.0, -9.9, -9.8, ...  , upper_threshold
    # (-10.0 + (.1 * i)) (i < upper)

    # upper_threshold: 10.0, 9.9, 9.8, ... , lower_threshold
    # 0.010, 0.011, 0.012, ... , 0.20 (190) (.01 + (.001 * i))
        
    # trail amount = 0.010, 0.011, 0.012, ... , 0.20 (190) (.01 + (.001 * i))


    for lower_thres in range(0, 200): # og: 0 - 200
        print_time_elapsed(start_time, Color.OKBLUE) 

        for upper_thres in range(lower_thres, 200): # og: 0 - 200      

            for i in range(2**2):
                rand_num  = [ (-10.0 + (.1 * lower_thres)), round((-10 + (.1 * upper_thres)), 2) ]
                on_or_off = [int(i//2)%2, int(i//1)%2]
                number = run_backtesting()
                
                if number > max:
                    print("Found: ", end='')
                    print_time_elapsed(start_time)
                    print(on_or_off, rand_num)
                    print(str(number) + "\n")
                    optimized_list.append(str(on_or_off) + str(rand_num) + "\n" + str(number) + "\n")
                    max = number


    print("FINAL----------")
    print_time_elapsed(start_time, Color.Red)
    for i in optimized_list:
        print(i) 



if __name__ == '__main__':
    print_header()
    run_hybrid_optimizer()
    # run_backtesting()
