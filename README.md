# Perp DEX 竞对分析自动化看板

自动抓取 Perp DEX 竞对数据，生成图表看板 + Google Sheets 自动更新。**全免费。**

## 监控协议

| 协议 | 链 | DefiLlama Slug |
|------|-----|----------------|
| Hyperliquid | Hyperliquid L1 | hyperliquid-perp |
| EdgeX | edgeX | edgeX |
| GRVT | GRVT | grvt-perps |
| Variational | Arbitrum | variational-omni |
| Lighter | zkLighter | lighterv2 |
| Aster | Off Chain | apollox |
| Paradex | Paradex | paradex |
| Extended | Ethereum/Starknet | extended |
| Pacifica | Solana | pacifica |

## 架构

```
DefiLlama API (免费) → Python ETL → data/perp_data.json → GitHub Pages 图表看板
                                   → Google Sheets (可选)
```

## 快速开始

```bash
pip install -r requirements.txt

# 增量更新（获取最新快照，1 次 API 调用）
cd src && python main.py

# 首次拉取全部历史（9 次 API 调用，~1 分钟）
cd src && python main.py --history
```

然后用浏览器打开 `index.html` 查看图表看板。

## 输出

| 输出 | 说明 |
|------|------|
| `data/perp_data.json` | 原始数据（供 GitHub Pages 读取） |
| `index.html` | Chart.js 图表看板 |
| Google Sheets (可选) | Latest sheet + History sheet |

## 衍生指标

| 指标 | 公式 |
|------|------|
| Market Share % | 协议 Volume / 总 Volume × 100 |
| Growth Rate % | (今日 - 昨日) / 昨日 × 100 |

## 自动化

GitHub Actions 每周一 UTC 08:00 自动运行。支持手动触发：
- `snapshot`: 只获取最新数据（默认）
- `history`: 拉取全部历史

## 成本

| 项目 | 成本 |
|------|------|
| DefiLlama API | 免费 |
| Google Sheets | 免费 |
| GitHub Actions | 免费 |
| GitHub Pages | 免费 |

## Google Sheets 配置（可选）

详见 [Google Sheets 配置指南](docs/google_sheets_setup.md)

## 部署 GitHub Pages

1. 推送代码到 GitHub
2. Settings → Pages → Source: Deploy from a branch → Branch: main, / (root)
3. 访问 `https://你的用户名.github.io/你的仓库名/`
