"""
app.py
AI Candlestick Pattern Analyzer — Professional Financial Dashboard UI
----------------------------------------------------------------------
UI redesign only. All backend logic (data loading, pattern detection,
profitability analysis) is untouched and imported from:
  - data_loader.py
  - pattern_detector.py
  - pattern_analysis.py

Run with:  streamlit run app.py
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# ── Backend imports (unchanged) ──────────────────────────────────────────────
from data_loader      import load_stock_data, get_ticker_info
from pattern_detector import get_latest_patterns, PATTERNS
from pattern_analysis import analyse_all_patterns, build_ai_explanation


# ════════════════════════════════════════════════════════════════════════════
# 1. PAGE CONFIG
#    layout="wide" gives us the full browser width — essential for a dashboard
# ════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="AI Candlestick Pattern Analyzer",
    page_icon="📊",
    layout="wide",                      # <-- required for dashboard feel
    initial_sidebar_state="expanded",
)


# ════════════════════════════════════════════════════════════════════════════
# 2. GLOBAL CSS
#    We inject a small stylesheet to:
#      - Set a dark background matching a trading terminal
#      - Style "dashboard cards" with rounded borders & subtle gradient tops
#      - Style pattern badges, section headings, and the explanation box
# ════════════════════════════════════════════════════════════════════════════
# Add this AT THE TOP of app.py (after st.set_page_config)
st.markdown("""
<style>
""" + open("global.css").read() + """
/* Landing page additions */
.landing-container {
    padding: 140px 40px 80px;
    text-align: center;
    min-height: 100vh;
}
.stockz-h1 {
    font-size: 4.5rem;
    font-weight: 800;
    background: linear-gradient(90deg, #2563eb, #60a5fa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 2rem;
    line-height: 1.1;
}
.hero-text {
    font-size: 1.3rem;
    max-width: 700px;
    margin: 0 auto 3.5rem;
    line-height: 1.7;
}
.cta-main {
    background: linear-gradient(90deg, #2563eb, #3b82f6);
    color: white !important;
    padding: 18px 40px;
    border-radius: 16px;
    font-size: 1.2rem;
    font-weight: 700;
    border: none;
    display: inline-block;
    box-shadow: 0 8px 32px rgba(37, 99, 235, 0.3);
    transition: all 0.3s ease;
}
.cta-main:hover {
    transform: translateY(-3px);
    box-shadow: 0 12px 40px rgba(37, 99, 235, 0.4);
}
.navbar-fixed {
    position: fixed;
    top: 0;
    width: 100%;
    background: rgba(11, 15, 25, 0.98);
    backdrop-filter: blur(20px);
    padding: 20px 60px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    z-index: 1000;
    border-bottom: 1px solid #1e293b;
}
.nav-links { color: #94a3b8; font-weight: 500; }
.stockz-nav { font-size: 2.2rem; font-weight: 800; }
.auth-links { color: #94a3b8; }
</style>
""", unsafe_allow_html=True)


# Landing page - show first
if 'show_dashboard' not in st.session_state:
    st.session_state.show_dashboard = False

if not st.session_state.show_dashboard:
    st.markdown("""
    <div class="navbar-fixed">
        <div class="nav-links">News | Features</div>
        <div class="stockz-nav">𝗦𝗧𝗢𝗖𝗞𝗭</div>
        <div class="auth-links">About | Login | Sign Up</div>
    </div>
    
    <div class="landing-container">
        <h1 class="stockz-h1">What is Stockz?</h1>
        <p class="hero-text">
            A simple and easy to understand app made by students to aid beginners 
            get into the world of trading and stock markets.
        </p>
        <button class="cta-main" onclick="parent.streamlit.setComponentValue({show_dashboard: true})">
            Start Learning →
        </button>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Skip to Dashboard"):  # Fallback button
        st.session_state.show_dashboard = True
        st.rerun()
    st.stop()



# ════════════════════════════════════════════════════════════════════════════
# 3. SIDEBAR — user controls
# ════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 📊 Pattern Analyzer")
    st.markdown("<hr style='border-color:#1e2d40;margin:0.75rem 0'>", unsafe_allow_html=True)

    # Stock ticker input
    ticker = st.text_input(
        "Stock Ticker",
        value="AAPL",
        help="Enter any Yahoo Finance symbol, e.g. AAPL, MSFT, TSLA, ^GSPC",
    ).upper().strip()

    # Time range selector
    period = st.selectbox(
        "Time Range",
        options=["6mo", "1y", "2y", "5y"],
        index=1,
        format_func=lambda x: {
            "6mo": "6 Months",
            "1y":  "1 Year",
            "2y":  "2 Years",
            "5y":  "5 Years",
        }[x],
    )

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    analyse = st.button("🔍  Run Analysis")

    # Pattern legend in sidebar
    st.markdown("<hr style='border-color:#1e2d40;margin:1rem 0 0.75rem 0'>", unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:0.72rem;color:#4b5563;font-weight:600;"
        "text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.5rem'>"
        "Patterns Tracked</div>",
        unsafe_allow_html=True,
    )
    legend = {
        "Hammer":            ("#34d399", "↑ Bullish"),
        "Doji":              ("#fbbf24", "— Neutral"),
        "Bullish Engulfing": ("#34d399", "↑ Bullish"),
        "Bearish Engulfing": ("#f87171", "↓ Bearish"),
        "Shooting Star":     ("#f87171", "↓ Bearish"),
    }
    for p_name, (p_color, p_label) in legend.items():
        st.markdown(
            f"<div style='font-size:0.8rem;padding:3px 0;color:{p_color}'>"
            f"{p_label} &nbsp;·&nbsp; {p_name}</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<hr style='border-color:#1e2d40;margin:1rem 0 0.5rem 0'>", unsafe_allow_html=True)
    st.caption("Data: Yahoo Finance · Patterns: TA-Lib")


# ════════════════════════════════════════════════════════════════════════════
# CONTAINER A — Dashboard header (always visible)
# ════════════════════════════════════════════════════════════════════════════
with st.container():
    st.markdown("""
    <div class="dash-header">
        <h1>📊 AI Candlestick Pattern Analyzer</h1>
        <p>
            Identify classic candlestick patterns in historical stock data and evaluate
            how profitable those signals have been over the selected time period.
            Patterns are detected using TA-Lib; profitability is measured as the
            3-day forward price change after each signal.
        </p>
    </div>
    """, unsafe_allow_html=True)

# ── Show a friendly placeholder if no analysis has been run yet ──────────────
if not analyse:
    st.markdown("""
    <div style="background:#111827;border:1px dashed #1e2d40;border-radius:10px;
                padding:3rem;text-align:center;margin-top:2rem;">
        <div style="font-size:2.5rem;margin-bottom:0.75rem">🕯️</div>
        <div style="font-size:1rem;font-weight:600;color:#f9fafb;margin-bottom:0.4rem">
            Ready to analyze
        </div>
        <div style="font-size:0.875rem;color:#4b5563">
            Enter a stock ticker in the sidebar and click
            <strong style="color:#9ca3af">Run Analysis</strong>.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ════════════════════════════════════════════════════════════════════════════
# LOAD DATA  (calls backend — no changes here)
# ════════════════════════════════════════════════════════════════════════════
with st.spinner(f"Fetching data for {ticker} …"):
    df   = load_stock_data(ticker, period)
    info = get_ticker_info(ticker)

if df.empty:
    st.error(f"❌  Could not load data for **{ticker}**. Check the symbol and try again.")
    st.stop()


# ════════════════════════════════════════════════════════════════════════════
# RUN ANALYSIS  (calls backend — no changes here)
# ════════════════════════════════════════════════════════════════════════════
with st.spinner("Detecting patterns and calculating historical statistics …"):
    stats_all       = analyse_all_patterns(df)
    latest_patterns = get_latest_patterns(df)


# ── Convenience variables derived from data ──────────────────────────────────
latest_close = float(df["Close"].iloc[-1])
prev_close   = float(df["Close"].iloc[-2])
daily_chg    = (latest_close - prev_close) / prev_close * 100
chg_color    = "bullish" if daily_chg >= 0 else "bearish"
chg_arrow    = "▲"       if daily_chg >= 0 else "▼"

# Primary pattern = the first one detected today (used for headline KPIs)
primary = latest_patterns[0] if latest_patterns else None


# ════════════════════════════════════════════════════════════════════════════
# CONTAINER B — Stock identity + price KPI row
# ════════════════════════════════════════════════════════════════════════════
with st.container():
    st.markdown(
        f"<div class='stock-title'>{info['name']} &nbsp;"
        f"<code style='font-size:0.9rem'>{ticker}</code></div>"
        f"<div class='stock-sub'>{info['sector']} · {info['currency']} · {period} lookback</div>",
        unsafe_allow_html=True,
    )

    # ── METRICS ROW (4 cards) ─────────────────────────────────────────────
    # Card 1: Latest close price
    # Card 2: Daily % change (green/red)
    # Card 3: Detected pattern win rate   ← key requirement
    # Card 4: Average 3-day return         ← key requirement
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Latest Close</div>
            <div class="metric-value">{latest_close:.2f}</div>
            <div class="metric-sub">{info['currency']}</div>
        </div>""", unsafe_allow_html=True)

    with col2:
        cc = "bullish-card" if daily_chg >= 0 else "bearish-card"
        st.markdown(f"""
        <div class="metric-card {cc}">
            <div class="metric-label">Daily Change</div>
            <div class="metric-value {chg_color}">{chg_arrow} {abs(daily_chg):.2f}%</div>
            <div class="metric-sub">vs prior close</div>
        </div>""", unsafe_allow_html=True)

    with col3:
        # Show win rate of today's primary pattern, or a placeholder
        if primary:
            p_wr     = stats_all[primary]["win_rate"]
            p_sig    = stats_all[primary]["signal"]
            wr_cls   = p_sig                           # bullish / bearish / neutral
            card_cls = f"{p_sig}-card"
            wr_disp  = f"{p_wr}%"
        else:
            wr_cls   = "neutral"
            card_cls = ""
            wr_disp  = "—"

        st.markdown(f"""
        <div class="metric-card {card_cls}">
            <div class="metric-label">Detected Pattern</div>
            <div class="metric-value {wr_cls}">{primary if primary else "None"}</div>
            <div class="metric-sub">historical win rate: {wr_disp}</div>
        </div>""", unsafe_allow_html=True)

    with col4:
        if primary:
            p_ar   = stats_all[primary]["avg_return"]
            ar_str = f"+{p_ar:.2f}%" if p_ar >= 0 else f"{p_ar:.2f}%"
            ar_cls = "bullish" if p_ar >= 0 else "bearish"
        else:
            ar_str = "—"
            ar_cls = "neutral"

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Avg Return (3 Days)</div>
            <div class="metric-value {ar_cls}">{ar_str}</div>
            <div class="metric-sub">{primary if primary else "No pattern today"}</div>
        </div>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# CONTAINER C — Today's signals (pattern badges)
# ════════════════════════════════════════════════════════════════════════════
with st.container():
    st.markdown(
        "<div class='section-heading'>Today's Signals</div>",
        unsafe_allow_html=True,
    )

    if latest_patterns:
        html = "<div class='badge-row'>"
        for p in latest_patterns:
            sig   = PATTERNS[p]["signal"]
            arrow = "↑" if sig == "bullish" else ("↓" if sig == "bearish" else "—")
            html += f"<span class='pattern-badge badge-{sig}'>{arrow}&nbsp;{p}</span>"
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)
    else:
        st.markdown(
            "<span class='badge-none'>No candlestick patterns detected on the most recent candle.</span>",
            unsafe_allow_html=True,
        )


# ════════════════════════════════════════════════════════════════════════════
# CONTAINER D — Candlestick chart
#   - Plotly dark theme  (template="plotly_dark")
#   - Range slider disabled  (rangeslider_visible=False)
#   - Full width  (use_container_width=True)
# ════════════════════════════════════════════════════════════════════════════
with st.container():
    st.markdown(
        "<div class='section-heading'>Price Chart — Last 120 Candles</div>",
        unsafe_allow_html=True,
    )

    chart_df = df.tail(120)

    fig = go.Figure()

    # Main candlestick trace
    fig.add_trace(go.Candlestick(
        x=chart_df.index,
        open=chart_df["Open"],
        high=chart_df["High"],
        low=chart_df["Low"],
        close=chart_df["Close"],
        name="Price",
        increasing_line_color="#34d399",   # green for up candles
        decreasing_line_color="#f87171",   # red  for down candles
        increasing_fillcolor="#34d399",
        decreasing_fillcolor="#f87171",
    ))

    # Overlay triangle markers wherever each pattern was detected
    MARKER_COLORS = {
        "Hammer":            "#60a5fa",
        "Doji":              "#fbbf24",
        "Bullish Engulfing": "#34d399",
        "Bearish Engulfing": "#f87171",
        "Shooting Star":     "#c084fc",
    }
    for name, stats in stats_all.items():
        fired_in_window = stats["fired_series"].loc[chart_df.index]
        hit_dates = fired_in_window[fired_in_window].index
        if len(hit_dates) == 0:
            continue
        fig.add_trace(go.Scatter(
            x=hit_dates,
            y=chart_df.loc[hit_dates, "Low"] * 0.993,
            mode="markers",
            marker=dict(
                symbol="triangle-up",
                size=11,
                color=MARKER_COLORS.get(name, "#ffffff"),
                line=dict(color="#0b0f19", width=1),
            ),
            name=name,
            hovertemplate=f"<b>{name}</b><br>%{{x}}<extra></extra>",
        ))

    # Chart layout — dark theme, no range slider
    fig.update_layout(
        template="plotly_dark",                # dark Plotly theme
        height=500,
        plot_bgcolor="#0f1623",
        paper_bgcolor="#0f1623",
        font=dict(family="Inter, sans-serif", color="#9ca3af", size=12),
        xaxis=dict(
            gridcolor="#1e2d40",
            showgrid=True,
            rangeslider_visible=False,         # range slider disabled
            tickfont=dict(color="#4b5563"),
        ),
        yaxis=dict(
            gridcolor="#1e2d40",
            showgrid=True,
            tickfont=dict(color="#4b5563"),
            side="right",                      # price axis on the right (like trading platforms)
        ),
        legend=dict(
            bgcolor="#111827",
            bordercolor="#1e2d40",
            borderwidth=1,
            font=dict(size=11),
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="left",
            x=0,
        ),
        margin=dict(l=0, r=0, t=36, b=0),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#111827", bordercolor="#1e2d40", font_size=12),
    )

    st.plotly_chart(fig, use_container_width=True)   # full width


# ════════════════════════════════════════════════════════════════════════════
# CONTAINER E — Pattern explanation for today's primary signal
# ════════════════════════════════════════════════════════════════════════════
with st.container():
    if primary:
        st.markdown(
            "<div class='section-heading'>Pattern Explanation</div>",
            unsafe_allow_html=True,
        )
        p_stats     = stats_all[primary]
        explanation = build_ai_explanation(primary, p_stats)
        p_sig       = p_stats["signal"]
        sig_color   = {"bullish": "#34d399", "bearish": "#f87171", "neutral": "#fbbf24"}[p_sig]

        st.markdown(
            f"<div style='font-size:0.75rem;font-weight:600;color:{sig_color};"
            f"text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.5rem'>"
            f"● {p_sig.capitalize()} signal — {primary}</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="explanation-box">{explanation}</div>',
            unsafe_allow_html=True,
        )


# ════════════════════════════════════════════════════════════════════════════
# CONTAINER F — Historical statistics (one expandable section per pattern)
# ════════════════════════════════════════════════════════════════════════════
with st.container():
    st.markdown(
        "<div class='section-heading'>Historical Statistics by Pattern</div>",
        unsafe_allow_html=True,
    )

    for name, stats in stats_all.items():
        sig    = stats["signal"]
        occ    = stats["occurrences"]
        wr     = stats["win_rate"]
        ar     = stats["avg_return"]
        ar_str = f"+{ar:.2f}%" if ar >= 0 else f"{ar:.2f}%"
        ar_cls = "bullish" if ar >= 0 else "bearish"
        wr_cls = "bullish" if wr >= 55 else ("bearish" if wr < 45 else "neutral")
        dot    = {"bullish": "🟢", "bearish": "🔴", "neutral": "🟡"}[sig]

        # Auto-expand the expander for patterns detected today
        is_today = name in latest_patterns

        with st.expander(
            f"{dot}  {name}" + ("  ← detected today" if is_today else ""),
            expanded=is_today,
        ):
            # 3 metric cards inside the expander
            sc1, sc2, sc3 = st.columns(3)

            with sc1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Occurrences</div>
                    <div class="metric-value">{occ}</div>
                    <div class="metric-sub">in selected period</div>
                </div>""", unsafe_allow_html=True)

            with sc2:
                wc = "bullish-card" if wr >= 55 else ("bearish-card" if wr < 45 else "neutral-card")
                st.markdown(f"""
                <div class="metric-card {wc}">
                    <div class="metric-label">Win Rate</div>
                    <div class="metric-value {wr_cls}">{wr}%</div>
                    <div class="metric-sub">of trades profitable</div>
                </div>""", unsafe_allow_html=True)

            with sc3:
                ac = "bullish-card" if ar >= 0 else "bearish-card"
                st.markdown(f"""
                <div class="metric-card {ac}">
                    <div class="metric-label">Avg Return (3 Days)</div>
                    <div class="metric-value {ar_cls}">{ar_str}</div>
                    <div class="metric-sub">mean forward return</div>
                </div>""", unsafe_allow_html=True)

            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

            # Plain-English explanation (generated by pattern_analysis.py)
            explanation = build_ai_explanation(name, stats)
            st.markdown(
                f'<div class="explanation-box">{explanation}</div>',
                unsafe_allow_html=True,
            )

            # ── Detailed statistics (nested expandable section) ──────────
            if stats["returns"] and len(stats["returns"]) >= 5:
                with st.expander("📊  Detailed return distribution", expanded=False):
                    ret_series = pd.Series(stats["returns"])

                    # 4 summary stat mini-cards
                    d1, d2, d3, d4 = st.columns(4)
                    detail_stats = [
                        ("Median Return", f"{ret_series.median():+.2f}%"),
                        ("Std Deviation", f"{ret_series.std():.2f}%"),
                        ("Best Trade",    f"{ret_series.max():+.2f}%"),
                        ("Worst Trade",   f"{ret_series.min():+.2f}%"),
                    ]
                    for col, (label, val) in zip([d1, d2, d3, d4], detail_stats):
                        with col:
                            st.markdown(f"""
                            <div class="metric-card">
                                <div class="metric-label">{label}</div>
                                <div class="metric-value" style="font-size:1.2rem">{val}</div>
                            </div>""", unsafe_allow_html=True)

                    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

                    # Return distribution histogram
                    fig_hist = go.Figure()
                    fig_hist.add_trace(go.Histogram(
                        x=ret_series,
                        nbinsx=20,
                        marker_color="#2563eb",
                        marker_line_color="#1e2d40",
                        marker_line_width=1,
                        opacity=0.85,
                        name="3-day returns",
                    ))
                    # Vertical breakeven line
                    fig_hist.add_vline(
                        x=0,
                        line_color="#f87171",
                        line_dash="dash",
                        line_width=1.5,
                        annotation_text=" breakeven",
                        annotation_font_color="#6b7280",
                        annotation_font_size=11,
                    )
                    fig_hist.update_layout(
                        template="plotly_dark",
                        height=220,
                        plot_bgcolor="#0f1623",
                        paper_bgcolor="#0f1623",
                        font=dict(family="Inter", color="#6b7280", size=11),
                        xaxis=dict(
                            title="3-day return (%)",
                            gridcolor="#1e2d40",
                            tickfont=dict(color="#4b5563"),
                        ),
                        yaxis=dict(
                            title="Count",
                            gridcolor="#1e2d40",
                            tickfont=dict(color="#4b5563"),
                        ),
                        margin=dict(l=0, r=0, t=10, b=0),
                        showlegend=False,
                        bargap=0.05,
                    )
                    st.plotly_chart(fig_hist, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════
# FOOTER
# ════════════════════════════════════════════════════════════════════════════
st.markdown(
    "<div class='dash-footer'>"
    "⚠️ <strong>Educational use only.</strong> "
    "Past pattern performance does not guarantee future results. "
    "This tool is designed to help students explore technical analysis concepts."
    "</div>",
    unsafe_allow_html=True,
)
