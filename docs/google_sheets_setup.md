# Google Sheets 自动化配置指南

## 第一步：创建 Google Cloud 项目（免费）

1. 打开 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建新项目（如 "Perp DEX Dashboard"）
3. 在左侧菜单选 **APIs & Services → Library**
4. 搜索并启用 **Google Sheets API**
5. 搜索并启用 **Google Drive API**

## 第二步：创建服务账号

1. **APIs & Services → Credentials → Create Credentials → Service Account**
2. 填写名称（如 `perp-data-writer`）
3. 创建后，点击该服务账号 → **Keys → Add Key → Create New Key → JSON**
4. 下载 JSON 密钥文件，记住服务账号邮箱（格式：`xxx@xxx.iam.gserviceaccount.com`）

## 第三步：创建 Google Sheet

1. 新建一个 Google Sheet
2. 点击右上角 **Share**，将服务账号邮箱添加为 **Editor**
3. 从 URL 复制 Spreadsheet ID：
   `https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit`

## 第四步：配置环境变量

```bash
# 将 JSON 密钥文件转为 base64
cat your-credentials.json | base64 | tr -d '\n'
```

本地开发 `.env`：
```
GOOGLE_SHEETS_ID=你的SpreadsheetID
GOOGLE_CREDENTIALS_JSON=base64编码后的JSON
```

GitHub Actions Secrets：
- `GOOGLE_SHEETS_ID` → Spreadsheet ID
- `GOOGLE_CREDENTIALS_JSON` → base64 编码后的 JSON

## 输出说明

脚本会自动创建两个 Sheet：
- **Latest**: 最新一天的数据（每次覆盖）
- **History**: 全部历史数据（用于建图表）
