"""
アプリ共有ロガー。

方針（Qiita: Python のロギングを完全に理解する より）：
- ルートロガーは使わない → 名前付きロガー "knowledge_audit" を一つ定義
- propagate=False でルートロガーへの伝播を遮断
- StreamHandler（コンソール）と FileHandler（logs/app.log）の両方に出力

使い方：
    from src.logger import logger
    logger.info("done")
    logger.error("something went wrong", exc_info=True)
"""

import logging
import os
from logging import Logger, Formatter, StreamHandler, FileHandler

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"


def _build_logger() -> Logger:
    _logger = logging.getLogger("knowledge_audit")
    _logger.setLevel(LOG_LEVEL)
    _logger.propagate = False  # ルートロガーへ伝播させない

    if _logger.handlers:  # 二重登録防止（Streamlit の再実行対策）
        return _logger

    formatter = Formatter(LOG_FORMAT)

    # コンソール出力
    sh = StreamHandler()
    sh.setLevel(LOG_LEVEL)
    sh.setFormatter(formatter)
    _logger.addHandler(sh)

    # ファイル出力
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    fh = FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(LOG_LEVEL)
    fh.setFormatter(formatter)
    _logger.addHandler(fh)

    return _logger


logger: Logger = _build_logger()
