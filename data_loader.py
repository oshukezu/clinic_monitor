import streamlit as st
from serpapi import GoogleSearch
import pandas as pd

# 診所座標資料
CLINICS = {
    "高堂中醫": {"lat": 24.17766189594869, "lng": 120.65779797277963}, # Fixed typo: 1120 -> 120
    "達春中醫": {"lat": 24.141324780508835, "lng": 120.71890942277749},
    "永康中醫": {"lat": 24.218685339899235, "lng": 120.66500772606646},
    "祥順中醫": {"lat": 24.110931501778026, "lng": 120.54965128794603},
    "祐生中醫": {"lat": 24.138505089517263, "lng": 120.68286050815652},
    "耕心中醫": {"lat": 24.249992057506148, "lng": 120.64990152583641},
    "文心中醫": {"lat": 23.82984498934362, "lng": 120.46038737749569},
    "蕙心中醫": {"lat": 24.183612679356635, "lng": 120.7103263267566},
    "姥芝瑞中醫": {"lat": 24.156048822921335, "lng": 120.69247354466657},
    "德心中醫": {"lat": 24.184865440500257, "lng": 120.7062064539666},
    "祥鶴中醫": {"lat": 24.161060875784358, "lng": 120.69110025373655},
}

@st.cache_data(ttl=86400)
def get_competitors(lat, lng, api_key):
    """
    使用 SerpApi 抓取指定座標周邊的中醫診所資料。
    """
    if not api_key:
        st.error("未設定 SerpApi Key")
        return pd.DataFrame()

    params = {
        "engine": "google_maps",
        "q": "中醫",
        "ll": f"@{lat},{lng},14z",
        "type": "search",
        "api_key": api_key,
        "hl": "zh-TW",
        "gl": "tw"
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        local_results = results.get("local_results", [])
        
        data = []
        # 提取前 5 名
        for item in local_results[:5]:
            data.append({
                "店名": item.get("title"),
                "星等": item.get("rating", 0),
                "評論數": item.get("reviews", 0),
                "排名": item.get("position", 0),
                "type": "competitor" # 預設標記為競爭對手
            })
            
        return pd.DataFrame(data)

    except Exception as e:
        st.error(f"API 呼叫失敗: {e}")
        return pd.DataFrame()
