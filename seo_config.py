# seo_config.py

# SEO 監控關鍵字列表
# 建議不要超過 5-10 個，以免 API 呼叫次數過多
KEYWORDS = [
    "中醫",
    "針灸",
    "傷科",
    "過敏",
    "轉骨"
]

# 搜尋半徑參數
# Google Maps 主要是用 Zoom Level (z) 來控制顯示範圍
# 15z 大約對應街道級別，適合模擬方圓 1 公里的 Local Search
SEARCH_ZOOM = "15z"

# 快取時間 (秒)
# 604800 秒 = 7 天
CACHE_TTL = 604800
