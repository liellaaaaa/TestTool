import os
import sys

# 导入generate_pytest_tests函数
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from pytest_generator import generate_pytest_tests
import configparser

# 测试数据
test_points = [
    {
        'id': 'test001',
        'type': 'button',
        'selector': 'button.el-button.el-button--primary.el-button--large.login-btn',
        'priority': 'high'
    }
]

# 测试配置
config = configparser.ConfigParser()
config['DEFAULT'] = {
    'browser': 'chromium',
    'headless': 'true',
    'page_load_timeout': '30',
    'log_level': 'INFO',
    'screenshot_dir': 'screenshots'
}

# 测试URL
url = 'https://ai.gdhonghao.com/dashboard'

# 测试账号
username = 'test001'
password = '123456'

# 调用generate_pytest_tests函数
try:
    test_file_path = generate_pytest_tests(url, test_points, config, username, password)
    print(f"测试成功！生成的测试文件路径: {test_file_path}")
    
    # 读取生成的测试文件，验证登录逻辑是否正确
    with open(test_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查登录逻辑是否正确生成
    if 'username_input.fill("test001")' in content:
        print("用户名输入生成正确！")
    else:
        print("用户名输入生成失败！")
        
    if 'password_input.fill("123456")' in content:
        print("密码输入生成正确！")
    else:
        print("密码输入生成失败！")
        
    if 'page.wait_for_load_state(\'networkidle\', timeout=30 * 1000)' in content:
        print("等待网络空闲生成正确！")
    else:
        print("等待网络空闲生成失败！")
        
    # 检查变量是否正确替换
    if 'logger.info("开始测试: " + "test001" + " - " + "button")' in content:
        print("变量替换正确！")
    else:
        print("变量替换失败！")
        
except Exception as e:
    print(f"测试失败: {str(e)}")
