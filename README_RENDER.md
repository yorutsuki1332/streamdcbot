部署到 Render 的快速說明

- 在 Render 建立新服務 (Web Service)，選擇連接你的 Git repo
- Start Command: `python main.py`（或使用根目錄的 `Procfile`）
- Environment Variables:
  - `DISCORD_BOT_TOKEN` = 你的 Discord bot token
- Render 會自動提供 `PORT` 環境變數；程式會綁定該埠以回應健康檢查
- 建議使用 Python 3.11（或與 `pyproject.toml` 相符的版本）

本機測試：

```bash
# macOS / Linux
export DISCORD_BOT_TOKEN="your_token_here"
python main.py

# Windows PowerShell
$env:DISCORD_BOT_TOKEN="your_token_here"
python main.py
```

若需要讓 Render 自動建立服務，於 Dashboard 建立 Web Service，部署後檢查 Logs 確認 bot 成功啟動。

GitHub 自動部署（選用）:

- 建議在 GitHub repository 的 `Settings -> Secrets -> Actions` 新增兩個 secrets:
  - `RENDER_API_KEY` = 你的 Render API Key（在 Render Dashboard 的 Account Settings 產生）
  - `RENDER_SERVICE_ID` = 你在 Render 上建立的 Service ID（或在 Dashboard 的 URL 找到）
- 專案內已包含 `.github/workflows/render-deploy.yml`，每次 push 到 `main` 分支會用上述 secrets 透過 Render API 觸發一次部署。

使用 `render.yaml`:

- 專案包含 `render.yaml`，可在 Render 建立服務時使用此檔案作為基礎設定（IaC）。建立服務後，請到 Dashboard 手動在 Environment Variables 加上 `DISCORD_BOT_TOKEN`。

注意: 切勿把 `DISCORD_BOT_TOKEN` 放進 repo；必須在 Render Dashboard 的 Environment Variables 或 GitHub Secrets 中設定。
