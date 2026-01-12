import streamlit as st
import yfinance as yf
import time
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Spot Gold Sniper (XAU/USD)",
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
SYMBOL = "XAUUSD=X" 

# --- CUSTOM UI STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    .big-price {
        font-size: 60px !important; font-weight: bold;
        color: #FFD700; text-align: center;
        font-family: 'Courier New', Courier, monospace;
        text-shadow: 0px 0px 10px #B8860B;
    }
    .signal-box {
        padding: 20px; border-radius: 10px;
        text-align: center; font-size: 24px; font-weight: bold;
        margin-bottom: 20px; border: 2px solid #333;
    }
    .status-msg {
        text-align: center; color: #888; font-size: 14px;
    }
    .stTable { font-size: 18px; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCTION: GET SPOT PRICE ---
def get_spot_gold():
    try:
        # Fetch data with error handling
        ticker = yf.Ticker(SYMBOL)
        df = ticker.history(period="1d", interval="1m")
        if not df.empty:
            return float(df['Close'].iloc[-1])
        return None
    except Exception as e:
        return None

# --- SESSION STATE ---
if 'last_res' not in st.session_state: st.session_state.last_res = None
if 'last_sup' not in st.session_state: st.session_state.last_sup = None
if 'sell_active' not in st.session_state: st.session_state.sell_active = False
if 'buy_active' not in st.session_state: st.session_state.buy_active = False

# --- MAIN APP LAYOUT ---
st.title("👑 Spot Gold Sniper (XAU/USD)")
st.caption("Data Source: Yahoo Finance Spot Rate (Free/Unlimited)")

# UI Placeholders
price_placeholder = st.empty()
signal_placeholder = st.empty()
barriers_placeholder = st.empty()
debug_placeholder = st.empty() # New debug area

# --- MAIN LOOP ---
while True:
    price = get_spot_gold()
    
    if price:
        # CLEAR DEBUG MESSAGE
        debug_placeholder.empty()

        # 1. IDENTIFY BARRIERS
        active_res = None
        active_sup = None
        
        potential_resistances = [r for r in BARRIER_RANGES if r[0] > price]
        if potential_resistances:
            active_res = min(potential_resistances, key=lambda x: x[0])

        potential_supports = [r for r in BARRIER_RANGES if r[1] < price]
        if potential_supports:
            active_sup = max(potential_supports, key=lambda x: x[0])

        # 2. UPDATE PRICE DISPLAY
        with price_placeholder.container():
            st.markdown(f'<div class="big-price">${price:.2f}</div>', unsafe_allow_html=True)

        # 3. STRATEGY LOGIC
        status_msg = "SCANNING CHART..."
        box_color = "#262730"
        text_color = "#aaaaaa"

        # SELL LOGIC
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
                        status_msg = f"🚨 SELL SIGNAL 🚨<br>FAILED RETEST<br>Drop: ${drop:.2f}"
                        box_color = "#8B0000"
                        text_color = "white"
                    else:
                        status_msg = f"📉 SELL SETUP<br>Retesting Resistance...<br>Drop: ${drop:.2f}"
                        box_color = "#5c0000"
                        text_color = "white"
                else:
                    status_msg = "⚠️ TESTING RESISTANCE ZONE"
                    box_color = "#B8860B"
                    text_color = "black"

        # BUY LOGIC
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
                        status_msg = f"🚀 BUY SIGNAL 🚀<br>SUCCESSFUL RETEST<br>Bounce: ${rise:.2f}"
                        box_color = "#006400"
                        text_color = "white"
                    else:
                        status_msg = f"📈 BUY SETUP<br>Retesting Support...<br>Bounce: ${rise:.2f}"
                        box_color = "#004d00"
                        text_color = "white"
                else:
                    if "SELL" not in status_msg:
                        status_msg = "⚠️ TESTING SUPPORT ZONE"
                        box_color = "#B8860B"
                        text_color = "black"

        # 4. RENDER SIGNAL BOX
        with signal_placeholder.container():
            st.markdown(f"""
                <div class="signal-box" style="background-color: {box_color}; color: {text_color};">
                    {status_msg}
                </div>
            """, unsafe_allow_html=True)

        # 5. RENDER BARRIER LIST
        data = []
        sorted_barriers = sorted(BARRIER_RANGES, key=lambda x: x[0], reverse=True)
        for r in sorted_barriers:
            status = ""
            if r == active_res: status = "🔴 RESISTANCE"
            elif r == active_sup: status = "🟢 SUPPORT"
            elif r[0] <= price <= r[1]: status = "🟡 INSIDE ZONE"
            data.append({"Lower": f"{r[0]:.3f}", "Upper": f"{r[1]:.3f}", "Status": status})

        with barriers_placeholder.container():
            st.table(pd.DataFrame(data))
    
    else:
        # DATA FETCH FAILED - SHOW LOADING MESSAGE
        with debug_placeholder.container():
            st.warning("⚠️ Connecting to Yahoo Finance... (Retrying in 5s)")
            
    time.sleep(5)
