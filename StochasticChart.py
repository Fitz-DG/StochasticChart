import pandas as pd
import numpy as np
import plotly.offline as offline
import plotly.graph_objs as go
from plotly import tools
pd.set_option('display.max_rows', 100000)
pd.set_option('display.max_columns', 100000)

# 종목 이름을 입력하면 종목에 해당하는 코드를 불러와
# 네이버 금융(http://finance.naver.com)에 넣어줌
def get_url(item_name, code_df):
    code = code_df.query("name=='{}'".format(item_name))['code'].to_string(index=False)
    url = 'http://finance.naver.com/item/sise_day.nhn?code={code}'.format(code=code)

    print("요청 URL = {}".format(url))
    return url


# 일자(n,m,t)에 따른 Stochastic(KDJ)의 값을 구하기 위해 함수형태로 만듬
def get_stochastic(df, n=12, m=5, t=5):
#def get_stochastic(df, n=15, m=5, t=3):
    # 입력받은 값이 dataframe이라는 것을 정의해줌
    df = pd.DataFrame(df)

    # n일중 최고가
    ndays_high = df['고가'].rolling(window=n, min_periods=1).max()
    #ndays_high = df['고가'].rolling(window=n).max()
    # n일중 최저가
    ndays_low = df['저가'].rolling(window=n, min_periods=1).min()
    #ndays_low = df['저가'].rolling(window=n).min()

    # Fast%K 계산
    kdj_k = ((df['종가'] - ndays_low) / (ndays_high - ndays_low)) * 100
    # Fast%D (=Slow%K) 계산
    kdj_d = kdj_k.ewm(span=m).mean()
    # Slow%D 계산
    kdj_j = kdj_d.ewm(span=t).mean()

    # dataframe에 컬럼 추가
    df = df.assign(kdj_k=kdj_k, kdj_d=kdj_d, kdj_j=kdj_j).dropna()

    return df

def stochastic(df, n=15, m=5, t=3):
    high = df['고가'].rolling(window=5).max()
    low = df['저가'].rolling(window=5).min()
    #df['K'] = 100 * (df['종가'] - low) / (high - low)
    #df['D'] = df['K'].rolling(window=3).mean()

    df['kdj_k'] = 100 * (df['종가'] - low) / (high - low)
    df['kdj_d'] = df['kdj_k'].rolling(window=3).mean()
    df['kdj_j'] = df['kdj_k'].rolling(window=3).mean()

    #df = df.assign(kdj_k=kdj_k, kdj_d=kdj_d, kdj_j=kdj_j).dropna()

    return df


code_df = pd.read_html('http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13', header=0)[0]

# 종목코드가 6자리이기 때문에 6자리를 맞춰주기 위해 설정해줌
code_df.종목코드 = code_df.종목코드.map('{:06d}'.format)

# 우리가 필요한 것은 회사명과 종목코드이기 때문에 필요없는 column들은 제외해준다.
code_df = code_df[['회사명', '종목코드']]

# 한글로된 컬럼명을 영어로 바꿔준다.
code_df = code_df.rename(columns={'회사명': 'name', '종목코드': 'code'})
#print( code_df.head() )


# 신라젠의 일자데이터 url 가져오기
#item_name = '신라젠'
item_name = '동국제강'
url = get_url(item_name, code_df)

# 일자 데이터를 담을 df라는 DataFrame 정의
df = pd.DataFrame()

# 1페이지에서 20페이지의 데이터만 가져오기
for page in range(1, 21):
    pg_url = '{url}&page={page}'.format(url=url, page=page)
    df = df.append(pd.read_html(pg_url, header=0)[0], ignore_index=True)

# df.dropna()를 이용해 결측값 있는 행 제거
df = df.dropna()
# 상위 5개 데이터 확인하기


#fast campus
#df = stochastic(df)

df = df.iloc[::-1]
df = get_stochastic(df)
index = df['날짜']
df.set_index(index)
df['diff'] = df['kdj_d'] - df['kdj_j']
df['shift'] = df['diff'].shift(1)
#df['result'] = (df['diff'] * df['diff'].shift(1)) < 0
df['result'] = np.where(df['kdj_d'] - df['kdj_j'] > 0, 1, 0)
print( df.head(20) )
#print( df.iloc())

# jupyter notebook 에서 출력
#offline.init_notebook_mode(connected=True)

kdj_k = go.Scatter(
    x=df['날짜'],
    y=df['kdj_k'],
    name="Fast%K")

kdj_d = go.Scatter(
    x=df['날짜'],
    y=df['kdj_d'],
    name="Fast%D")

kdj_d2 = go.Scatter(
    x=df['날짜'],
    y=df['kdj_d'],
    name="Slow%K")

kdj_j = go.Scatter(
    x=df['날짜'],
    y=df['kdj_j'],
    name="Slow%D")

close = go.Scatter(
    x=df['날짜'],
    y=df['종가'],
    name='종가')

result = go.Scatter(
    x=df['날짜'],
    y=df['result'],
    name='Signal')

trade_volume = go.Bar(
    x=df['날짜'],
    y=df['거래량'],
    name='거래량')

#data0 = close
data1 = [kdj_d2, kdj_j]
data2 = [trade_volume]

# fast campus
#data0 = close
#data1 = [kdj_k, kdj_d]
#data2 = [trade_volume]

# data = [celltrion]
# layout = go.Layout(yaxis=dict(
#         autotick=False,
#         ticks='outside',
#         tick0=0,
#         dtick=10,
#         ticklen=8,
#         tickwidth=4,
#         tickcolor='#000'
#     ))

fig = tools.make_subplots(rows=4, cols=1, shared_xaxes=True)

#fig.append_trace(data0, 1, 1)
fig.add_candlestick(open=df['시가'], high=df['고가'], low=df['저가'], close=df['종가'], row=1, col=1)
#data0 = go.Candlestick(x=df['날짜'], open=df['시가'], high=df['고가'], low=df['저가'], close=df['종가'])
for trace in data1:
    fig.append_trace(trace, 2, 1)

    fig.append_trace(result, 3, 1)
for trace in data2:
    fig.append_trace(trace, 4, 1)
# fig = go.Figure(data=data, layout=layout)

offline.plot(fig)

