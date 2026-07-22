import streamlit as st
import pandas as pd
import os
from sqlalchemy import create_engine, text
from datetime import datetime
import psycopg2

st.set_page_config(page_title="⚽ 足球推演数据库", layout="wide")

# 从环境变量读取 Supabase 数据库连接信息
DB_URL = f"postgresql://postgres:{os.getenv('SUPABASE_PASSWORD')}@{os.getenv('SUPABASE_HOST')}:5432/postgres"

engine = create_engine(DB_URL)

def run_query(query, params=None):
    with engine.connect() as conn:
        if params:
            result = conn.execute(text(query), params)
        else:
            result = conn.execute(text(query))
        if result.returns_rows:
            return result.fetchall()
        else:
            conn.commit()
            return None

def run_query_df(query, params=None):
    return pd.read_sql(query, engine, params=params)

st.title("⚽ 足球推演数据库管理系统")

menu = st.sidebar.radio("导航菜单", ["📊 推演总览", "📝 新增推演", "📋 历史记录", "📁 球队管理", "⚽ 球员管理", "📊 复盘统计"])

if menu == "📊 推演总览":
    st.subheader("近10场推演记录")
    df = run_query_df("""
        SELECT p.id, m.match_date, t1.name AS home, t2.name AS away, 
               p.pred_home_score, p.pred_away_score,
               p.actual_home_score, p.actual_away_score, 
               p.is_hit, p.confidence
        FROM predictions p
        JOIN matches m ON p.match_id = m.id
        JOIN teams t1 ON m.home_team_id = t1.id
        JOIN teams t2 ON m.away_team_id = t2.id
        ORDER BY p.pred_date DESC LIMIT 10
    """)
    st.dataframe(df)

elif menu == "📁 球队管理":
    st.subheader("添加新球队")
    with st.form("add_team"):
        name = st.text_input("球队名称")
        league = st.text_input("所属联赛")
        home_color = st.text_input("主场颜色")
        away_color = st.text_input("客场颜色")
        wuxing = st.text_input("五行属性")
        submitted = st.form_submit_button("添加球队")
        if submitted and name:
            run_query(
                "INSERT INTO teams (name, league, home_color, away_color, wuxing) VALUES (:name, :league, :home_color, :away_color, :wuxing)",
                {"name": name, "league": league, "home_color": home_color, "away_color": away_color, "wuxing": wuxing}
            )
            st.success(f"球队 {name} 已添加！")

    st.subheader("现有球队")
    df_teams = run_query_df("SELECT * FROM teams ORDER BY name")
    st.dataframe(df_teams)

elif menu == "📊 复盘统计":
    st.subheader("总体命中率")
    rows = run_query("SELECT COUNT(*) AS total, SUM(CASE WHEN is_hit THEN 1 ELSE 0 END) AS hits FROM predictions")
    if rows:
        total, hits = rows[0]
        if total and total > 0:
            hit_rate = hits / total * 100
            st.metric("总推演场次", total)
            st.metric("命中场次", hits or 0)
            st.metric("命中率", f"{hit_rate:.1f}%")
        else:
            st.info("暂无推演记录")

# 其余菜单（新增推演、历史记录、球员管理）可根据需要继续补充
