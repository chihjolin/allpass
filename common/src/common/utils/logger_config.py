import logging
import os
from pathlib import Path


def setup_logging(level: int | str | None = None) -> None:
    if level is None:
        level_name = os.getenv("LOG_LEVEL", "INFO").upper()
        level = logging._nameToLevel.get(level_name, logging.INFO)

    # 所有子 logger 會繼承
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    if root_logger.handlers:
        return  # 避免重複設定（防 uvicorn reload/防 pytest session 重跑/防 handler 疊加）

    # --------------------------
    # Console handler (CloudWatch 標準)
    # --------------------------
    console_handler = logging.StreamHandler()
    # handler 也setLevel:雙層保護/可獨立調整
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        "[%(levelname)s] %(asctime)s %(name)s - %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )

    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # --------------------------
    # File handler (本地開發環境留檔、上雲不留)
    # --------------------------
    if os.getenv("ENV", "local") == "local":
        from logging.handlers import TimedRotatingFileHandler

        LOG_DIR = Path("logs")
        LOG_DIR.mkdir(exist_ok=True)
        LOG_FILE = LOG_DIR / "app.log"
        file_handler = TimedRotatingFileHandler(
            LOG_FILE,
            when="midnight",
            backupCount=7,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
