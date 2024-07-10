OpenLLM-VTuber: ToDo

- [x] ~~實現 python --- server 的 ws 連接~~ 目前不需要全鏈路ws連結
- [x] ~~讓 client 向 server -> python 發送請求, 獲取模型~~ 讓python向client發送模型數據, 設置模型
- [x] 把 prompt analysis 邏輯放到 python, 變成由server 給client 發送表情和說話命令

LLM

- [ ] 聊天記錄 (每次交流都append, 可以用json存)
- [ ] 重新實現Rag, 用graph database?
- [ ] personality card, 加載 system prompt? 把system prompt 拆分出config.yaml
- [x] [memGPT] 讓LLM 記住關鍵信息 (比如Potato-As-A-Service)
- [x] [memGPT] Personality Prompt Profile. 保存個性(和記憶,還有一些config?)的檔案

Plugin 插件系統, 外部數據交互

- [ ] 與瀏覽器插件交互
- [ ] 與屏幕截圖交互
- [ ] 主動獲取外部數據

TTS / ASR

- [ ] 實現 chatTTS
- [ ] 實現 GPT-SoVits
- [x] 實現 超快whisper
- [ ] 實現 coqui-ai-tts
- [ ] 日文配音(?), 只在voice synthesis 部分做翻譯

Live2D

- [ ] 實現 motion
- [ ] 抽象化 live2d 組件, 不知道能不能適配多種前端...

整體

- [x] 實現中文
- [ ] configuration 設置網頁, 用webui 編輯配置文件, 優化項目配置流程
- [x] 寫接口類 (LLM/TTS/ASR)
- [x] 開啟`server.py` 時自動 serve 前端頁面
- [x] 設置 本服務器的 base_url (放live2d頁面 以及ws api 接口)
- [x] 整理項目文件/命名, 比如 `speech2text` -> asr, text2speech-> speech synthesis 之類的, 還有 faster-whisper 文件夾結構, 



問題

- [x] azureTTS 在逐句發送下過慢, 句子間 間隔過長
  - 比較耗時的tts應該都會有這個問題, 希望能async 生成語音, sentence收到就立刻tts, 然後根據順序發送

- [ ] live2d模型笑起來就開不了口了



無法解決的問題

- [ ] 在完全response tts發送下, 無法控制表情執行的順序和展現時間







### 重構計畫

- [ ] api 那邊, 把 control type 刪掉, 直接用 type 和空text就完了



### 大整合計畫

- 讓項目部署更簡潔
- 把所有用戶交互的部分都放到前端, 讓用戶手機上也能訪問, client 跟 server徹底分離
- 後端 only 模式徹底消失, 必須使用前端交互

前端

- [ ] 前端文字輸入
- [x] 前端語音識別(已實現) 或 前端stream 語音到後端做asr (好麻煩)
- [ ] 
