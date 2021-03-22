from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
import datetime
import sys      # To find out the script name (in argv[0])
import os
from color import Color
from base_strategy import BaseStrategies

os.system("cls")
print()



class EthereumStrategy(BaseStrategies):
    def __init__(self):
        super(EthereumStrategy, self).__init__()


    # region [blue]
    def macd_strategy(self):
        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if not self.order:
            # Check if we are in the market
            if not self.position:
                if self.macd_histogram[0] >= 0:
                    self.order    = self.buy()
            else:
                if self.macd_histogram[0] < -3:
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
        
        self.macd_strategy()
    # end region  



def run_backtesting(filename):
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(EthereumStrategy)

    # modpath  = os.path.dirname(os.path.abspath(sys.argv[0]))
    # datapath = os.path.join(modpath, filename)

    # start_year = 2017
    # start_month = 3
    # start_day   = 15

    # end_year  = 2021
    # end_month = 3
    # end_day   = 19

    # Create a Data Feed
    # data = bt.feeds.YahooFinanceCSVData(
    #         dataname=datapath,
    #         fromdate=datetime.datetime(start_year, start_month, start_day),
    #         todate=datetime.datetime(end_year, end_month, end_day),
    #         reverse=False)

    data = bt.feeds.GenericCSVData(
        timeframe=bt.TimeFrame.Minutes,
        compression=5,
        dataname='ETHUSD.txt',
        # fromdate=datetime.datetime(2017, 3, 15),
        # todate=datetime.datetime(2021, 3, 19),
        nullvalue=0,
        dtformat=('%Y-%m-%d'),
        datetime=0,
        open=1,
        high=2,
        low=3,
        close=4,
        volume=6,
        openinterest=-1
    )


    # First add the original data - smaller timeframe
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
    cerebro.run(runonce=False)
    # cerebro.run()

    # Print out the final result
    print()
    print(Color.WARNING + "Starting Portfolio Value:    ${:,.2f}".format(starting_cash) + Color.ENDC)
    print(Color.OKGREEN + Color.UNDERLINE + 'Final Portfolio Value:       ${:,.2f}'.format(cerebro.broker.getvalue()) + Color.ENDC)

    # plot the results
    cerebro.plot()    




if __name__ == '__main__':
    filename = 'C:\\Users\\Rory Glenn\\Documents\\python_repos\\Stocks\\BackTesting\\ETH-USD.txt'
    run_backtesting(filename)
