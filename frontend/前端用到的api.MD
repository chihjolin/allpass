# API 路由整理


|**API 路由**|**所在頁面/子元件**|**功能**|**預想用的到DB欄位**|**已實裝**|
|-|-|-|-|-|
|`/api/trails`| `Home.jsx`/ `TrailCard.jsx`| 首頁載入時call，所有步道基本資料，並顯示步道卡片。 |`trail_id` `trail_name_ch` `location_name` `permit_required` `difficulty?`|O|
|`/api/trail/:id`|`TrailDetail.jsx`/ `StatsGrid.jsx` `MapWithTrail.jsx`|使用者在首頁點選步道卡片後，會進一步請求步道ID，獲取指定步道的詳細資料，步道資料for路線資料；linestring那些for地圖。|特定步道的:  `trail_id` `trail_name_ch` `location_name` `permit_required` `difficulty?` `length_km` `elevation_start_m` `elevation_end_m` `route_geometry` `geolocation` `sequence_order` `poi_name` `poi_type` `description`|O|
|`/api/weather`|`TrailDetail.jsx`/ `WeatherCard.jsx`|根據選擇的步道傳location_name，獲取天氣資料，並顯示天氣卡片。|串外部api|O|
|`/api/predict`|`PlanPage.jsx`/ `PredictBtn.jsx`|傳抵達通訊點時間，模型回傳並顯示預測結果。|串模型|X|
|`/api/upload-gpx`|`PlanPage.jsx`/ `GpxUploadBtn.jsx`|上傳 GPX 檔案，並顯示LLM的單一GPX分析報告。|串LLM|X|
|`/api/login`|`LogIn.jsx`| 傳登入時的帳號密碼|不用回傳東東 or 後端接到帳密去查DB回傳前端Bool(true登入成功、false登入失敗)|X|
|`/api/llm-report`|`Profile.jsx`| 傳userID?，獲得LLM的個人化客製報告|串LLM|X|
|`/api/recommended-trails`|`Profile.jsx`|推薦系統用，傳userID，獲取推薦步道資料，並顯示 "你可能會喜歡" 區塊|串模型|X|
|`/api/user-record/:id`|`Profile.jsx`| 設想功能而已，個人紀錄頁面用，userID隨機配對進特徵表，獲取爬山紀錄等等個人統計資訊並顯示，一個成就的概念|ex:`總爬山次數` `近期爬山紀錄顯示` `個人總爬升高度` ...|X|
---

1. **登入功能簡化設想?**：
   - 登入的時候前端localstorage記下帳號(user_id)，在profile頁面發請求的時候帶user_id，後端就可以拿user_id撈相關資料回傳前端。登出時清除



/api/prediction.
trail_id
poi_id
order
time