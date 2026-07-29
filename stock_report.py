# ============================================================
# 位置1：文件最顶部 —— 所有 import 集中放在这里
# ============================================================
import yfinance as yf
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime
import os
import time          # 【新增】用于重试等待
import matplotlib.pyplot as plt   # 【新增】用于画图
import base64        # 【新增】用于图片转Base64
from io import BytesIO  # 【新增】用于内存中处理图片

# ============================================================
# 位置2：配置区域（保持不变）
# ============================================================
STOCKS = ["AAPL", "MSFT", "GOOGL", "AMZN", "^GSPC"]

SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 465
SENDER_EMAIL = os.getenv('QQ_EMAIL')
AUTH_CODE = os.getenv('QQ_AUTH_CODE')
RECEIVER_EMAIL = "494923589@qq.com"

# ============================================================
# 位置3：新增函数 —— 生成柱状图并转为Base64
# 放在 fetch_stock_data 函数之前或之后都可以
# ============================================================
def generate_chart_base64(data):
    """生成涨跌幅柱状图，返回Base64编码的图片数据"""
    symbols = []
    changes = []
    for sym, info in data.items():
        if "Change" in info:
            symbols.append(sym)
            changes.append(info["Change"])
    
    if not symbols:
        return None
    
    colors = ['red' if c >= 0 else 'green' for c in changes]
    
    plt.figure(figsize=(10, 5))
    bars = plt.bar(symbols, changes, color=colors, edgecolor='black')
    plt.axhline(y=0, color='black', linewidth=0.8, linestyle='--')
    plt.title('美股主要标的今日涨跌情况 (开盘→收盘)', fontsize=14)
    plt.ylabel('涨跌额 (美元)')
    plt.grid(axis='y', linestyle=':', alpha=0.7)
    
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                 f'{height:.2f}', ha='center', va='bottom' if height>0 else 'top')
    
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close()
    return image_base64

# ============================================================
# 位置4：修改后的 fetch_stock_data 函数（增加了重试机制）
# 替换掉原来同名函数
# ============================================================
def fetch_stock_data(symbols, retries=3):
    """获取股票数据，带重试机制"""
    for attempt in range(retries):
        try:
            data = {}
            for symbol in symbols:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                if len(hist) >= 2:
                    today = hist.iloc[-1]
                    yesterday = hist.iloc[-2]
                    change_pct = ((today['Close'] - yesterday['Close']) / yesterday['Close']) * 100
                    data[symbol] = {
                        "Open": round(today['Open'], 2),
                        "Close": round(today['Close'], 2),
                        "Change": round(today['Close'] - today['Open'], 2),
                        "Change_Pct": round(change_pct, 2)
                    }
                else:
                    data[symbol] = {"Error": "Insufficient data"}
            return data  # 成功则直接返回
        except Exception as e:
            print(f"第 {attempt+1} 次获取失败，重试中... 错误: {e}")
            time.sleep(2)
    raise Exception("所有重试均失败，请检查网络或数据源。")

# ============================================================
# 位置5：修改后的 format_email_content 函数（增加了图片参数）
# 替换掉原来同名函数
# ============================================================
def format_email_content(data, img_base64):
    """生成带图片的邮件HTML"""
    df = pd.DataFrame(data).T
    
    img_html = f'<img src="data:image/png;base64,{img_base64}" alt="走势图" style="max-width:100%;">' if img_base64 else ''
    
    html_content = f"""
    <html>
    <head><meta charset="UTF-8"></head>
    <body>
        <h2>📊 美股收盘日报 - {datetime.now().strftime('%Y-%m-%d')}</h2>
        <p>数据来源：Yahoo Finance</p>
        {df.to_html(classes='dataframe', border=1, justify='center')}
        <hr>
        <h3>📈 涨跌柱状图</h3>
        {img_html}
        <p style="color:gray;font-size:small;">* 此邮件由自动脚本生成，仅供参考。</p>
    </body>
    </html>
    """
    return html_content

# ============================================================
# 位置6：send_email 函数（完全不变，照旧）
# ============================================================
def send_email(html_content):
    msg = MIMEText(html_content, 'html', 'utf-8')
    msg['Subject'] = Header(f'美股日报 {datetime.now().strftime("%Y-%m-%d")}', 'utf-8')
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL

    try:
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SENDER_EMAIL, AUTH_CODE)
        server.sendmail(SENDER_EMAIL, [RECEIVER_EMAIL], msg.as_string())
        server.quit()
        print("邮件发送成功！")
    except Exception as e:
        print(f"邮件发送失败：{e}")

# ============================================================
# 位置7：主程序（修改了调用逻辑，增加了图片生成步骤）
# ============================================================
if __name__ == "__main__":
    print("正在获取美股数据...")
    stock_data = fetch_stock_data(STOCKS)
    print("数据获取完成。")
    
    print("正在生成图表...")
    chart_img = generate_chart_base64(stock_data)
    
    print("正在组装邮件...")
    email_body = format_email_content(stock_data, chart_img)
    
    print("正在发送邮件...")
    send_email(email_body)
    print("程序执行完毕。")
