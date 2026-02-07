部署到 Render 的快速說明

**系統要求：**
- Python 3.11+
- **FFmpeg** (用於音樂播放，必需！)

- 在 Render 建立新服務 (Web Service)，選擇連接你的 Git repo
- Start Command: `python main.py`（或使用根目錄的 `Procfile`）
- Environment Variables:
  - `DISCORD_BOT_TOKEN` = 你的 Discord bot token
- Render 會自動提供 `PORT` 環境變數；程式會綁定該埠以回應健康檢查

本機測試：

**安裝 FFmpeg：**

Windows:
```powershell
winget install ffmpeg
```

macOS:
```bash
brew install ffmpeg
```

Linux (Ubuntu/Debian):
```bash
sudo apt-get install ffmpeg
```

啟動 Bot：

```bash
# macOS / Linux
export DISCORD_BOT_TOKEN="your_token_here"
python main.py

# Windows PowerShell
$env:DISCORD_BOT_TOKEN="your_token_here"
python main.py
```

**YouTube 音樂播放注意事項：**

bot 使用 yt-dlp 從 YouTube 提取音頻。如果遇到 "Sign in to confirm you're not a bot" 錯誤，這是 YouTube 的反爬蟲機制。目前的解決方案：
- 本機測試時，通常會自動處理
- Render 上部署時，可能需要設定 YouTube cookies（進階用法）

簡單測試：使用 `!play <youtube_url>` 測試小視頻，YouTube 會逐漸解除限制。

若需要讓 Render 自動建立服務，於 Dashboard 建立 Web Service，部署後檢查 Logs 確認 bot 成功啟動。

GitHub 自動部署（選用）:

- 建議在 GitHub repository 的 `Settings -> Secrets -> Actions` 新增兩個 secrets:
  - `RENDER_API_KEY` = 你的 Render API Key（在 Render Dashboard 的 Account Settings 產生）
  - `RENDER_SERVICE_ID` = 你在 Render 上建立的 Service ID（或在 Dashboard 的 URL 找到）
- 專案內已包含 `.github/workflows/render-deploy.yml`，每次 push 到 `main` 分支會用上述 secrets 透過 Render API 觸發一次部署。

使用 `render.yaml`:

- 專案包含 `render.yaml`，可在 Render 建立服務時使用此檔案作為基礎設定（IaC）。建立服務後，請到 Dashboard 手動在 Environment Variables 加上 `DISCORD_BOT_TOKEN`。

注意: 切勿把 `DISCORD_BOT_TOKEN` 放進 repo；必須在 Render Dashboard 的 Environment Variables 或 GitHub Secrets 中設定。
