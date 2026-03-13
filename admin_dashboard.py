import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from analytics_service import (
    get_total_stats, get_persona_distribution, get_weekly_signups,
    get_dimension_averages, get_top_catalog_items, search_user_profile,
    get_budget_by_style
)

# Page Config
st.set_page_config(page_title="PreferenceAI Admin", layout="wide", page_icon="💎")

# Custom CSS for Premium Look
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1f2937; padding: 20px; border-radius: 10px; border: 1px solid #374151; }
    div[data-testid="stMetricValue"] { color: #818cf8; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("💎 Jewelry Preference Analytics")
st.markdown("Monitor user trends, personas, and system performance.")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Admin Actions")
    user_email = st.text_input("Find User Profile (Email)")
    if st.button("Search User"):
        profile = search_user_profile(user_email)
        if profile:
            st.success(f"Found {user_email}")
            st.json(profile)
        else:
            st.error("User not found.")
    
    st.divider()
    st.info("Log in as Superuser to modify the Catalog in Django Admin.")

# --- TOP METRICS ---
stats = get_total_stats()
col1, col2, col3, col4 = st.columns(4)
with col1: st.metric("Unique Users", stats["total_users"])
with col2: st.metric("Profiles Generated", stats["total_recommendations"])
with col3: st.metric("Likability Actions", stats["total_swipes"])
with col4: st.metric("Catalog Items", stats["total_catalog_items"])

st.divider()

# --- ROW 1: DISTRIBUTION & TRENDS ---
row1_col1, row1_col2 = st.columns([1, 1])

with row1_col1:
    st.subheader("🎭 Persona Distribution")
    df_persona = get_persona_distribution()
    if not df_persona.empty:
        fig_pie = px.pie(df_persona, values='count', names='jewelry_persona', 
                         hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_pie.update_layout(template="plotly_dark", margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.write("No persona data available yet.")

with row1_col2:
    st.subheader("📈 User Growth (8 Weeks)")
    df_growth = get_weekly_signups()
    if not df_growth.empty:
        fig_line = px.line(df_growth, x="date", y="count", markers=True)
        fig_line.update_traces(line_color="#818cf8", line_width=3)
        fig_line.update_layout(template="plotly_dark", yaxis_title="Signups", xaxis_title="Date")
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.write("No signup data to show.")

st.divider()

# --- ROW 2: DIMENSIONS & BUDGET ---
row2_col1, row2_col2 = st.columns([1, 1])

with row2_col1:
    st.subheader("🕸️ Global Dimension Averages")
    df_dims = get_dimension_averages()
    if not df_dims.empty:
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=df_dims['Score'],
            theta=df_dims['Dimension'],
            fill='toself',
            name='Global Average',
            line_color='#34d399'
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            template="plotly_dark",
            showlegend=False
        )
        st.plotly_chart(fig_radar, use_container_width=True)

with row2_col2:
    st.subheader("💰 Budget vs Style by Persona")
    df_bs = get_budget_by_style()
    if not df_bs.empty:
        fig_bar = px.bar(df_bs, x="jewelry_persona", y=["avg_budget", "avg_style"],
                         barmode='group', color_discrete_map={"avg_budget": "#f87171", "avg_style": "#818cf8"})
        fig_bar.update_layout(template="plotly_dark", yaxis_title="Score (0-100)")
        st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

# --- ROW 3: TOP ITEMS ---
st.subheader("🌟 Most Liked Jewelry (Top 10)")
df_top = get_top_catalog_items()
if not df_top.empty:
    st.dataframe(df_top, use_container_width=True)
else:
    st.write("No likes recorded yet.")
