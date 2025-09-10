import logging
import os
import sys
from dotenv import load_dotenv

load_dotenv()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

def get_logger(name: str = "insty") -> logging.Logger:
    """
    프로젝트 전역에서 공용으로 쓸 logger 생성 함수.
    이미 동일한 logger가 생성되어 있으면 그대로 반환.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    # 기본 로그 레벨
    level = getattr(logging, LOG_LEVEL, logging.INFO)
    logger.setLevel(level)

    # 출력 포맷
    formatter = logging.Formatter(
        fmt="[%(asctime)s] %(levelname)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # stdout 핸들러
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
