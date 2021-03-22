from base_strategy import BaseStrategies, PivotPoints, get_total_backtested_years, run_backtesting
from color         import Color
from os            import system

import backtrader as bt
import datetime
import os.path
import sys


system("cls")
print()


class test_strat(BaseStrategies):
    def __init__(self):
        super(test_strat, self).__init__()


    # region [red]
    def next(self):
        # self.buy_and_hold()
        self.macd_strategy()
        # self.rsi_strategy()
        # self.ppsr()
        # self.hybrid_strategy()
        # self.moving_averages()
        # self.exponential_averages()
        
    # end region


def run_backtesting(filename):
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(test_strat)

    # Datas are in a subfolder of the samples. Need to find where the script is
    # because it could have been called from anywhere
    
    modpath  = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(modpath, filename)

    start_year  = 2014
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

    # First add the original data - smaller timeframe
    cerebro.adddata(data)

    # Set our desired cash start
    starting_cash = 1000.0
    cerebro.broker.setcash(starting_cash)

    # Add a FixedSize sizer according to the stake
    cerebro.addsizer(bt.sizers.AllInSizer)

    # Set the commission
    # cerebro.broker.setcommission(commission=0.0)

    binance_trade_fee = 0.00075
    relative_trade_fee = cerebro.broker.getvalue() * binance_trade_fee
    cerebro.broker.setcommission(commission=relative_trade_fee, margin=True)    

    # Run over everything
    cerebro.run()

    percent_gained           = (cerebro.broker.getvalue() / starting_cash) * 10
    average_percent_per_year = percent_gained / get_total_backtested_years(filename)

    # Print out the final result
    print()
    print(Color.WARNING + "Starting Portfolio Value:    ${:,.2f}".format(starting_cash) + Color.ENDC)
    print(Color.WARNING + 'Final Portfolio Value:       ${:,.2f}'.format(cerebro.broker.getvalue()) + Color.ENDC)

    if cerebro.broker.getvalue() < starting_cash:
        print(Color.OKGREEN + Color.BOLD + Color.UNDERLINE + "Total Percent gained:        %-{:,.2f}".format(round(percent_gained, 3)) + Color.ENDC)
        print("Average Percent Per Year:    %-{:,.2f}".format(average_percent_per_year))
    else:
        print(Color.OKGREEN + Color.BOLD + Color.UNDERLINE + "Total Percent gained:        %{:,.2f}".format(round(percent_gained, 3)) + Color.ENDC)
        print("Average Percent Per Year:    %{:,.2f}".format(average_percent_per_year))
    print("Total Backtested Years:      " + str(get_total_backtested_years(filename)))

    cerebro.plot()    



if __name__ == '__main__':
    filename = 'C:\\Users\\Rory Glenn\\Documents\\python_repos\\Stocks\\BackTesting\\BTC-USD.csv'
    run_backtesting(filename)
