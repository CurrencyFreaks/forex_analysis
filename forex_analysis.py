import requests
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Avoid Tkinter GUI issues
import matplotlib.pyplot as plt
import mplfinance as mpf
import os

# ---------- CONFIG ----------
API_KEY = "c0cf4c51f1424ef483b76cbf83592864"  # <-- Your CurrencyFreaks API key
BASE_URL = "https://api.currencyfreaks.com/v2.0"
# ----------------------------

# Fetch supported currency symbols
def get_supported_currencies():
    url = f"{BASE_URL}/currency-symbols"
    response = requests.get(url)
    data = response.json()
    return data.get("currencySymbols", {})

currencies = get_supported_currencies()
print("Supported currencies (first 50 shown for brevity):")
for code, name in list(currencies.items())[:50]:
    print(f"{code} - {name}")

# ---------- USER INPUT ----------
base_currency = input("Enter base currency code (e.g., USD): ").upper()
symbol_currency = input("Enter symbol currency code (e.g., EUR): ").upper()
start_date = input("Enter start date (YYYY-MM-DD): ")
end_date = input("Enter end date (YYYY-MM-DD): ")

print("\nEndpoints:\n1 - Historical\n2 - Time Series\n3 - Fluctuation")
endpoint_choice = input("Choose endpoint (1/2/3): ")

print("\nOutput options:\n1 - Download CSV\n2 - Draw Chart")
output_choice = input("Choose output (1/2): ")

chart_type = None
if output_choice == "2":
    print("\nChart options:\n1 - Line Chart\n2 - Bar Chart\n3 - Candlestick Chart")
    chart_type = input("Choose chart type: ")

# ---------- API CALL ----------
def fetch_data():
    if endpoint_choice == "1":  # Historical
        dates = pd.date_range(start=start_date, end=end_date)
        all_data = []
        for d in dates:
            url = f"{BASE_URL}/rates/historical?apikey={API_KEY}&date={d.strftime('%Y-%m-%d')}&base={base_currency}&symbols={symbol_currency}"
            r = requests.get(url).json()
            rate = r.get("rates", {}).get(symbol_currency)
            all_data.append({"Date": d.strftime("%Y-%m-%d"), "Rate": float(rate) if rate else None})
        return pd.DataFrame(all_data)

    elif endpoint_choice == "2":  # Time Series
        url = f"{BASE_URL}/timeseries?apikey={API_KEY}&startDate={start_date}&endDate={end_date}&base={base_currency}&symbols={symbol_currency}"
        r = requests.get(url).json()
        data_list = r.get("historicalRatesList", [])
        all_data = [{"Date": d["date"], "Rate": float(d["rates"].get(symbol_currency, 0))} for d in data_list]
        return pd.DataFrame(all_data)

    elif endpoint_choice == "3":  # Fluctuation
        url = f"{BASE_URL}/fluctuation?apikey={API_KEY}&startDate={start_date}&endDate={end_date}&base={base_currency}&symbols={symbol_currency}"
        r = requests.get(url).json()
        rate_data = r.get("rateFluctuations", {}).get(symbol_currency, {})
        all_data = [{"Date": start_date,
                     "StartRate": float(rate_data.get("startRate", 0)),
                     "EndRate": float(rate_data.get("endRate", 0)),
                     "Change": float(rate_data.get("change", 0)),
                     "PercentChange": float(rate_data.get("percentChange", 0))}]
        return pd.DataFrame(all_data)

df = fetch_data()

# ---------- OUTPUT ----------
# CSV download
if output_choice == "1":
    filename = f"{base_currency}_{symbol_currency}_{start_date}_{end_date}.csv"
    df.to_csv(filename, index=False)
    print(f"CSV saved as {filename}")

# Chart output
elif output_choice == "2":
    if chart_type in ["1", "2"]:
        plt.figure(figsize=(12,6))

        # Handle tiny numbers automatically
        if endpoint_choice != "3" and df["Rate"].max() < 1:
            # Convert to reciprocal if rates are very small
            df["DisplayRate"] = 1 / df["Rate"]
            ylabel = f"{symbol_currency} per {base_currency}"
        else:
            df["DisplayRate"] = df.get("Rate", df.get("EndRate", df.get("Close", 0)))
            ylabel = "Rate"

        x = pd.to_datetime(df["Date"])
        y = df["DisplayRate"]

        if endpoint_choice == "3":  # Fluctuation chart
            plt.bar(x, y, color='orange', alpha=0.7)
            plt.title(f"{symbol_currency} Fluctuation ({base_currency})")
        else:
            if chart_type == "1":  # Line
                plt.plot(x, y, marker='o', color='blue', linewidth=2)
            else:  # Bar
                plt.bar(x, y, color='skyblue', alpha=0.7)
            plt.title(f"{base_currency} vs {symbol_currency}")

        plt.ylabel(ylabel)
        plt.xlabel("Date")
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.xticks(rotation=45)
        plt.tight_layout()
        filename = f"{base_currency}_{symbol_currency}_{start_date}_{end_date}.png"
        plt.savefig(filename)
        print(f"Chart saved as {filename}")

    elif chart_type == "3":  # Candlestick chart
        if endpoint_choice != "2":
            print("Candlestick chart only works for Time Series endpoint.")
        else:
            df_candle = df.copy()
            df_candle["Open"] = df_candle["Rate"]
            df_candle["Close"] = df_candle["Rate"]
            df_candle["High"] = df_candle["Rate"] * 1.01
            df_candle["Low"] = df_candle["Rate"] * 0.99
            df_candle.index = pd.to_datetime(df_candle["Date"])
            df_candle = df_candle[["Open","High","Low","Close"]]
            filename = f"{base_currency}_{symbol_currency}_{start_date}_{end_date}_candlestick.png"
            mpf.plot(df_candle, type='candle', style='charles', title=f"{base_currency} vs {symbol_currency}", volume=False, savefig=filename)
            print(f"Candlestick chart saved as {filename}")
