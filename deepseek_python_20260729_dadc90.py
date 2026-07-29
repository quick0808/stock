import yfinance as yf
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime

# ================== 配置区域（请修改这里）==================
# 要获取的股票代码（美股代码， Yahoo Finance格式）
STOCKS = ["SKHY", "MSFT", "SNDK", "MU","STX","WDC", "^GSPC"]  # ^GSPC 是标普500指数

# QQ邮箱SMTP配置
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 465  # SSL加密端口
SENDER_EMAIL = "494923589@qq.com"  # 发送邮件的邮箱
AUTH_CODE = "ezrxvfevzxpubhbc"      # 上一步获取的授权码，不是QQ密码！
RECEIVER_EMAIL = "doublesone@outlook.com" # 接收邮件的邮箱
# =======================================================

def fetch_stock_data(symbols):
    """获取股票数据"""
    data = {}
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            # 获取最新一个交易日的日线数据
            hist = ticker.history(period="1d")
            if not hist.empty:
                # 获取当天的开盘价和收盘价
                today = hist.iloc[-1]
                data[symbol] = {
                    "Open": round(today['Open'], 2),
                    "Close": round(today['Close'], 2),
                    "Change": round(today['Close'] - today['Open'], 2)
                }
            else:
                data[symbol] = {"Error": "No data"}
        except Exception as e:
            data[symbol] = {"Error": str(e)}
    return data

def format_email_content(data):
    """将数据格式化为邮件正文（HTML表格）"""
    df = pd.DataFrame(data).T
    # 生成美观的HTML表格
    table_html = df.to_html(classes='dataframe', border=1, justify='center')
    
    # 构造完整的HTML邮件
    html_content = f"""
    <html>
    <head><meta charset="UTF-8"></head>
    <body>
        <h2>📊 美股收盘报告 - {datetime.now().strftime('%Y-%m-%d')}</h2>
        <p>数据来源：Yahoo Finance</p>
        {table_html}
        <p style="color:gray;font-size:small;">* 此邮件由自动脚本生成，仅供参考。</p>
    </body>
    </html>
    """
    return html_content

def send_email(html_content):
    """发送邮件"""
    msg = MIMEText(html_content, 'html', 'utf-8')
    msg['Subject'] = Header(f'美股日报 {datetime.now().strftime("%Y-%m-%d")}', 'utf-8')
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL

    try:
        # 使用SSL加密连接
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SENDER_EMAIL, AUTH_CODE)
        server.sendmail(SENDER_EMAIL, [RECEIVER_EMAIL], msg.as_string())
        server.quit()
        print("邮件发送成功！")
    except Exception as e:
        print(f"邮件发送失败：{e}")

if __name__ == "__main__":
    print("正在获取美股数据...")
    stock_data = fetch_stock_data(STOCKS)
    print("数据获取完成。")
    
    email_body = format_email_content(stock_data)
    print("正在发送邮件...")
    send_email(email_body)
    print("程序执行完毕。")