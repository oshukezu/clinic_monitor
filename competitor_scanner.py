# competitor_scanner.py
import os
import streamlit as st
from serpapi import GoogleSearch
import pandas as pd
from typing import List, Dict, Optional
import time

# 嘗試載入 .env 變數 (即使在 Streamlit Cloud 可能無效，開發時有用)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def get_api_key() -> Optional[str]:
    """獲取 API Key，優先檢查 Streamlit Secrets，其次環境變數"""
    # 這裡預留給 Streamlit Secrets 或環境變數
    # 如果使用者在 sidebar 輸入 key 也可以從那邊傳入，但本函數主要從環境讀取
    return os.getenv("SERPAPI_KEY")

@st.cache_data(ttl=86400)
def scan_competitors(clinic_name: str, lat: float, lng: float, api_key: str = None) -> List[Dict]:
    """
    掃描指定座標周邊的中醫診所競爭狀況。
    
    Args:
        clinic_name (str): 我方診所名稱 (用於識別)。
        lat (float): 緯度。
        lng (float): 經度。
        api_key (str): SerpApi Key。
        
    Returns:
        List[Dict]: 包含我方與前 4 名競品的資料列表。
    """
    
    # 如果沒有 Key，回傳模擬資料
    if not api_key:
        return _get_mock_data(clinic_name)

    params = {
        "engine": "google_maps",
        "q": "中醫",
        "ll": f"@{lat},{lng},15z",
        "type": "search",
        "api_key": api_key,
        "hl": "zh-TW", # 設定語言為繁體中文
        "gl": "tw"     # 設定地區為台灣
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        
        local_results = results.get("local_results", [])
        
        # 資料清洗與篩選
        my_clinic_data = None
        competitors = []
        
        for result in local_results:
            title = result.get("title", "")
            data = {
                "name": title,
                "rating": result.get("rating", 0.0),
                "reviews": result.get("reviews", 0),
                "position": result.get("position", 999), # 若無排名則設為後段
                "address": result.get("address", ""),
                "place_id": result.get("place_id", ""),
                "is_me": False
            }
            
            # 簡易模糊比對：若搜尋結果名稱包含我方設定的名稱 (去除常見後綴以免誤判)
            # 例如 "高堂中醫" vs "高堂中醫診所"
            clean_my_name = clinic_name.replace("診所", "").replace("中醫", "")
            clean_result_name = title.replace("診所", "").replace("中醫", "")
            
            if clean_my_name in clean_result_name:
                data["is_me"] = True
                my_clinic_data = data
            else:
                competitors.append(data)
        
        # 確保資料數量 (取前 4 名競品)
        final_list = []
        if my_clinic_data:
            final_list.append(my_clinic_data)
        else:
            # 若搜尋結果沒找到自己 (可能排名太後面)，插入一個假的我方資料提醒用戶
            final_list.append({
                "name": f"{clinic_name} (未在前 20 名)",
                "rating": 0.0,
                "reviews": 0,
                "position": 999,
                "is_me": True
            })
            
        # 排序競品並取前 4
        # 這裡依據 position 排序，如果 API 沒回傳 position，則依據原始順序 (通常也是排名順)
        competitors.sort(key=lambda x: x["position"])
        final_list.extend(competitors[:4])
        
        return final_list

    except Exception as e:
        st.error(f"API 呼叫失敗: {str(e)}")
        # 失敗時回傳模擬資料以免畫面壞掉
        return _get_mock_data(clinic_name)

def _get_mock_data(clinic_name: str) -> List[Dict]:
    """產生測試用的模擬資料"""
    import random
    
    # 我方
    results = [{
        "name": clinic_name,
        "rating": round(random.uniform(3.5, 4.9), 1),
        "reviews": random.randint(50, 500),
        "position": random.randint(1, 10),
        "is_me": True,
        "place_id": "mock_id_me"
    }]
    
    # 競品
    competitor_names = ["仁心堂中醫", "回春中醫", "保生大帝中醫", "華佗中醫"]
    for i, name in enumerate(competitor_names):
        results.append({
            "name": name,
            "rating": round(random.uniform(3.0, 5.0), 1),
            "reviews": random.randint(10, 800),
            "position": i + 1 if i < results[0]["position"] else i + 2, # 簡單錯開排名
            "is_me": False,
            "place_id": f"mock_id_{i}"
        })
        
    # 根據排名重新排序
    results.sort(key=lambda x: x["position"])
    return results
