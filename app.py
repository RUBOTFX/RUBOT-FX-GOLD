{\rtf1\ansi\ansicpg1252\cocoartf2822
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww16400\viewh10720\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import streamlit as st\
import yfinance as yf\
import time\
import pandas as pd\
\
# --- CONFIGURATION ---\
st.set_page_config(\
    page_title="Spot Gold Sniper (XAU/USD)",\
    page_icon="\uc0\u55357 \u56401 ",\
    layout="centered"\
)\
\
# --- 1H BARRIER RANGES ---\
BARRIER_RANGES = [\
    (4551.000, 4570.000),\
    (4380.000, 4400.000),\
    (4253.000, 4273.000),\
    (3980.000, 4000.000),\
    (3871.000, 3891.000),\
    (3651.000, 3671.000)\
]\
PIP_TRIGGER = 2.00\
SYMBOL = "XAUUSD=X" # Correct Spot Gold Ticker\
\
# --- CUSTOM UI STYLING ---\
st.markdown("""\
    <style>\
    .stApp \{ background-color: #0E1117; color: white; \}\
    .big-price \{\
        font-size: 60px !important; font-weight: bold;\
        color: #FFD700; text-align: center;\
        font-family: 'Courier New', Courier, monospace;\
        text-shadow: 0px 0px 10px #B8860B;\
    \}\
    .signal-box \{\
        padding: 20px; border-radius: 10px;\
        text-align: center; font-size: 24px; font-weight: bold;\
        margin-bottom: 20px; border: 2px solid #333;\
    \}\
    .stTable \{ font-size: 18px; \}\
    </style>\
    """, unsafe_allow_html=True)\
\
# --- FUNCTION: GET SPOT PRICE ---\
def get_spot_gold():\
    try:\
        # Fetch standard 1-minute data for the Spot Ticker\
        ticker = yf.Ticker(SYMBOL)\
        df = ticker.history(period="1d", interval="1m")\
        \
        if not df.empty:\
            # Return the most recent 'Close' price\
            return float(df['Close'].iloc[-1])\
        return None\
    except:\
        return None\
\
# --- SESSION STATE ---\
if 'last_res' not in st.session_state: st.session_state.last_res = None\
if 'last_sup' not in st.session_state: st.session_state.last_sup = None\
if 'sell_active' not in st.session_state: st.session_state.sell_active = False\
if 'buy_active' not in st.session_state: st.session_state.buy_active = False\
\
# --- MAIN APP ---\
st.title("\uc0\u55357 \u56401  Spot Gold Sniper (XAU/USD)")\
st.caption("Data Source: Yahoo Finance Spot Rate (Free/Unlimited)")\
\
price_placeholder = st.empty()\
signal_placeholder = st.empty()\
barriers_placeholder = st.empty()\
\
while True:\
    price = get_spot_gold()\
    \
    if price:\
        # 1. IDENTIFY BARRIERS\
        active_res = None\
        active_sup = None\
        \
        # Closest Resistance (Above Price)\
        potential_resistances = [r for r in BARRIER_RANGES if r[0] > price]\
        if potential_resistances:\
            active_res = min(potential_resistances, key=lambda x: x[0])\
\
        # Closest Support (Below Price)\
        potential_supports = [r for r in BARRIER_RANGES if r[1] < price]\
        if potential_supports:\
            active_sup = max(potential_supports, key=lambda x: x[0])\
\
        # 2. UPDATE PRICE DISPLAY\
        with price_placeholder.container():\
            st.markdown(f'<div class="big-price">$\{price:.2f\}</div>', unsafe_allow_html=True)\
\
        # 3. STRATEGY LOGIC\
        status_msg = "SCANNING CHART..."\
        box_color = "#262730"\
        text_color = "#aaaaaa"\
\
        # === SELL LOGIC ===\
        if active_res:\
            if active_res != st.session_state.last_res:\
                st.session_state.sell_active = False\
                st.session_state.last_res = active_res\
            \
            # Entry: Touch Bottom of Resistance\
            if price >= active_res[0]: st.session_state.sell_active = True\
            \
            if st.session_state.sell_active:\
                if price > active_res[1]:\
                    st.session_state.sell_active = False # Failed (Broke Top)\
                elif price < active_res[0]:\
                    drop = active_res[0] - price\
                    if drop >= PIP_TRIGGER:\
                        status_msg = f"\uc0\u55357 \u57000  SELL SIGNAL \u55357 \u57000 <br>FAILED RETEST<br>Drop: $\{drop:.2f\}"\
                        box_color = "#8B0000" # Deep Red\
                        text_color = "white"\
                    else:\
                        status_msg = f"\uc0\u55357 \u56521  SELL SETUP<br>Retesting Resistance...<br>Drop: $\{drop:.2f\}"\
                        box_color = "#5c0000" # Dim Red\
                        text_color = "white"\
                else:\
                    status_msg = "\uc0\u9888 \u65039  TESTING RESISTANCE ZONE"\
                    box_color = "#B8860B" # Gold\
                    text_color = "black"\
\
        # === BUY LOGIC ===\
        if active_sup:\
            if active_sup != st.session_state.last_sup:\
                st.session_state.buy_active = False\
                st.session_state.last_sup = active_sup\
            \
            # Entry: Touch Top of Support\
            if price <= active_sup[1]: st.session_state.buy_active = True\
            \
            if st.session_state.buy_active:\
                if price < active_sup[0]:\
                    st.session_state.buy_active = False # Failed (Broke Bottom)\
                elif price > active_sup[1]:\
                    rise = price - active_sup[1]\
                    if rise >= PIP_TRIGGER:\
                        status_msg = f"\uc0\u55357 \u56960  BUY SIGNAL \u55357 \u56960 <br>SUCCESSFUL RETEST<br>Bounce: $\{rise:.2f\}"\
                        box_color = "#006400" # Deep Green\
                        text_color = "white"\
                    else:\
                        status_msg = f"\uc0\u55357 \u56520  BUY SETUP<br>Retesting Support...<br>Bounce: $\{rise:.2f\}"\
                        box_color = "#004d00" # Dim Green\
                        text_color = "white"\
                else:\
                    if "SELL" not in status_msg:\
                        status_msg = "\uc0\u9888 \u65039  TESTING SUPPORT ZONE"\
                        box_color = "#B8860B"\
                        text_color = "black"\
\
        # 4. RENDER SIGNAL BOX\
        with signal_placeholder.container():\
            st.markdown(f"""\
                <div class="signal-box" style="background-color: \{box_color\}; color: \{text_color\};">\
                    \{status_msg\}\
                </div>\
            """, unsafe_allow_html=True)\
\
        # 5. RENDER BARRIER LIST\
        data = []\
        sorted_barriers = sorted(BARRIER_RANGES, key=lambda x: x[0], reverse=True)\
        for r in sorted_barriers:\
            status = ""\
            if r == active_res: status = "\uc0\u55357 \u56628  RESISTANCE"\
            elif r == active_sup: status = "\uc0\u55357 \u57314  SUPPORT"\
            elif r[0] <= price <= r[1]: status = "\uc0\u55357 \u57313  INSIDE ZONE"\
            data.append(\{"Lower": f"\{r[0]:.3f\}", "Upper": f"\{r[1]:.3f\}", "Status": status\})\
\
        with barriers_placeholder.container():\
            st.table(pd.DataFrame(data))\
    \
    # 5-second polling for Yahoo Finance (Safe speed)\
    time.sleep(5)}