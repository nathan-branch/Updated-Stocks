# Nathan Branch 2023
# Stock Trading Display & Algorythm

import tkinter as tk
from tkinter import ttk
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import threading
import time

class TradingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Trading Algorithm GUI")

        # Load historical stock data from a CSV file
        self.data = pd.read_csv('AAPL.csv')

        # Initialize trading parameters
        self.initial_balance = 100000
        self.current_balance = self.initial_balance
        self.buy_threshold = 30
        self.sell_threshold = 70
        self.stop_loss = 5
        self.high_point = 0

        # Initialize data structures
        self.portfolio = {}
        self.trades_log = []

        # Initialize live stock data
        self.current_price = 0

        # Create Matplotlib figure and axis for stock graph
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.x_data, self.y_data = [], []
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack()

        # Labels for algorithm information
        self.balance_label = tk.Label(root, text=f'Initial Balance: {self.initial_balance:.2f}')
        self.balance_label.pack()
        self.current_balance_label = tk.Label(root, text=f'Current Balance: {self.current_balance:.2f}')
        self.current_balance_label.pack()

        # Create a control panel for setting trading parameters
        control_panel = ttk.LabelFrame(root, text="Trading Parameters")
        control_panel.pack(padx=10, pady=10)

        self.buy_threshold_label = ttk.Label(control_panel, text="Buy Threshold (RSI):")
        self.buy_threshold_label.grid(row=0, column=0)
        self.buy_threshold_entry = ttk.Entry(control_panel)
        self.buy_threshold_entry.grid(row=0, column=1)

        self.sell_threshold_label = ttk.Label(control_panel, text="Sell Threshold (RSI):")
        self.sell_threshold_label.grid(row=1, column=0)
        self.sell_threshold_entry = ttk.Entry(control_panel)
        self.sell_threshold_entry.grid(row=1, column=1)

        self.stop_loss_label = ttk.Label(control_panel, text="Stop Loss (%):")
        self.stop_loss_label.grid(row=2, column=0)
        self.stop_loss_entry = ttk.Entry(control_panel)
        self.stop_loss_entry.grid(row=2, column=1)

        update_params_button = ttk.Button(control_panel, text="Update Parameters", command=self.update_parameters)
        update_params_button.grid(row=3, columnspan=2)

        # Start updating the stock graph
        self.update_stock_graph()

        # Start a separate thread to fetch and update live stock data
        self.update_thread = threading.Thread(target=self.update_stock_data)
        self.update_thread.daemon = True
        self.update_thread.start()

        # Start the trading algorithm
        self.trading_thread = threading.Thread(target=self.trading_algorithm)
        self.trading_thread.daemon = True
        self.trading_thread.start()

    def update_parameters(self):
        try:
            self.buy_threshold = float(self.buy_threshold_entry.get())
            self.sell_threshold = float(self.sell_threshold_entry.get())
            self.stop_loss = float(self.stop_loss_entry.get())
        except ValueError:
            pass  # Handle invalid input

    def update_stock_data(self):
        while True:
            self.current_price = self.get_live_stock_price("AAPL")
            if self.current_price is not None:
                self.current_balance_label.config(text=f'Current Balance: {self.current_balance:.2f}')
            time.sleep(1)

    def get_live_stock_price(self, ticker):
        stock_data = yf.download(ticker, period="1s")
        if len(stock_data) > 0:
            return stock_data.iloc[-1]["Open"]
        return None

    def log_trade(self, action, date, price, shares):
        trade = f"{action} - Date: {date}, Price: {price}, Shares: {shares}"
        self.trades_log.append(trade)
        self.update_log()

    def update_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete('1.0', tk.END)
        self.log_text.insert(tk.END, "\n".join(self.trades_log))
        self.log_text.config(state=tk.DISABLED)

    def update_stock_graph(self):
        if self.current_price is not None:
            self.x_data.append(time.strftime('%H:%M:%S'))
            self.y_data.append(self.current_price)
            self.ax.clear()
            self.ax.plot(self.x_data, self.y_data, label='Live Data', color='blue')
            
            # Plot historical data from CSV file
            self.ax.plot(self.data['Date'], self.data['Close'], label='Historical Data', color='gray')
            
            self.ax.set_xlabel('Time')
            self.ax.set_ylabel('Stock Price')
            self.ax.set_title('Stock Price Comparison')
            self.ax.legend(loc='upper left')
            self.canvas.draw()
        self.root.after(1000, self.update_stock_graph)

    def trading_algorithm(self):
        while True:
            if self.current_price is not None and self.current_price != 0:
                if self.current_price < self.buy_threshold and self.current_balance > 0:
                    # Buy stock when the price is below the buy threshold
                    shares_to_buy = int(self.current_balance / self.current_price)
                    if shares_to_buy > 0:
                        cost = shares_to_buy * self.current_price
                        self.portfolio["AAPL"] = self.portfolio.get("AAPL", 0) + shares_to_buy
                        self.current_balance -= cost
                        self.log_trade("BUY", time.strftime('%Y-%m-%d %H:%M:%S'), self.current_price, shares_to_buy)
                elif self.current_price > self.sell_threshold and "AAPL" in self.portfolio:
                    # Sell stock when the price is above the sell threshold
                    shares_to_sell = self.portfolio["AAPL"]
                    sale_amount = shares_to_sell * self.current_price
                    self.current_balance += sale_amount
                    del self.portfolio["AAPL"]
                    self.log_trade("SELL", time.strftime('%Y-%m-%d %H:%M:%S'), self.current_price, shares_to_sell)
                elif self.current_price < self.stop_loss and "AAPL" in self.portfolio:
                    # Implement a stop-loss mechanism
                    shares_to_sell = self.portfolio["AAPL"]
                    sale_amount = shares_to_sell * self.current_price
                    self.current_balance += sale_amount
                    del self.portfolio["AAPL"]
                    self.log_trade("STOP LOSS", time.strftime('%Y-%m-%d %H:%M:%S'), self.current_price, shares_to_sell)
            time.sleep(1)

if __name__ == "__main__":
    root = tk.Tk()
    root.configure(bg='#E0E0E0')
    app = TradingApp(root)
    root.mainloop()