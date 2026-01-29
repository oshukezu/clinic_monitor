# app.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from clinics_config import CLINICS
from competitor_scanner import scan_competitors, get_api_key

# 設定頁面配置
st.set_page_config(
    page_title="中醫診所區域競品監測系統",
    page_icon="🏥",
    layout="wide"
)

# 載入 API Key
api_key = get_api_key()

# CSS 優化視覺
st.markdown("""
    <style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    .warning-row {
        background-color: #ffe6e6 !important;
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    st.title("🏥 中醫診所區域競品監測系統")
    
    # 側邊欄：選擇模式
    with st.sidebar:
        st.header("功能選單")
        mode = st.radio("選擇檢視模式", ["全域戰報", "單點戰區分析"])
        
        if mode == "單點戰區分析":
            selected_clinic_name = st.selectbox(
                "選擇診所",
                [c["name"] for c in CLINICS]
            )
            selected_clinic = next(c for c in CLINICS if c["name"] == selected_clinic_name)
    
    if mode == "全域戰報":
        show_global_dashboard()
    else:
        show_local_analysis(selected_clinic)

def show_global_dashboard():
    st.header("🏢 全域戰報：所有診所排名概況")
    
    # 掃描所有診所 (這裡可能會花一點時間，但因為有 cache 應該還好)
    # 為了避免 API 瞬間爆量，實際生產環境可能需要非同步或預先跑批次
    # 這裡 demo 直接跑迴圈
    
    if not api_key:
        st.warning("查無 SERPAPI_KEY，目前使用模擬資料展示。")
    
    results_summary = []
    
    progress_bar = st.progress(0)
    
    for i, clinic in enumerate(CLINICS):
        data = scan_competitors(clinic["name"], clinic["latitude"], clinic["longitude"], api_key)
        
        # 找出我方資料
        my_data = next((d for d in data if d.get("is_me")), None)
        
        if my_data:
            results_summary.append({
                "診所名稱": clinic["name"],
                "城市": clinic["city"],
                "區域排名": my_data["position"],
                "星等": my_data["rating"],
                "評論數": my_data["reviews"],
                "狀態": "⚠️" if (my_data["rating"] < 4.0 or my_data["position"] > 3) else "✅"
            })
        progress_bar.progress((i + 1) / len(CLINICS))
        
    df = pd.DataFrame(results_summary)
    
    # 顯示指標
    col1, col2, col3 = st.columns(3)
    avg_rating = df["星等"].mean()
    avg_rank = df["區域排名"].mean()
    risk_count = df[df["狀態"] == "⚠️"].shape[0]
    
    col1.metric("平均星等", f"{avg_rating:.2f}")
    col2.metric("平均區域排名", f"{avg_rank:.1f}")
    col3.metric("需注意診所數", risk_count, delta_color="inverse")
    
    # 顯示表格，Highlight 警示項目
    st.subheader("詳細數據")
    st.dataframe(
        df.style.map(lambda x: 'color: red; font-weight: bold;' if x == "⚠️" else None, subset=['狀態']),
        use_container_width=True,
        hide_index=True
    )
    
    # 顯示警示診所的具體原因
    if risk_count > 0:
        st.subheader("🚨 警示診所清單")
        risky_clinics = df[df["狀態"] == "⚠️"]
        for _, row in risky_clinics.iterrows():
            reasons = []
            if row["星等"] < 4.0:
                reasons.append(f"星等過低 ({row['星等']})")
            if row["區域排名"] > 3:
                reasons.append(f"排名落後 (第 {row['區域排名']} 名)")
            
            st.error(f"**{row['診所名稱']} ({row['城市']})**: {', '.join(reasons)}")

def show_local_analysis(clinic):
    st.header(f"📍 單點戰區分析：{clinic['name']}")
    
    data = scan_competitors(clinic["name"], clinic["latitude"], clinic["longitude"], api_key)
    
    if not data:
        st.error("無法取得數據")
        return

    # 分離我方與競品
    my_data = next((d for d in data if d.get("is_me")), None)
    competitors = [d for d in data if not d.get("is_me")]
    
    if not my_data:
        st.error("在此區域搜尋不到我方診所資料")
        return

    #上半部：我方表現
    col1, col2, col3 = st.columns(3)
    col1.metric("目前星等", f"{my_data['rating']} ⭐")
    col2.metric("總評論數", f"{my_data['reviews']} 💬")
    col3.metric("區域排名", f"第 {my_data['position']} 名")
    
    st.divider()
    
    # 圖表分析
    st.subheader("📊 競爭力分析")
    
    # 準備圖表資料
    chart_data = []
    # 加入我方
    chart_data.append({
        "Name": "我方 (" + my_data["name"] + ")",
        "Rating": my_data["rating"],
        "Reviews": my_data["reviews"],
        "Type": "Me"
    })
    # 加入競品
    for c in competitors:
        chart_data.append({
            "Name": c["name"],
            "Rating": c["rating"],
            "Reviews": c["reviews"],
            "Type": "Competitor"
        })
        
    df_chart = pd.DataFrame(chart_data)
    
    # 雙軸圖表：星等 vs 評論數
    fig = go.Figure()
    
    # 星等 (Bar)
    fig.add_trace(go.Bar(
        x=df_chart['Name'],
        y=df_chart['Rating'],
        name='星等',
        marker_color=['#FF4B4B' if x == 'Me' else '#808080' for x in df_chart['Type']]
    ))
    
    # 評論數 (Line/Scatter on secondary y-axis) - 改用 Scatter 點或另外一個 Bar，避免太亂
    # 這裡為了簡單，用並排 Bar
    
    # 重新構建為 Plotly Express 可能更簡單，但要客製化顏色
    fig = px.bar(
        df_chart, 
        x='Name', 
        y=['Rating'], 
        barmode='group',
        title="星等比較 (紅色為我方)",
        color='Type',
        color_discrete_map={'Me': '#FF4B4B', 'Competitor': '#A0A0A0'}
    )
    fig.update_yaxes(range=[0, 5])
    st.plotly_chart(fig, use_container_width=True)
    
    # 評論數比較
    fig2 = px.bar(
        df_chart,
        x='Name',
        y='Reviews',
        title="評論數比較",
        color='Type',
        color_discrete_map={'Me': '#FF4B4B', 'Competitor': '#A0A0A0'}
    )
    st.plotly_chart(fig2, use_container_width=True)

    # 詳細列表
    st.subheader("📋 區域競品詳細清單")
    
    # 整理表格資料
    table_data = []
    # 合併排序
    all_shops = [my_data] + competitors
    all_shops.sort(key=lambda x: x["position"])
    
    for shop in all_shops:
        row = {
            "排名": shop["position"],
            "名稱": shop["name"],
            "星等": shop["rating"],
            "評論數": shop["reviews"],
            "Google Maps 連結": f"https://www.google.com/maps/place/?q=place_id:{shop.get('place_id', '')}"
        }
        table_data.append(row)
        
    df_table = pd.DataFrame(table_data)
    
    st.dataframe(
        df_table,
        column_config={
            "Google Maps 連結": st.column_config.LinkColumn("連結", display_text="前往地圖")
        },
        use_container_width=True,
        hide_index=True
    )

if __name__ == "__main__":
    main()
