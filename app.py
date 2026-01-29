import streamlit as st
import pandas as pd
import plotly.express as px
from rank_tracker import check_rankings
from clinics_config import CLINICS
from seo_config import KEYWORDS

# 設定頁面配置
st.set_page_config(
    page_title="高堂體系周邊診所評價系統",
    page_icon="🏥",
    layout="wide"
)

# CSS 優化視覺 (特別針對 Table 和 Metric)
st.markdown("""
    <style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    div[data-testid="stDataFrame"] {
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    st.title("🏥 高堂體系周邊診所評價系統")
    
    # 取得 API Key
    try:
        api_key = st.secrets["SERPAPI_KEY"]
    except Exception:
        st.error("找不到 API Key，請確認 .streamlit/secrets.toml 設定正確。")
        return

    st.markdown(f"""
    此系統監控 **{len(CLINICS)}** 家診所 x **{len(KEYWORDS)}** 個關鍵字 的搜尋排名。
    搜尋範圍：以各診所為中心，半徑約 1 公里 (Zoom 15z)。
    """)
    
    # Action Area
    col1, col2 = st.columns([1, 4])
    with col1:
        start_btn = st.button("🚀 開始每週排名檢測", type="primary")
    with col2:
        st.caption("⚠️ 注意：每次完整檢測會消耗約 55 次 API 呼叫。結果會快取 7 天，請勿擔心重複點擊。")

    # 檢查是否觸發過或已有快取資料
    # 這裡我們直接呼叫 check_rankings，因為它有 @st.cache_data 保護
    # 只有當使用者點擊按鈕，或者之前已經跑過有快取時，才顯示結果
    # 但為了避免誤觸，我們還是用按鈕當作一個 explicit trigger，
    # 不過為了讓介面友善，如果 session_state 註記過已執行，就直接顯示
    
    if start_btn:
        st.session_state["has_run"] = True
        
    if st.session_state.get("has_run", False):
        try:
            with st.spinner("正在進行 SEO 排名分析，這可能需要幾分鐘..."):
                raw_data = check_rankings(api_key)
                df = pd.DataFrame(raw_data)
                
            if df.empty:
                st.warning("查無資料，請確認 API 狀態。")
                return

            st.divider()
            
            # --- 1. 排名矩陣熱力圖 (Ranking Matrix) ---
            st.subheader("📊 排名矩陣 (Heatmap)")
            
            # 轉換資料格式為 Pivot Table: Index=診所, Columns=關鍵字, Values=排名
            pivot_df = df.pivot(index="clinic", columns="keyword", values="rank")
            
            # 為了讓 Heatmap 顏色正確，數值需為數字。 '20+' 我們在 raw data 存的是 21
            # 顏色邏輯：1(綠) -> 10(黃) -> 20+(紅)
            fig = px.imshow(
                pivot_df,
                labels=dict(x="關鍵字", y="診所", color="排名"),
                x=KEYWORDS,
                y=list(CLINICS.keys()),
                text_auto=True,
                color_continuous_scale="RdYlGn_r", # 紅黃綠 反轉 (排名越小越綠)
                range_color=[1, 20] # 顏色範圍鎖定在 1~20
            )
            fig.update_layout(height=600)
            st.plotly_chart(fig, use_container_width=True)

            # --- 2. 詳細競爭對手分析 ---
            st.divider()
            st.subheader("🕵️ 詳細競品分析")
            
            selected_clinic = st.selectbox("請選擇要查看的診所：", list(CLINICS.keys()))
            
            if selected_clinic:
                clinic_df = df[df["clinic"] == selected_clinic]
                
                # 整理顯示用的表格
                display_rows = []
                for _, row in clinic_df.iterrows():
                    competitors_str = ", ".join(row["top_competitors"])
                    display_rows.append({
                        "關鍵字": row["keyword"],
                        "我方排名": row["rank_display"],
                        "前三名強敵": competitors_str
                    })
                
                if display_rows:
                    st.table(pd.DataFrame(display_rows))
                else:
                    st.info("該診所尚無分析資料。")

        except Exception as e:
            st.error(f"執行失敗: {str(e)}")

if __name__ == "__main__":
    main()
