import logging
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_encoding.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 测试中文字符
logger.info("测试中文字符：这是一条测试日志")
logger.warning("测试中文字符：这是一条警告日志")
logger.error("测试中文字符：这是一条错误日志")

print("测试完成，请查看test_encoding.log文件")
