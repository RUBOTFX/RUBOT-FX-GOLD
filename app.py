import streamlit as st
import yfinance as yf
import time
import pandas as pd
import requests

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Spot Gold Sniper (15M)",
    page_icon="👑",
    layout="centered"
)

# --- 1H BARRIER RANGES ---
BARRIER_RANGES = [
    (4551.000, 4570.000),
    (4380.000, 4400.000),
    (4253.000, 4273.000),
    (3980.000, 4000.000),
    (3871.000, 3891.000),
    (3651.000, 3671.000)
]
PIP_TRIGGER = 2.00
SYMBOL = "XAUUSD=X" # Spot Gold

# --- CUSTOM UI STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: white; }
    .big-price {
        font-size: 70px !important; font-weight: 800;
        color: #FFD700; text-align: center;
        text-shadow: 0px 0px 15px rgba(255, 215, 0, 0.5);
        margin-bottom: 10px;
    }
    .signal-box {
        padding: 25px; border-radius: 12px;
        text-align: center; font-size: 22px; font-weight: bold;
        margin-bottom: 20px; border: 1px solid #333;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .stTable { font-size: 16px; }
    </style>
    """, unsafe_allow_html=True)

# --- ADVANCED DATA FETCHING (15M BYPASS) ---
def get_gold_price():
    try:
        # 1. Randomize User-Agent to look like a real Laptop (Windows 10)
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        
        # 2. Fetch 15-Minute Data (Less likely to be blocked than 1m)
        ticker = yf.Ticker(SYMBOL, session=session)
        # We fetch 1 day of 15m candles
        df = ticker.history(period="1d", interval="15m")
        
        if not df.empty:
            return float(df['Close'].iloc[-1])
        return None
    except Exception as e:
        # Optional: print error to terminal logs for debugging
        print(f"Data Fetch Error: {e}")
        return None

# --- SESSION STATE ---
if 'last_res' not in st.session_state: st.session_state.last_res = None
if 'last_sup' not in st.session_state: st.session_state.last_sup = None
if 'sell_active' not in st.session_state: st.session_state.sell_active = False
if 'buy_active' not in st.session_state: st.session_state.buy_active = False

# --- MAIN APP LAYOUT ---
st.title("👑 Spot Gold Sniper (15M)")
st.caption(f"Tracking: {SYMBOL} | Interval: 15-Minute (Anti-Block)")

price_placeholder = st.empty()
signal_placeholder = st.empty()
barriers_placeholder = st.empty()
status_placeholder = st.empty()

# --- MAIN LOOP ---
while True:
    price = get_gold_price()
    
    if price:
        status_placeholder.empty() # Clear loading message

        # 1. BARRIER LOGIC
        active_res = None
        active_sup = None
        
        potential_resistances = [r for r in BARRIER_RANGES if r[0] > price]
        if potential_resistances:
            active_res = min(potential_resistances, key=lambda x: x[0])

        potential_supports = [r for r in BARRIER_RANGES if r[1] < price]
        if potential_supports:
            active_sup = max(potential_supports, key=lambda x: x[0])

        # 2. RENDER PRICE
        with price_placeholder.container():
            st.markdown(f'<div class="big-price">${price:.2f}</div>', unsafe_allow_html=True)

        # 3. SIGNAL LOGIC
        status_msg = "SCANNING MARKET..."
        box_color = "#2a2a2a"
        text_color = "#888888"

        # SELL SIDE
        if active_res:
            if active_res != st.session_state.last_res:
                st.session_state.sell_active = False
                st.session_state.last_res = active_res
            
            if price >= active_res[0]: st.session_state.sell_active = True
            
            if st.session_state.sell_active:
                if price > active_res[1]:
                    st.session_state.sell_active = False
                elif price < active_res[0]:
                    drop = active_res[0] - price
                    if drop >= PIP_TRIGGER:
                        status_msg = f"🚨 SELL SIGNAL 🚨<br>REJECTION CONFIRMED<br>Drop: {drop:.2f} pts"
                        box_color = "#8B0000"
                        text_color = "white"
                    else:
                        status_msg = f"📉 SELL WATCH<br>Retesting Zone...<br>Drop: {drop:.2f} pts"
                        box_color = "#5c0000"
                        text_color = "white"
                else:
                    status_msg = "⚠️ IN RESISTANCE ZONE"
                    box_color = "#B8860B"
                    text_color = "black"

        # BUY SIDE
        if active_sup:
            if active_sup != st.session_state.last_sup:
                st.session_state.buy_active = False
                st.session_state.last_sup = active_sup
            
            if price <= active_sup[1]: st.session_state.buy_active = True
            
            if st.session_state.buy_active:
                if price < active_sup[0]:
                    st.session_state.buy_active = False
                elif price > active_sup[1]:
                    rise = price - active_sup[1]
                    if rise >= PIP_TRIGGER:
                        status_msg = f"🚀 BUY SIGNAL 🚀<br>BOUNCE CONFIRMED<br>Rise: {rise:.2f} pts"
                        box_color = "#006400"
                        text_color = "white"
                    else:
                        status_msg = f"📈 BUY WATCH<br>Retesting Zone...<br>Rise: {rise:.2f} pts"
                        box_color = "#004d00"
                        text_color = "white"
                else:
                    if "SELL" not in status_msg:
                        status_msg = "⚠️ IN SUPPORT ZONE"
                        box_color = "#B8860B"
                        text_color = "black"

        # 4. RENDER SIGNAL BOX
        with signal_placeholder.container():
            st.markdown(f"""
                <div class="signal-box" style="background-color: {box_color}; color: {text_color};">
                    {status_msg}
                </div>
            """, unsafe_allow_html=True)

        # 5. RENDER TABLE
        data = []
        sorted_barriers = sorted(BARRIER_RANGES, key=lambda x: x[0], reverse=True)
        for r in sorted_barriers:
            status = ""
            if r == active_res: status = "🔴 RESISTANCE"
            elif r == active_sup: status = "🟢 SUPPORT"
            elif r[0] <= price <= r[1]: status = "🟡 INSIDE"
            data.append({"Lower": f"{r[0]:.3f}", "Upper": f"{r[1]:.3f}", "Type": status})

        with barriers_placeholder.container():
            st.table(pd.DataFrame(data))
            
    else:
        # STILL CONNECTING
        with status_placeholder.container():
            st.warning("⚠️ Connecting... If this takes >20s, Yahoo is busy. Retrying...")
            
    time.sleep(15) # Wait 15 seconds between checks to respect Yahoo limits
