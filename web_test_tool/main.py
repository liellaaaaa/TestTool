import logging
import os
import configparser
from page_analyzer import PageAnalyzer
from test_runner import TestRunner
from pytest_generator import generate_pytest_tests

# 读取配置文件
config = configparser.ConfigParser()
config_file = 'config.ini'
if os.path.exists(config_file):
    # 使用UTF-8编码读取配置文件
    with open(config_file, 'r', encoding='utf-8') as f:
        config.read_file(f)
else:
    # 默认配置
    config['DEFAULT'] = {
        'browser': 'chromium',
        'headless': 'false',
        'page_load_timeout': '30',
        'element_timeout': '10',
        'screenshot_dir': 'screenshots',
        'report_dir': 'reports',
        'log_level': 'INFO'
    }
    config['TEST'] = {
        'default_test_selection': 'all',
        'generate_pytest': 'true'
    }

# 配置日志
log_level = getattr(logging, config.get('DEFAULT', 'log_level').upper(), logging.INFO)
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test.log'),
        logging.StreamHandler()
    ]
)

def main():
    """主函数"""
    # 输入目标URL
    url = input("请输入要测试的网页URL: ").strip()
    
    # 分析页面元素
    analyzer = PageAnalyzer(url, config)
    test_points = analyzer.analyze_page()
    
    if not test_points:
        print("未分析出可测试的元素")
        return
    
    # 打印测试点
    analyzer.print_test_points()
    
    # 生成pytest测试文件
    if config.getboolean('TEST', 'generate_pytest', fallback=True):
        generate_pytest_tests(url, test_points, config)
        print("\n已生成pytest测试文件: tests/test_page_elements.py")
    
    # 运行测试
    runner = TestRunner(url, test_points, config)
    selected_test_ids = runner.select_tests()
    runner.run_tests(selected_test_ids)

if __name__ == "__main__":
    main()