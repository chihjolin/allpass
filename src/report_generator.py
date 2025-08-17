# -*- coding: utf-8 -*-
"""
使用 LangChain 和 Google Gemini 模型的個人化登山行程報告生成器
分析使用者在行程中的實際表現，並結合 GPX 特徵，生成一份客觀且具深度的專業分析報告。
"""
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config import GOOGLE_API_KEY

# --- 數據準備 ---
def fetch_hiking_data(gpx_upload_id: int) -> dict:
    """
    模擬函數：從資料庫獲取數據並進行特徵工程。
    在真實應用中，這裡會包含 SQLAlchemy 或 psycopg2 的查詢邏輯。
    """
    print(f"INFO: 正在為 gpx_upload_id: {gpx_upload_id} 準備數據...")
    # TODO: 未來實作真實的資料庫查詢與特徵計算

    # 模擬一份針對「雪山主東峰」行程的、包含進階特徵的數據包
    return {
        # 基本資訊
        "user_name": "凱琳",
        "trail_name": "雪山主東峰線",
        "hike_date": "2025-08-10",
        "weather_conditions": "上午晴朗，下午轉為雲霧繚繞",
        
        # 使用者表現數據
        "total_distance_km": 21.8,
        "total_duration_hours": 10.5,
        "moving_duration_hours": 8.5,
        "resting_duration_hours": 2.0,
        "avg_speed_kmh": 2.56, # (21.8km / 8.5h)
        
        # 官方路線數據
        "official_duration_hours": 12.0,
        "official_elevation_gain_m": 1350,

        # 進階特徵數據
        "elevation_change": 1344,               # 總爬升 (公尺)
        "elevation_range": "2550m - 3886m",     # 海拔範圍
        "max_elevation_m": 3886,
        "slope_std_dev": 12.5,                  # 坡度標準差 (數值越大，坡度起伏越多變)
        "slope_variance": 156.25,               # 坡度變異數 (數值極高，代表地形極具挑戰)
        "max_slope": 35.2,                      # 最大坡度 (超過30度已屬陡峭)
        "slope_freq_dist": "主要分布於 15-25 度之間", # 坡度分布頻率
        "terrain_roughness": 7.8,               # 地形粗糙度 (1-10，越高代表越崎嶇不平)
        "max_slope_time_diff": "黑森林水源地至圈谷段", # 最大坡度高低時間差發生的路段
        "high_elevation": True,                 # 是否進入高海拔區域 (>2438m)
        "waypoints_in_segment": 8,              # 該路段的重要地點數量 (山屋, 岔路等)

        # 與基準比較的數據
        "duration_comparison_vs_official_hours": -1.5,    # 比官方預估快了 1.5 小時
    }

# --- 核心：報告生成函數 ---
def generate_hiking_report(hiking_data: dict) -> str:
    """
    根據準備好的行程數據，呼叫 LLM 生成報告。
    """
    print("INFO: 正在設計數據驅動的 Prompt 並呼叫 LLM API...")

    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=GOOGLE_API_KEY, temperature=0.6)

    prompt_template_str = """
**角色扮演:**
你是一位名叫「AllPass AI」的數據導向高山嚮導。你的專長是結合使用者的基本資料和詳細的 GPX 軌跡特徵，提供一份具備深度洞察、專業且充滿鼓勵的分析報告。使用繁體中文。

**你的任務:**
根據我提供的「行程特徵數據」，生成一份結構清晰、包含四個部分的專業報告。

**行程特徵數據:**
- 使用者名稱: {user_name}
- 步道名稱: {trail_name}
- 健行日期: {hike_date}
- 天氣狀況: {weather_conditions}
- 總距離 (公里): {total_distance_km}
- 總時長 (小時): {total_duration_hours}
- 移動時間 (小時): {moving_duration_hours}
- 休息時間 (小時): {resting_duration_hours}
- 平均移動速度 (km/h): {avg_speed_kmh}
- 最高海拔 (公尺): {max_elevation_m}
- 官方預估時長 (小時): {official_duration_hours}
- 與官方時長比較 (小時): {duration_comparison_vs_official_hours}
- 坡度變異數: {slope_variance}
- 地形粗糙度: {terrain_roughness}
- 最大坡度: {max_slope}

**報告生成指南 (嚴格遵守):**

**1. 行程總覽 (Trip Overview):**
   - 以親切的語氣稱呼 `{user_name}`，祝賀他完成 `{trail_name}` 這條經典路線。
   - 簡要總結行程日期、天氣、總距離和總耗時。

**2. 體能與配速分析 (Performance & Pacing Analysis):**
   - **關鍵分析點:** 強調在 `{max_elevation_m}` 公尺的高海拔環境下，要克服空氣稀薄、背負重裝備以及應對複雜地形等多重挑戰。在這種條件下，能維持 `{avg_speed_kmh}` km/h 的移動速度是非常不容易的成就。
   - **表現標竿:** 稱讚他比官方預估時間快了 `{duration_comparison_vs_official_hours}` 小時，這直接證明了他的卓越體能與有效的配速策略。
   - 評論休息與移動時間的比例 (`{resting_duration_hours}` vs `{moving_duration_hours}` 小時)，判斷其休息策略是否得宜。

**3. 路線技術分析 (Technical & Route Analysis):**
   - **解讀數據:** 根據 `{slope_variance}` (坡度變異數) 和 `{terrain_roughness}` (地形粗糙度) 的數值，分析這條路線的技術挑戰性。以容易讀懂的方式表達，可以參考網站：健行筆記或hiking note。
   - 提及 `{max_slope}` 度的最大坡度，指出這是對心肺能力的一大考驗。
   - 稱讚使用者成功應對了這些複雜地形，展現了良好的登山技巧。

**4. 個人化未來建議 (Personalized Recommendations):**
   - 根據本次的表現，推薦一條難度相仿或稍高一階的路線並說明原因，作為下一個目標。
   - 提出一項具體的訓練建議，以應對未來的挑戰。例如：「為了挑戰更長天數的縱走路線，可以將部分訓練轉換為階梯或坡地間歇跑，以增強上坡的專項肌力。」
   - 最後，用一句激勵人心的話語作結。
"""

    prompt = ChatPromptTemplate.from_template(template=prompt_template_str)
    output_parser = StrOutputParser()
    chain = prompt | llm | output_parser

    report = chain.invoke(hiking_data)
    return report

# --- 主執行區塊 ---
if __name__ == "__main__":
    print("--- 開始執行個人化行程報告生成腳本 ---")
    mock_gpx_id = 123

    # 1. 獲取並處理數據
    data_package = fetch_hiking_data(mock_gpx_id)

    # 2. 生成報告
    if data_package:
        try:
            final_report = generate_hiking_report(data_package)

            # 3. 呈現結果
            print("\n✅ --- 您的個人化行程報告 --- ✅")
            print(final_report)
            print("--------------------------------")
        except Exception as e:
            print(f"❌ 生成報告時發生錯誤: {e}")
    else:
        print(f"❌ 無法為 gpx_upload_id: {mock_gpx_id} 獲取數據。")
