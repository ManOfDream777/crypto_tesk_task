import time
import requests

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from binance.um_futures import UMFutures
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

gwei_price_in_usd = 0.00000169
transaction_cost = 21000
previous_coeff_list = [0]
previous_price_list = [0]
um_futures_client = UMFutures()

"""
1 Gwei = 0.00000169 USD
"""

def _get_eth_gas_price() -> float:
    """ Находит цену газа в Gwei """
    ua = UserAgent()
    req = requests.get('https://etherscan.io/gastracker', headers={'user-agent': ua.random, 'Content-Type': 'text/html'})
    soup = BeautifulSoup(req.text, 'html.parser')
    price = soup.find('span', attrs={'id':'ContentPlaceHolder1_ltGasPrice'})
    if price is None:
        price = soup.find('span', attrs={'id':'spanLowPrice'})
    return float(price.text)

def _get_real_future_eth_price() -> float:
    return float(um_futures_client.ticker_price("ETHUSDT")['price'])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    while True:
        eth_price = _get_real_future_eth_price()
        gas_price = _get_eth_gas_price()
        new_eth_price = gas_price * transaction_cost * gwei_price_in_usd
        coeff = eth_price / new_eth_price
        one_percent = coeff * 0.01
        previous_coeff = previous_coeff_list[0]
        previous_price = previous_price_list[0]
        if previous_price == 0:
            previous_price_list[0] = new_eth_price
            continue

        if coeff > previous_coeff + one_percent:
            previous_coeff_list[0] = coeff
            previous_price_list[0] = new_eth_price
            response = f'Произошло понижение цены. \nПредыдущая цена: {round(previous_price, 2)}$. \nНовая цена: {round(new_eth_price, 2)}$.'
            await update.message.reply_text(response)

        elif coeff < previous_coeff + one_percent:
            if previous_price == new_eth_price:
                continue
            previous_coeff_list[0] = coeff
            previous_price_list[0] = new_eth_price
            response = f'Произошло повышение цены. \nПредыдущая цена: {round(previous_price, 2)}$. \nНовая цена: {round(new_eth_price, 2)}$.'
            await update.message.reply_text(response)
        
        time.sleep(1)
    
app = ApplicationBuilder().token("bot_token").build()

app.add_handler(CommandHandler("start", start))

app.run_polling()