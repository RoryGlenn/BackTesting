from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
import datetime
import sys      # To find out the script name (in argv[0])
import os
from color import Color
from base_strategy import BaseStrategies

os.system("cls")
print()



class BitcoinStrategy(BaseStrategies):
    def __init__(self):
        super(BitcoinStrategy, self).__init__()


    # region [blue]
    def macd_strategy(self):
        if not self.order:
            if not self.position:
                if self.macd_histogram[0] >= 0.10:
                    self.order    = self.buy()
            else:
                if self.macd_histogram[0] < 0.10:
                    self.order = self.sell(exectype=bt.Order.StopTrail, trailamount=0.02)

    # end region


    # region [blue]
    def hybrid_strategy(self):
        if not self.order:
            if not self.position:
                if self.ema_short[0] > self.ema_long[0] + self.ema_long[0] * 0.009 or self.rsi < 29:
                    self.order    = self.buy()
                    self.buyprice = self.dataclose[0]
            else:
                if self.ema_short[0] < self.ema_long[0] + self.ema_long[0] * 0.009:
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
        self.hybrid_strategy()
    # end region  



def run_backtesting(filename):
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(BitcoinStrategy)

    modpath  = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(modpath, filename)

    start_year  = 2017
    start_month = 3
    start_day   = 15

    end_year  = 2021
    end_month = 3
    end_day   = 19

    # Create a Data Feed
    data = bt.feeds.YahooFinanceCSVData(
            dataname=datapath,
            fromdate=datetime.datetime(start_year, start_month, start_day),
            todate=datetime.datetime(end_year, end_month, end_day),
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
    cerebro.run()

    # Print out the final result
    print()
    print(Color.WARNING + "Starting Portfolio Value:    ${:,.2f}".format(starting_cash) + Color.ENDC)
    print(Color.OKGREEN + Color.UNDERLINE + 'Final Portfolio Value:       ${:,.2f}'.format(cerebro.broker.getvalue()) + Color.ENDC)

    # plot the results
    cerebro.plot()    




if __name__ == '__main__':
    filename = 'C:\\Users\\Rory Glenn\\Documents\\python_repos\\Stocks\\BackTesting\\BTC-USD.csv'
    run_backtesting(filename)
