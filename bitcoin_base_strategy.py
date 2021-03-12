import datetime  # For datetime objects
import os.path  # To manage paths
import sys      # To find out the script name (in argv[0])
import backtrader as bt
from os import system
system("cls")

"""
base_strategy.py 

Used as a benchmark for all future strategies.
Simply buys and holds the S&P 500 with $1,000
from (1993, 1, 29) to (2021, 3, 5).

Final Portfolio Value: $14,405.74
Percent gained:        %1,440.60

Make sure your strategy can beat this!

"""


class BaseStrategy(bt.Strategy):
    params = (('maperiod', 15),)

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def buy_and_hold(self):
        if not self.position:
            self.log('BUY CREATE, %.2f' % self.dataclose[0])
            self.order = self.buy()
            self.buyprice = self.dataclose[0]

    def next(self):
        self.buy_and_hold()


if __name__ == '__main__':

    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(BaseStrategy)

    # Datas are in a subfolder of the samples. Need to find where the script is
    # because it could have been called from anywhere
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(modpath, 'BTC-USD.csv')

    # Create a Data Feed
    data = bt.feeds.YahooFinanceCSVData(
        dataname=datapath,
        fromdate=datetime.datetime(1993, 1, 29),
        todate=datetime.datetime(2021, 3, 5),
        reverse=False)

    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Set our desired cash start
    starting_cash = 1000.0
    cerebro.broker.setcash(starting_cash)

    # Add a FixedSize sizer according to the stake
    cerebro.addsizer(bt.sizers.AllInSizer)

    # Set the commission
    cerebro.broker.setcommission(commission=0.0)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()

    percent_gained = (cerebro.broker.getvalue() / starting_cash) * 100

    # Print out the final result
    print('Final Portfolio Value: ${:,.2f}'.format(cerebro.broker.getvalue()))
    print("Percent gained:        %{:,.2f}".format(round(percent_gained, 1)))

    # Plot the result
    cerebro.plot()
