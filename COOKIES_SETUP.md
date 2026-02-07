# YouTube Cookies 設定說明

YouTube 現在要求認證才能下載音頻。bot 需要有效的 cookies 文件才能播放音樂。

## 快速設定（推薦）

### 方法 1：使用 Chrome 擴充（最簡單）

1. **安裝擴充**：
   - 打開 Chrome 並訪問 [Chrome Web Store](https://chrome.google.com/webstore)
   - 搜尋 "cookies.txt" 或 "Get cookies.txt"
   - 安裝任何評分高的擴充（例如 "Get cookies.txt"）

2. **導出 Cookies**：
   - 訪問 https://www.youtube.com
   - 確保已登入你的 Google 帳戶
   - 點擊擴充圖示 → "Export cookies"
   - 檔案會自動下載為 `cookies.txt`

3. **放置檔案**：
   - 將 `cookies.txt` 放在此專案根目錄（與 `main.py` 同級）
   - 路徑應為：`v:\streamdcbot\cookies.txt`

4. **測試**：
   - 重啟 bot
   - 試用 `!play <youtube_url>`

---

### 方法 2：使用 yt-dlp 內置工具

如果你有 Firefox 或 Chrome，可以用 yt-dlp 直接從瀏覽器提取：

```powershell
# 進入專案目錄
cd v:\streamdcbot

# 使用 yt-dlp 從 Firefox 提取
V:/.venv/Scripts/yt-dlp.exe --cookies-from-browser firefox --write-cookies cookies.txt https://www.youtube.com

# 或從 Chrome 提取
V:/.venv/Scripts/yt-dlp.exe --cookies-from-browser chrome --write-cookies cookies.txt https://www.youtube.com
```

---

## 驗證 Cookies

確認 `cookies.txt` 有效：

```powershell
# 測試連接
V:/.venv/Scripts/yt-dlp.exe --cookies cookies.txt "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -e --no-warnings
```

如果成功，會顯示影片標題。

---

## Render 部署

**重要**：不要將 `cookies.txt` 提交到 GitHub（它包含個人認證信息）！

1. 添加到 `.gitignore`：
   ```
   cookies.txt
   ```

2. 在 Render Dashboard 上：
   - 無法直接上傳 cookies 文件
   - 可以在 Render 環境變量中設定 YouTube cookies 內容（進階用法）
   - 或在 Render 上設定 Firefox/Chrome 環境變量

---

## 常見問題

**Q: Cookies 多久需要更新？**
A: 通常每幾周需要重新導出一次（當 bot 無法連接時）

**Q: 多個 YouTube 帳戶？**
A: 只需要登入一個有效帳戶即可。推薦使用無限制內容的帳戶。

**Q: 仍然收到 "Sign in" 錯誤？**
A: 嘗試：
- 更新 yt-dlp：`pip install --upgrade yt-dlp`
- 重新導出 cookies（可能已過期）
- 確認 cookies.txt 在正確位置

---

## 隱私提示

Cookies 文件包含你的 YouTube 會話信息。請：
- 不要分享或提交到 GitHub
- 定期更新（定期登入 YouTube）
- 定期刪除舊的 cookies.txt 文件
