import yfinance as yf
import plotly.graph_objects as go

def get_stock(ticker):
    return yf.Ticker(ticker)

def get_data(stock):
    # 최근 6개월 일봉 데이터 가져오기
    return stock.history(period="6mo")

def get_price(data):
    if data.empty:
        return "N/A"
    latest_close = data['Close'].iloc[-1]
    return f"${latest_close:,.2f}"

def get_change(data):
    if len(data) < 2:
        return {'amount': '0.00', 'percent': '0.0%', 'icon': 'dash', 'color': 'secondary'}
    
    prev_close = data['Close'].iloc[-2]
    latest_close = data['Close'].iloc[-1]
    diff = latest_close - prev_close
    pct = (diff / prev_close) * 100
    
    is_positive = diff >= 0
    return {
        'amount': f"{'+' if is_positive else ''}${diff:,.2f}",
        'percent': f"{'+' if is_positive else ''}{pct:.2f}%",
        'icon': 'arrow-up-right' if is_positive else 'arrow-down-right',
        'color': 'success' if is_positive else 'danger'
    }

def make_candlestick_chart(data, ticker_symbol):
    fig = go.Figure(data=[go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close']
    )])
    fig.update_layout(
        title=f"{ticker_symbol} Daily Price Chart",
        xaxis_rangeslider_visible=False,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig

def make_OHLC_table(data):
    if data.empty:
        return {}
    last = data.iloc[-1]
    date_str = data.index[-1].strftime('%Y-%m-%d')
    return {
        'date': date_str,
        'close': f"${last['Close']:,.2f}",
        'open': f"${last['Open']:,.2f}",
        'high': f"${last['High']:,.2f}",
        'low': f"${last['Low']:,.2f}",
        'volume': f"{int(last['Volume']):,}"
    }
