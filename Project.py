import streamlit as st
import pandas_datareader as pdr
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import bs4 as bs
import requests

print("Это программа предназначена для инвестиций на Американском рынке.\n "
      "Введите тикер ценной бумаги, которая вас интересует и период (больше 3-х месяцев включительно) на который "
      "вы хотите инвестировать и программа проведёт анализ этой инвестиции.")
ticker = str(input("Введите тикер ценной бумаги или 0 и тогда программа предложит вам варианты: "))

if ticker == str(0):
    resp = requests.get('http://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    soup = bs.BeautifulSoup(resp.text, 'lxml')
    table = soup.find('table', {'class': 'wikitable sortable'})
    tickers = []
    for row in table.findAll('tr')[1:]:
        tick = row.findAll('td')[0].text.replace('\n', '')
        comp = row.findAll('td')[1].text.replace('\n', '')
        cell = [tick, "-", comp]
        tickers.append(cell)
    print("Если вы не знаете какие тикеры существуют вы можете попробовать такие:")
    for n in tickers:
        print(*n)
    ticker = str(input("Введите тикер ценной бумаги: "))
#  загрузка тикеров с сайта - вебскрапинг => 1 балл

period = list(map(int, input("Введите гаризонт инвестиции (гг-мм): ").split("-")))
now = datetime.now()

# перематываем на год, если месяцы получились "отрицательными"
if now.month - period[1] < 0:
    period[0] += 1
    period[1] -= 12

date_start = [now.year - period[0], now.month - period[1], now.day]
Date_begin = datetime(date_start[0], date_start[1], date_start[2])

company = pdr.get_data_yahoo(symbols=ticker, start=Date_begin)  # продвинутый уровень использования pandas 2 балла
# Использовались какие-то технологии, необходимые для реализации проекта, и не обсуждавшиеся в курсе 2 балла

DaysPeriod = period[0] * 360 + period[1] * 30
plt.figure(figsize=(12, 9))
# Построение графика ценной бумаги
plt.subplot(2, 1, 1)
plt.title(f"График {ticker} и линии Боллинджера")  # заголовок
plt.ylabel("Цена")  # ось ординат
# Строим полосы Боллинджера - стреднее +- 2 стандартных отклонения
MA = company['Adj Close'].rolling(window=30).mean()
BOLU = MA + 2 * company['Adj Close'].rolling(window=30).std()
BOLD = MA - 2 * company['Adj Close'].rolling(window=30).std()
MA.plot()
BOLU.plot()
BOLD.plot()
company['Adj Close'].plot()  # построение графика
plt.grid()  # включение отображение сетки

plt.subplot(2, 1, 2)
# Первым показателем является система MACD - система операющаяся на експоненциальные скользящие средние
MACDquick = company['Adj Close'].ewm(com=12).mean() \
            - company['Adj Close'].ewm(com=26).mean()
# EWM - эксп. скользящее среднее и это продвинутое использование PANDAS выходящее за рамки пройденного => 2 балла
# EWM - Математические возможности Python
# (содержательное использование numpy/scipy, SymPy и т.д. для решения математических задач) => 1 балл
plt.title(f"График MACD")  # заголовок
plt.grid()  # включение отображение сетки
MACDquick.plot()
MACDsignal = MACDquick.ewm(com=9).mean()
MACDsignal.plot()
plt.grid()
plt.show()

# строим гистаграмму объёма торгов
plt.figure(figsize=(12, 9))
plt.title(f"График объема торгов {ticker}")  # заголовок
plt.grid()  # включение отображение сетки
volume = company['Volume']
volume.plot()
plt.grid()
plt.show()

SP500 = "^GSPC"  # Маркет портфолио будем считать через SP500
treasuries = [(13 * 7, "^IRX"), (5 * 365, "^FVX"), (10 * 365, "^TNX"), (30 * 365, "^TYX")]  # (длинна в днях, название)

# Подбираем облигацию, которая ближе всего по периоду к рассматриваему промежутку


def get_bond(DaysPeriod, treasuries):
    if DaysPeriod < treasuries[0][0]:
        return treasuries[0][1]
    i = 1
    while i < len(treasuries):
        if treasuries[i - 1][0] <= DaysPeriod <= treasuries[i][0]:
            break
        i += 1
    if i == len(treasuries):
        return treasuries[-1][1]
    if abs(treasuries[i - 1][0] - DaysPeriod) < abs(treasuries[i][0] - DaysPeriod):
        return treasuries[i - 1][1]
    else:
        return treasuries[i][1]


bond = pdr.get_data_yahoo(symbols=get_bond(DaysPeriod, treasuries), start=Date_begin)
# из бонда извлечём безрисковую ставку процента
r_list = [bond.iloc[ind]['Adj Close'] for ind, value in enumerate(bond.index) if value.day == 1]
r_fr = 0
for i in range(len(r_list) - 1):
    r_fr += r_list[i] / len(r_list)
r_free = r_fr / 100

# ипортирум данные для маркет портфолио
market_portf = pdr.get_data_yahoo(symbols=SP500, start=Date_begin)
# из маркет портфолио извлечём ставку процента для рынка
price_list = [market_portf.iloc[ind]['Adj Close'] for ind, value in enumerate(market_portf.index) if value.day == 1]
r_market = []
for i in range(len(r_list) - 1):
    r_market.append((price_list[i + 1] / price_list[i]) ** 12 - 1)
rn_market = np.array(r_market)
# посчитаем ставку процента для выбранной компании
price_list = [company.iloc[ind]['Adj Close'] for ind, value in enumerate(company.index) if value.day == 1]
r_company = []
for i in range(len(price_list) - 1):
    r_company.append((price_list[i + 1] / price_list[i]) ** 12 - 1)
rn_company = np.array(r_company)
# посчитаем бету для выбранной компании
beta = np.cov(rn_company, rn_market)[0][1] / ((rn_market.std()) ** 2)

# считаем ожидаемую ставку рынка
re_market = 0
for i in range(len(r_market) - 1):
    re_market += r_market[i] / len(r_market)

# считаем ожидаемую ставку компании
re_company = 0
for i in range(len(r_company) - 1):
    re_company += r_company[i] / len(r_company)
alpha = re_company - (r_free + (re_market - r_free) * beta)
print("alpha is", alpha)
if alpha >= 0:
    print(f"Альфа компании равна {alpha} и так как она больше нуля значит компания обыгрывает рынок и надо покупать.")
else:
    print(f"Альфа компании равна {alpha} и так как она меньше нуля значит компания хуже рынка и её не стоит покупать.")

x = np.linspace(0, 3, 50)
y = [r_free + (re_market - r_free) * i for i in x]
# Построение графиков
plt.figure(figsize=(5, 4))
plt.plot(x, y)  # построение графика
plt.plot([beta], [re_company], 'ro')  # посторение точки самой компании
plt.title("Market line")  # заголовок
plt.ylabel("r", fontsize=14)  # ось ординат
plt.grid(True)  # включение отображение сетки
plt.show()

# объём более 120 строк 1 балл
# целостность проекта 1 балл
# впечатление 1 балл я надеюсь вам понравилась программа. Она рассматривает не только класические индикаторы рынка, но и
# финансовую теорию
# итого получается 11 баллов
