import yfinance as yf
import seaborn as sns
from datetime import datetime, date
import matplotlib.pyplot as plt
import pandas as pd
from bs4 import BeautifulSoup
import requests
import pymysql
import sqlalchemy as alch
from getpass import getpass
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

def getSymbols():
    """
    This function asks the user to provide the symbols (indexes or ISIN) for which would like to get the analysis. If the symbol does not exists in yfinance, will not consider it, and will keep 
    asking until either the user provide a valid symbol, or the user write "DONE".
    The ouptut of calling this function will be a string, containing all the symbols separated by a space (this will be the first argument of the API function yf.download).
    """
    my_symbols = ''
    symbols_w_currency = []
    symbol = input('Provide a symbol/ISIN: ')
    while symbol != 'DONE':
        try:
            yf.Ticker(symbol).info['currency']
            my_symbols += symbol + ' '
            symbols_w_currency.append(symbol + ' [' + yf.Ticker(symbol).info['currency'] + ']') 
            print(f'symbol {symbol} appended correctly to the desired list. Proceed providing a nee one, or write "DONE" if finish.')
            symbol = input('Provide a new symbol. Once finish, write "DONE".')
        except KeyError:
            print(f'The symbol {symbol} does not exist on the Data Base. Try serching for the ISIN or the symbol in "https://es.finance.yahoo.com/".')
            symbol = input('Provide a new symbol. Once finish, write "DONE".')
    return my_symbols[:-1]

def getSymbols_df():
    df = yf.download(tickers = getSymbols(), #AMZN, 3382.T, SPY, JPXN
                    period = '80y',
                    interval = '1d')
    df = df[['Adj Close']]
    df = df.droplevel(0, axis=1)
    #df.columns = my_tickers[1]
    df = df.reset_index()
    df = df.fillna(method='ffill')
    try:
        df = df.rename(columns={'3382.T':'Seven'})
        df['Seven'] = df['Seven'].apply(lambda x: x*0.0074) #Converting Seven value (in JPY curreny to USD currency)
    except:
        pass
    return df

def get_usa_pib():
    url = 'https://datosmacro.expansion.com/pib/usa'
    res = requests.get(url)
    soup = BeautifulSoup(res.content, 'html.parser')

    usa = soup.find_all('div', attrs={'class':'row'})[4]
    usa1 = usa.find_all('td', attrs={'class':'fecha'})
    usa2 = usa.find_all('td', attrs={'class':'numero dol'})
    years = []
    pib_value = []
    for i in usa1:
        year = date(int(i.getText()), 12, 31)
        years.append(year)
    for j in usa2:
        to_append = ''.join(filter(str.isdigit, j.getText()))
        pib_value.append(to_append)
    pib_value = pib_value[:94]
    years = years[:94]

    usa_hist_pib = {'year':years,
                    'pib_value':pib_value}
    return pd.DataFrame(usa_hist_pib)

def get_jap_pib():
    url = 'https://datosmacro.expansion.com/pib/japon'
    res = requests.get(url)
    soup = BeautifulSoup(res.content, 'html.parser')

    jap = soup.find_all('div', attrs={'class':'row'})[3]
    jap1 = jap.find_all('td', attrs={'class':'fecha'})
    jap2 = jap.find_all('td', attrs={'class':'numero dol'})
    years = []
    pib_value = []
    for i in jap1:
        year = date(int(i.getText()), 12, 31)
        years.append(year)
    for j in jap2:
        to_append = ''.join(filter(str.isdigit, j.getText()))
        pib_value.append(to_append)
    pib_value = pib_value[:63]
    years = years[:63]

    jap_hist_pib = {'year':years,
                    'pib_value':pib_value}
    return pd.DataFrame(jap_hist_pib)

def financial_wb_connection(password):   
    dbName = "financials"
    connectionData=f"mysql+pymysql://root:{password}@localhost/{dbName}"
    engine = alch.create_engine(connectionData)
    return engine

def get_wb_pass():
    return getpass("Please enter your Workbench password: ")

def load_to_sql(usa_hist_pib, jap_hist_pib, df):
    pib = usa_hist_pib.merge(jap_hist_pib, how='left', on='year', suffixes=['_usa', '_jap'])
    password = get_wb_pass()
    pib.to_sql(con=financial_wb_connection(password), name='pib', if_exists='replace')
    df.to_sql(con=financial_wb_connection(password), name='usa_jap', if_exists='replace')


def year_w_YoY(yearly_data):
    yearly_data['usa_pib_YoY'] = yearly_data['pib_value_usa'].pct_change(periods=1)*100 
    yearly_data['jap_pib_YoY'] = yearly_data['pib_value_jap'].pct_change(periods=1)*100 
    yearly_data['seven_YoY'] = yearly_data['seven'].pct_change(periods=1)*100 
    yearly_data['amzn_YoY'] = yearly_data['amzn'].pct_change(periods=1)*100 
    yearly_data['jpxn_YoY'] = yearly_data['jpxn'].pct_change(periods=1)*100 
    yearly_data['spy_YoY'] = yearly_data['spy'].pct_change(periods=1)*100
    return yearly_data

def week_w_YoY(weekly_data):
    weekly_data['seven_WoW'] = weekly_data['seven'].pct_change(periods=1)*100 
    weekly_data['amzn_WoW'] = weekly_data['amzn'].pct_change(periods=1)*100 
    weekly_data['jpxn_WoW'] = weekly_data['jpxn'].pct_change(periods=1)*100 
    weekly_data['spy_WoW'] = weekly_data['spy'].pct_change(periods=1)*100 
    return weekly_data