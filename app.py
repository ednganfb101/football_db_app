import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

# ---------- 从 secrets 读取 Supabase 配置 ----------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_ANON_KEY"]

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# ---------- 通用 REST 调用函数 ----------
def supabase_get(table, params=None):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    if params:
        # 构造查询参数
        query_string = "&".join([f"{k}=eq.{v}" if not isinstance(v, dict) else "" for k,v in params.items()])
        # 简单处理，只支持简单等式
    # 简化版：直接获取全部
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json()
    else:
        st.error(f"查询失败: {resp.text}")
        return []

def supabase_post(table, data):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    resp = requests.post(url, headers=headers, json=data)
    if resp.status_code in [200, 201]:
        return resp.json()
    else:
        st.error(f"插入失败: {resp.text}")
        return None

def supabase_delete(table, id):
    url = f"{SUPABASE_URL}/rest/v1/{table}?id=eq.{id}"
    resp = requests.delete(url, headers=headers)
    if resp.status_code == 200:
        return True
    else:
        st.error(f"删除失败: {resp.text}")
        return False

# ---------- 页面配置 ----------
st.set_page_config(page_title="⚽ 足球推演数据库", layout="wide")
st.title("⚽ 足球推演数据库管理系统")

# ---------- 侧边栏导航 ----------
menu = st.sidebar.radio(
    "导航菜单",
    ["📊 推演总览", "📁 球队管理", "📋 历史记录", "📊 复盘统计"]
)

# ---------- 推演总览 ----------
if menu == "📊 推演总览":
    st.subheader("近10场推演记录")
    # 获取推演数据（需联表查询，用两次请求简化）
    preds = supabase_get("predictions", {"order": "pred_date.desc", "limit": "10"})
    if preds:
        # 提取比赛信息
        rows = []
        for p in preds:
            match = supabase_get("matches", {"id": p["match_id"]})
            if match:
                m = match[0]
                home_team = supabase_get("teams", {"id": m["home_team_id"]})
                away_team = supabase_get("teams", {"id": m["away_team_id"]})
                rows.append({
                    "日期": m["match_date"],
                    "主队": home_team[0]["name"] if home_team else "?",
                    "客队": away_team[0]["name"] if away_team else "?",
                    "预测比分": f"{p['pred_home_score']}-{p['pred_away_score']}",
                    "实际比分": f"{p.get('actual_home_score','')}-{p.get('actual_away_score','')}",
                    "命中": "✅" if p.get("is_hit") else "❌" if p.get("actual_home_score") is not None else "待定",
                    "信心": p.get("confidence", "")
                })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("暂无推演记录，请先添加球队和比赛。")

# ---------- 球队管理 ----------
elif menu == "📁 球队管理":
    st.subheader("添加新球队")
    with st.form("add_team"):
        name = st.text_input("球队名称 *")
        league = st.text_input("所属联赛")
        home_color = st.text_input("主场颜色")
        away_color = st.text_input("客场颜色")
        wuxing = st.text_input("五行属性")
        submitted = st.form_submit_button("添加球队")
        if submitted and name:
            data = {
                "name": name,
                "league": league,
                "home_color": home_color,
                "away_color": away_color,
                "wuxing": wuxing
            }
            result = supabase_post("teams", data)
            if result:
                st.success(f"球队 {name} 已添加！")

    st.subheader("现有球队")
    teams = supabase_get("teams")
    if teams:
        df_teams = pd.DataFrame(teams)
        st.dataframe(df_teams, use_container_width=True)

# ---------- 历史记录 ----------
elif menu == "📋 历史记录":
    st.subheader("全部推演记录")
    preds = supabase_get("predictions", {"order": "pred_date.desc"})
    if preds:
        rows = []
        for p in preds:
            match = supabase_get("matches", {"id": p["match_id"]})
            if match:
                m = match[0]
                home_team = supabase_get("teams", {"id": m["home_team_id"]})
                away_team = supabase_get("teams", {"id": m["away_team_id"]})
                rows.append({
                    "日期": m["match_date"],
                    "主队": home_team[0]["name"] if home_team else "?",
                    "客队": away_team[0]["name"] if away_team else "?",
                    "预测": f"{p['pred_home_score']}-{p['pred_away_score']}",
                    "实际": f"{p.get('actual_home_score','')}-{p.get('actual_away_score','')}",
                    "命中": "✅" if p.get("is_hit") else "❌" if p.get("actual_home_score") is not None else "待定",
                    "信心": p.get("confidence", "")
                })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("暂无历史记录。")

# ---------- 复盘统计 ----------
elif menu == "📊 复盘统计":
    st.subheader("总体命中率")
    preds = supabase_get("predictions")
    if preds:
        total = len(preds)
        hits = sum(1 for p in preds if p.get("is_hit"))
        hit_rate = hits / total * 100 if total else 0
        col1, col2, col3 = st.columns(3)
        col1.metric("总推演场次", total)
        col2.metric("命中场次", hits)
        col3.metric("命中率", f"{hit_rate:.1f}%")
    else:
        st.info("暂无推演数据，请先录入。")
