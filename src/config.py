"""
配置模块：加载环境变量，定义常量。
"""
import os


def load_dotenv(path=".env"):
    """轻量 .env 加载器，不覆盖已有环境变量。"""
    if not os.path.isfile(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key, value = key.strip(), value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                value = value[1:-1]
            os.environ.setdefault(key, value)


load_dotenv()

# ---- DefiLlama (免费，主数据源) ----
DEFILLAMA_BASE_URL = "https://api.llama.fi"

# 协议名 → DefiLlama module slug 映射
PROTOCOL_SLUGS = {
    "Hyperliquid": "hyperliquid-perp",
    "EdgeX": "edgeX",
    "GRVT": "grvt-perps",
    "Variational": "variational-omni",
    "Lighter": "lighterv2",
    "Aster": "apollox",
    "Paradex": "paradex",
    "Extended": "extended",
    "Pacifica": "pacifica",
}

PROTOCOLS = list(PROTOCOL_SLUGS.keys())

# ---- Google Sheets (可选) ----
GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID", "")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON", "")  # base64 encoded

# ---- 数据存储 ----
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DATA_FILE = os.path.join(DATA_DIR, "perp_data.json")

# ---- 请求控制 ----
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5
API_CALL_INTERVAL = 10  # DefiLlama 免费额度: ~10 req/min, 留足余量避免限流
