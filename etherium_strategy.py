from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
import datetime
import sys      # To find out the script name (in argv[0])
import os
from time import time
from color import Color

from base_strategy import BaseStrategies, print_time_elapsed

os.system("cls")
print("\n\n")
print("#"*60)

on_or_off = []

rand_num =[]

"""
Or table
T T = T
T F = T
F T = T
F F = F

T T = T
T F = T
F T = F  ![(1 == F) and (2 == T)]
F F = T

T T = F
T F = F
F T = T
F F = F

"""


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

        current_price = self.dataclose[0]

        if not self.order:
            if not self.position:
                # if self.ema_very_short[0] > self.ema_short[0]:
                    if self.ema_short[0] > self.ema_long[0] + self.ema_long[0] * 0.004 or self.rsi < 21:
                        self.order    = self.buy()
                        self.buyprice = self.dataclose[0]
            else:
                if self.macd_histogram[0] < -3.6 or self.macd_histogram[0] > 5:
                    self.order = self.sell(exectype=bt.Order.StopTrail, trailamount=0.02)

        self.prev_ema_short = self.ema_short[0]
    # end region



    # TIMM ![(1 == F) and (2 == T)]
    def hybrid_strategy_optimizer(self):
        global on_or_off
        
        ema_line_clear = rand_num[0]
        rsi_thres      = rand_num[1]

        if not self.order:
            if not self.position:
                # buying?
                # not [( () == False ) and (on_or_off[] == True)]
                if  not (((self.ema_very_short[0] > self.ema_short[0])                                                   == False) and (on_or_off[0] == True)) and \
                    not (((self.ema_short[0] > self.ema_long[0] + self.ema_long[0] * rsi_thres)                          == False) and (on_or_off[1] == True)) and \
                    not (((self.rsi < rsi_thres)                                                                         == False) and (on_or_off[2] == True)) and \
                    not (((self.ema_short[0] > self.ema_long[0] + self.ema_long[0] * rsi_thres or self.rsi < rsi_thres ) == False) and (on_or_off[3] == True)) and \
                    not (((self.macd_histogram[0] >= 0)                                                                  == False) and (on_or_off[4] == True)) :
                        self.order    = self.buy()
                        self.buyprice = self.dataclose[0]
            else:
                if self.macd_histogram[0] < -3.6 or \
                   self.macd_histogram[0] > 5:
                   self.order = self.sell(exectype=bt.Order.StopTrail, trailamount=0.02)

        self.prev_ema_short = self.ema_short[0]


    # region [red]
    def next(self):
        """
        Possible strategies
            self.buy_and_hold()
            self.macd_strategy()
            self.rsi_strategy()
            self.ppsr()
            self.hybrid_strategy()
            self.moving_averages()
            self.exponential_averages()
        """

        # self.buy_and_hold()
        # self.stochastic_slow()
        # self.stochastic_fast()
        # self.rsi_strategy()
        # self.macd_strategy()
        # self.hybrid_strategy()
        self.hybrid_strategy_optimizer()
    # end region



def run_backtesting():
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(EthereumStrategy)

    # data = bt.feeds.GenericCSVData(
    #     timeframe=bt.TimeFrame.Days,
    #     # compression=5,
    #     dataname='ETH-USD.csv',
    #     nullvalue=0,
    #     dtformat=('%Y-%m-%d'),
    #     datetime=0,
    #     open=1,
    #     high=2,
    #     low=3,
    #     close=4,
    #     volume=6,
    #     openinterest=-1
    # )

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
            
            reverse=False)


    cerebro.adddata(data)

    # Set our desired cash start
    starting_cash = 1000.0
    cerebro.broker.setcash(starting_cash)

    # Add a FixedSize sizer according to the stake
    cerebro.addsizer(bt.sizers.AllInSizer)

    binance_fixed_trade_fee = 0.00075
    relative_trade_fee = cerebro.broker.getvalue() * binance_fixed_trade_fee
    cerebro.broker.setcommission(commission=relative_trade_fee, margin=True)    

    # Run over everything
    # cerebro.run(runonce=False)
    cerebro.run()

    # Print out the final result
    #print()
    #print(Color.WARNING + "Starting Portfolio Value:    ${:,.2f}".format(starting_cash) + Color.ENDC)
    #print(Color.OKGREEN + Color.UNDERLINE + 'Final Portfolio Value:       ${:,.2f}'.format(cerebro.broker.getvalue()) + Color.ENDC)
    return cerebro.broker.getvalue()
    # plot the results
    # cerebro.plot()    



if __name__ == '__main__':
    
    start_time = time()
    
    # (17*100)*20

    max = 0
    for ema_line_clear in range(0, 21):
        for rsi_thres in range(0, 101):
            print('.', end='')
            for i in range(17):
                rand_num  = [ema_line_clear*.001, rsi_thres]
                on_or_off = [int(i//16)%2,int(i//8)%2,int(i//4)%2,int(i//2)%2,int(i//1)%2]
                
                number = run_backtesting()

                if number > max:
                    print(on_or_off, rand_num)
                    print(str(number) + "\n")
                    max = number

    print_time_elapsed(start_time)
                