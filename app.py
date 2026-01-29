import streamlit as st
import pandas as pd
import plotly.express as px
from data_loader import CLINICS, get_competitors

# 設定頁面配置
st.set_page_config(
    page_title="中醫診所競品分析",
    page_icon="🏥",
    layout="wide"
)

# CSS 優化視覺
st.markdown("""
    <style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    st.title("🏥 中醫診所競品分析系統")

    # 取得 API Key
    try:
        api_key = st.secrets["6b51a088f6d4de92d73b3523951cfdf92022b8daab2c7f75e2eb262096d5e124"]
    except Exception:
        st.error("找不到 API Key，請確認 .streamlit/secrets.toml 設定正確。")
        return

    # 側邊欄：選擇診所
    with st.sidebar:
        st.header("設定")
        selected_name = st.selectbox("選擇診所", list(CLINICS.keys()))
    
    if selected_name:
        clinic_info = CLINICS[selected_name]
        st.header(f"📍 分析目標：{selected_name}")
        
        # 呼叫資料抓取函數
        with st.spinner('正在抓取競品資料...'):
            df = get_competitors(clinic_info["lat"], clinic_info["lng"], api_key)
            
        if not df.empty:
            # 標記我方診所 (簡單模糊比對)
            # 建立一個新欄位 '身份'，預設 '競爭對手'
            # 若店名包含選擇的診所名稱 (移除 '中醫' 後的比對可能更準，但這裡先試直接包含)
            # 使用者輸入的是 "高堂中醫"，搜尋結果可能是 "高堂中醫診所"
            
            # 定義判斷函式
            def identify_clinic(row_name):
                # 簡單正規化：移除 '診所'
                clean_target = selected_name.replace("診所", "")
                clean_row = row_name.replace("診所", "")
                if clean_target in clean_row:
                    return "我方診所"
                return "競爭對手"

            df["身份"] = df["店名"].apply(identify_clinic)
            
            # 若搜尋結果前五名都沒有自己，這是有可能的 (如果排名後段)
            # 這裡不特別補插資料，依據需求僅顯示 "local_results 中的前 5 名"
            
            # --- 顯示數據摘要 ---
            st.subheader("數據摘要")
            col1, col2 = st.columns(2)
            
            # 嘗試找出我方數據顯示
            my_data = df[df["身份"] == "我方診所"]
            if not my_data.empty:
                my_row = my_data.iloc[0]
                with col1:
                    st.metric("我方排名", f"第 {my_row['排名']} 名")
                with col2:
                    st.metric("我方星等", f"{my_row['星等']} ⭐ ({my_row['評論數']} 則評論)")
            else:
                st.warning(f"⚠️ 在前 5 名搜尋結果中未發現「{selected_name}」。")

            st.divider()

            # --- 繪製散佈圖 ---
            st.subheader("📊 星等 vs 評論數 散佈圖")
            
            if not df.empty:
                fig = px.scatter(
                    df,
                    x="星等",
                    y="評論數",
                    color="身份",
                    hover_data=["店名", "排名"],
                    title=f"{selected_name} 周邊競品分佈",
                    color_discrete_map={"我方診所": "#FF4B4B", "競爭對手": "#4169E1"},
                    size="評論數", # 讓點的大小跟評論數成正比，增加視覺豐富度
                    size_max=40
                )
                # 讓 X 軸範圍稍微寬一點以免貼邊
                fig.update_layout(xaxis_range=[0, 5.5])
                st.plotly_chart(fig, use_container_width=True)

            # --- 顯示詳細資料表 ---
            st.subheader("📋 詳細資料")
            # 調整欄位順序
            if not df.empty:
                display_df = df[["排名", "店名", "星等", "評論數", "身份"]].sort_values("排名")
                st.dataframe(display_df, use_container_width=True, hide_index=True)

        else:
            st.warning("查無資料或 API 額度不足。")

if __name__ == "__main__":
    main()
