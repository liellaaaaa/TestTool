import os

def generate_pytest_tests(url, test_points, config=None):
    """生成pytest测试文件"""
    # 创建tests目录
    os.makedirs('tests', exist_ok=True)
    
    # 从配置中读取设置
    browser_type = config.get('DEFAULT', 'browser', fallback='chromium') if config else 'chromium'
    headless = config.getboolean('DEFAULT', 'headless', fallback=True) if config else True
    page_load_timeout = int(config.get('DEFAULT', 'page_load_timeout', fallback='30')) if config else 30
    log_level = config.get('DEFAULT', 'log_level', fallback='INFO') if config else 'INFO'
    screenshot_dir = config.get('DEFAULT', 'screenshot_dir', fallback='screenshots') if config else 'screenshots'
    
    # 构建测试文件内容
    test_file_content = f"""
import pytest
from playwright.sync_api import sync_playwright
import logging
import os

# 配置日志
logging.basicConfig(
    level=logging.{log_level.upper()},
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class TestPageElements:
    @pytest.fixture(scope="class")
    def page(self):
        with sync_playwright() as p:
            browser = p.{browser_type}.launch(headless={headless})
            page = browser.new_page()
            page.set_default_timeout({page_load_timeout} * 1000)
            page.goto("{url}")
            page.wait_for_load_state('networkidle', timeout={page_load_timeout} * 1000)
            yield page
            browser.close()

""".format(
    url=url,
    browser_type=browser_type,
    headless=headless,
    page_load_timeout=page_load_timeout,
    log_level=log_level
).strip()
    
    # 为每个测试点生成测试方法
    for i, test_point in enumerate(test_points, 1):
        test_id = test_point['id']
        element_type = test_point['type']
        selector = test_point['selector']
        priority = test_point['priority']
        
        # 生成测试方法
        test_method = f"""
    @pytest.mark.{priority}
    def test_{test_id}(self, page):
        '''测试{element_type}元素: {test_id}'''
        try:
            logger.info("开始测试: " + test_id + " - " + element_type)
            
            if "{element_type}" == "button":
                # 测试按钮点击
                button = page.query_selector("{selector}")
                assert button is not None, "元素未找到"
                button.click()
                page.wait_for_timeout(1000)
                logger.info("测试通过: " + test_id + " - 按钮点击成功")
            
            elif "{element_type}" == "input":
                # 测试输入框
                input_elem = page.query_selector("{selector}")
                assert input_elem is not None, "元素未找到"
                input_elem.fill('测试输入')
                page.wait_for_timeout(1000)
                # 验证输入是否成功
                input_value = input_elem.input_value()
                assert input_value == '测试输入', "输入失败 - 期望值: '测试输入', 实际值: '" + input_value + "'"
                logger.info("测试通过: " + test_id + " - 输入框填写成功")
            
            elif "{element_type}" == "link":
                # 测试链接点击
                link = page.query_selector("{selector}")
                assert link is not None, "元素未找到"
                # 记录点击前的URL
                before_url = page.url
                link.click()
                # 等待页面导航
                page.wait_for_load_state('networkidle', timeout={page_load_timeout} * 1000)
                after_url = page.url
                logger.info("测试通过: " + test_id + " - 链接点击成功")
            
            elif "{element_type}" in ["checkbox", "radio"]:
                # 测试复选框和单选按钮
                input_elem = page.query_selector("{selector}")
                assert input_elem is not None, "元素未找到"
                input_elem.click()
                page.wait_for_timeout(1000)
                # 验证是否选中
                is_checked = input_elem.is_checked()
                assert is_checked, "{element_type}未选中"
                logger.info("测试通过: " + test_id + " - " + element_type + "选中成功")
            
            elif "{element_type}" == "select":
                # 测试下拉菜单
                select_elem = page.query_selector("{selector}")
                assert select_elem is not None, "元素未找到"
                # 选择第一个选项
                select_elem.select_option(index=0)
                page.wait_for_timeout(1000)
                # 验证选择是否成功
                selected_value = select_elem.input_value()
                assert selected_value, "下拉菜单选择失败"
                logger.info("测试通过: " + test_id + " - 下拉菜单选择成功，选中值: " + selected_value)
            
            elif "{element_type}" == "textarea":
                # 测试文本域
                textarea_elem = page.query_selector("{selector}")
                assert textarea_elem is not None, "元素未找到"
                # 填写文本
                test_text = '测试文本内容'
                textarea_elem.fill(test_text)
                page.wait_for_timeout(1000)
                # 验证填写是否成功
                textarea_value = textarea_elem.input_value()
                assert textarea_value == test_text, "文本域填写失败 - 期望值: '" + test_text + "', 实际值: '" + textarea_value + "'"
                logger.info("测试通过: " + test_id + " - 文本域填写成功")
            
            elif "{element_type}" == "form":
                # 测试表单
                form_elem = page.query_selector("{selector}")
                assert form_elem is not None, "元素未找到"
                # 检查表单是否存在提交按钮
                submit_button = form_elem.query_selector('button[type="submit"], input[type="submit"]')
                if submit_button:
                    logger.info("表单包含提交按钮")
                else:
                    logger.info("表单不包含提交按钮")
                logger.info("测试通过: " + test_id + " - 表单分析成功")
                
        except Exception as e:
            logger.error("测试失败: " + test_id + " - " + str(e))
            # 尝试截图
            try:
                screenshot_dir = '{screenshot_dir}'
                os.makedirs(screenshot_dir, exist_ok=True)
                screenshot_path = os.path.join(screenshot_dir, "test_{test_id}_failure.png")
                page.screenshot(path=screenshot_path)
                logger.info("已保存失败截图: " + screenshot_path)
            except Exception as screenshot_error:
                logger.warning("截图失败: " + str(screenshot_error))
            raise
""".format(
            test_id=test_id,
            element_type=element_type,
            selector=selector,
            priority=priority,
            page_load_timeout=page_load_timeout,
            screenshot_dir=screenshot_dir
        )
        
        test_file_content += test_method
    
    # 写入测试文件
    test_file_path = os.path.join('tests', 'test_page_elements.py')
    with open(test_file_path, 'w', encoding='utf-8') as f:
        f.write(test_file_content)
    
    return test_file_path