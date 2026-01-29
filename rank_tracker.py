# rank_tracker.py
import streamlit as st
from serpapi import GoogleSearch
import pandas as pd
import time
from typing import List, Dict, Any

# 匯入設定檔
from clinics_config import CLINICS
from seo_config import KEYWORDS, SEARCH_ZOOM, CACHE_TTL

@st.cache_data(ttl=CACHE_TTL)
def check_rankings(api_key: str) -> List[Dict[str, Any]]:
    """
    主要核心函數：檢查所有診所在所有關鍵字的排名。
    此函數會被快取 (預設 7 天)，以節省 API 費用。
    """
    
    if not api_key:
        raise ValueError("請先設定 API Key")

    results_data = []
    total_checks = len(CLINICS) * len(KEYWORDS)
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    current_idx = 0
    
    print(f"DEBUG: Starting SEO check. Total calls estimated: {total_checks}", flush=True)

    for clinic_name, info in CLINICS.items():
        lat = info["lat"]
        lng = info["lng"]
        
        for keyword in KEYWORDS:
            current_idx += 1
            status_text.text(f"正在分析 ({current_idx}/{total_checks}): {clinic_name} - {keyword}...")
            progress_bar.progress(current_idx / total_checks)
            
            try:
                # 執行單次搜尋
                rank_data = _fetch_single_rank(clinic_name, keyword, lat, lng, api_key)
                results_data.append(rank_data)
                
                # 避免太過頻繁呼叫被擋 (雖然 SerpApi 比較沒這問題，但保守起見)
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error checking {clinic_name} - {keyword}: {e}", flush=True)
                # 發生錯誤時記錄一個失敗的結果，以免中斷整個流程
                results_data.append({
                   "clinic": clinic_name,
                   "keyword": keyword,
                   "rank": 999, # 錯誤代碼
                   "rank_display": "Error",
                   "top_competitors": []
                })

    status_text.text("分析完成！")
    progress_bar.empty()
    
    return results_data

def _fetch_single_rank(my_clinic_name: str, keyword: str, lat: float, lng: float, api_key: str) -> Dict[str, Any]:
    """
    針對單一診所、單一關鍵字執行搜尋並解析結果。
    """
    params = {
        "engine": "google_maps",
        "q": keyword,
        "ll": f"@{lat},{lng},{SEARCH_ZOOM}",
        "type": "search",
        "api_key": api_key,
        "hl": "zh-TW",
        "gl": "tw",
        "start": 0 # 只抓第一頁 (前 20 名)
    }
    
    search = GoogleSearch(params)
    results = search.get_dict()
    
    if "error" in results:
        raise Exception(f"SerpApi Error: {results['error']}")
        
    local_results = results.get("local_results", [])
    
    # 初始化回傳資料
    data = {
        "clinic": my_clinic_name,
        "keyword": keyword,
        "rank": 21,         # 預設 21 (代表 20名以外)
        "rank_display": "20+", 
        "top_competitors": [] # 前 3 名競爭對手
    }
    
    # 1. 抓取前 3 名競爭對手 (不論有無包含自己，先抓前 3 顯示用)
    competitors = []
    for item in local_results[:3]:
        competitors.append(f"{item.get('title')} ({item.get('rating', 'N/A')}⭐)")
    data["top_competitors"] = competitors

    # 2. 判斷我方排名
    # 進行模糊比對：移除 "診所"、"中醫" 後進行包含檢查
    clean_my_name = my_clinic_name.replace("診所", "").replace("中醫", "")
    
    for item in local_results:
        position = item.get("position", 0)
        title = item.get("title", "")
        clean_title = title.replace("診所", "").replace("中醫", "")
        
        # 只要店名包含我方核心名稱，就視為找到
        if clean_my_name in clean_title:
            data["rank"] = position
            data["rank_display"] = str(position)
            break
            
    return data
