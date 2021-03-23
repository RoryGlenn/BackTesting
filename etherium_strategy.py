from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
import datetime
import sys      # To find out the script name (in argv[0])
import os
from time import time
from color import Color

from base_strategy import BaseStrategies, print_time_elapsed

os.system("cls")
print()



class EthereumStrategy(BaseStrategies):
    
    def __init__(self):
        super(EthereumStrategy, self).__init__()


    # region [blue]
    def macd_day_strategy(self):
        if not self.order:
            if not self.position:
                if self.macd_histogram[0] >= 0:
                    self.order    = self.buy()
            else:
                if self.macd_histogram[0] < -3:
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
        if not self.order:
            if not self.position:
                if self.ema_short[0] > self.ema_long[0] + self.ema_long[0] * 0.004 or self.rsi < 20:
                    self.order    = self.buy()
                    self.buyprice = self.dataclose[0]
            else:
                if self.macd_histogram[0] < -3.6 or self.macd_histogram[0] > 5 :
                    self.order = self.sell(exectype=bt.Order.StopTrail, trailamount=0.02)
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
            self.moving_averages()
            self.exponential_averages()
        """

        # self.buy_and_hold()
        # self.hybrid_strategy()
        # self.stochastic_slow()
        # self.stochastic_fast()

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
            # 
            fromdate=datetime.datetime(2017, 8, 7),
            todate=datetime.datetime(2018, 3, 19),

            # slice 1
            # fromdate=datetime.datetime(2017, 1, 11),
            # todate=datetime.datetime(2018, 1, 11),

            # slice 2
            # fromdate=datetime.datetime(2018, 1, 11),
            # todate=datetime.datetime(2019, 1, 11),

            # slice 3
            # fromdate=datetime.datetime(2019, 1, 11),
            # todate=datetime.datetime(2020, 1, 11),

            # slice 4
            # fromdate=datetime.datetime(2020, 1, 11),
            # todate=datetime.datetime(2021, 1, 11),            
            
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
    print()
    print(Color.WARNING + "Starting Portfolio Value:    ${:,.2f}".format(starting_cash) + Color.ENDC)
    print(Color.OKGREEN + Color.UNDERLINE + 'Final Portfolio Value:       ${:,.2f}'.format(cerebro.broker.getvalue()) + Color.ENDC)

    # plot the results
    cerebro.plot()    



if __name__ == '__main__':
    start_time = time()
    run_backtesting()
    print_time_elapsed(start_time)
