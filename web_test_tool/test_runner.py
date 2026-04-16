import logging
import os
from playwright.sync_api import sync_playwright

class TestRunner:
    def __init__(self, url, test_points, config=None):
        self.url = url
        self.test_points = test_points
        self.logger = logging.getLogger(__name__)
        self.config = config
        # 从配置中读取设置
        self.screenshot_dir = config.get('DEFAULT', 'screenshot_dir', fallback='screenshots') if config else 'screenshots'
        self.report_dir = config.get('DEFAULT', 'report_dir', fallback='reports') if config else 'reports'
        self.browser_type = config.get('DEFAULT', 'browser', fallback='chromium') if config else 'chromium'
        self.headless = config.getboolean('DEFAULT', 'headless', fallback=False) if config else False
        self.page_load_timeout = int(config.get('DEFAULT', 'page_load_timeout', fallback='30')) if config else 30
        self.element_timeout = int(config.get('DEFAULT', 'element_timeout', fallback='10')) if config else 10
        # 创建目录
        os.makedirs(self.screenshot_dir, exist_ok=True)
        os.makedirs(self.report_dir, exist_ok=True)
        # 初始化测试结果
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'total': 0
        }
        self.failed_tests = []
    
    def select_tests(self):
        """让用户选择要运行的测试"""
        print("\n请选择要运行的测试:")
        print("1. 输入 'all' 运行所有测试")
        print("2. 输入测试ID，如 '1,3,5' 运行指定测试")
        print("3. 输入范围，如 '1-5' 运行test001到test005")
        print("4. 输入元素类型，如 'button' 运行所有按钮测试")
        print("5. 输入优先级，如 'high' 运行所有高优先级测试")
        
        while True:
            user_input = input("请输入选择: ").strip()
            
            # 运行所有测试
            if user_input == 'all':
                return [tp['id'] for tp in self.test_points]
            
            # 按测试ID选择
            elif ',' in user_input:
                try:
                    selected_indices = [int(i.strip()) for i in user_input.split(',')]
                    selected_ids = [f'test{i:03d}' for i in selected_indices]
                    valid_ids = [tid for tid in selected_ids if any(tp['id'] == tid for tp in self.test_points)]
                    if valid_ids:
                        return valid_ids
                    else:
                        print("无效的测试ID，请重新输入")
                except ValueError:
                    print("输入格式错误，请重新输入")
            
            # 按范围选择
            elif '-' in user_input:
                try:
                    start, end = user_input.split('-')
                    start_idx = int(start.strip())
                    end_idx = int(end.strip())
                    if start_idx <= end_idx:
                        selected_ids = [f'test{i:03d}' for i in range(start_idx, end_idx + 1)]
                        valid_ids = [tid for tid in selected_ids if any(tp['id'] == tid for tp in self.test_points)]
                        if valid_ids:
                            return valid_ids
                        else:
                            print("无效的测试范围，请重新输入")
                    else:
                        print("范围开始值必须小于等于结束值，请重新输入")
                except ValueError:
                    print("输入格式错误，请重新输入")
            
            # 按元素类型选择
            elif user_input in ['button', 'input', 'link', 'checkbox', 'radio', 'select', 'textarea', 'form']:
                valid_ids = [tp['id'] for tp in self.test_points if tp['type'] == user_input]
                if valid_ids:
                    return valid_ids
                else:
                    print(f"没有找到{user_input}类型的测试，请重新输入")
            
            # 按优先级选择
            elif user_input in ['high', 'medium', 'low']:
                valid_ids = [tp['id'] for tp in self.test_points if tp['priority'] == user_input]
                if valid_ids:
                    return valid_ids
                else:
                    print(f"没有找到{user_input}优先级的测试，请重新输入")
            
            else:
                print("输入格式错误，请重新输入")
    
    def run_tests(self, selected_test_ids):
        """运行选定的测试"""
        print(f"\n开始运行测试: {', '.join(selected_test_ids)}")
        
        # 初始化测试结果统计
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'total': len(selected_test_ids)
        }
        self.failed_tests = []
        
        for test_id in selected_test_ids:
            test_point = next((tp for tp in self.test_points if tp['id'] == test_id), None)
            if test_point:
                result = self._run_single_test(test_point)
                if result:
                    self.test_results['passed'] += 1
                else:
                    self.test_results['failed'] += 1
                    self.failed_tests.append(test_id)
        
        # 展示测试结果
        self._show_test_summary()
    
    def _run_single_test(self, test_point):
        """运行单个测试"""
        test_id = test_point['id']
        element_type = test_point['type']
        selector = test_point['selector']
        self.logger.info(f"开始测试: {test_id} - {element_type} - 选择器: {selector}")
        
        try:
            with sync_playwright() as p:
                # 根据配置选择浏览器
                browser = getattr(p, self.browser_type).launch(headless=self.headless)
                page = browser.new_page()
                # 设置超时时间
                page.set_default_timeout(self.page_load_timeout * 1000)
                page.goto(self.url)
                
                # 等待页面加载完成
                page.wait_for_load_state('networkidle', timeout=self.page_load_timeout * 1000)
                
                if element_type == 'button':
                    # 测试按钮点击
                    button = page.query_selector(selector)
                    if button:
                        # 获取按钮文本
                        button_text = button.text_content().strip() if button.text_content() else '无文本'
                        self.logger.info(f"找到按钮: {button_text}")
                        button.click()
                        # 等待可能的页面变化
                        page.wait_for_timeout(2000)
                        self.logger.info(f"测试通过: {test_id} - 按钮点击成功")
                    else:
                        raise Exception(f"元素未找到 - 选择器: {selector}")
                
                elif element_type == 'input':
                    # 测试输入框
                    input_elem = page.query_selector(selector)
                    if input_elem:
                        # 获取输入框类型和占位符
                        input_type = input_elem.get_attribute('type') or 'text'
                        placeholder = input_elem.get_attribute('placeholder') or '无占位符'
                        self.logger.info(f"找到输入框: 类型={input_type}, 占位符={placeholder}")
                        input_elem.fill('测试输入')
                        # 等待输入完成
                        page.wait_for_timeout(1000)
                        # 验证输入是否成功
                        input_value = input_elem.input_value()
                        if input_value == '测试输入':
                            self.logger.info(f"测试通过: {test_id} - 输入框填写成功")
                        else:
                            raise Exception(f"输入失败 - 期望值: '测试输入', 实际值: '{input_value}'")
                    else:
                        raise Exception(f"元素未找到 - 选择器: {selector}")
                
                elif element_type == 'link':
                    # 测试链接点击
                    link = page.query_selector(selector)
                    if link:
                        # 获取链接文本和href
                        link_text = link.text_content().strip() if link.text_content() else '无文本'
                        href = link.get_attribute('href') or '无链接'
                        self.logger.info(f"找到链接: {link_text}, 目标: {href}")
                        # 记录点击前的URL
                        before_url = page.url
                        link.click()
                        # 等待页面导航
                        page.wait_for_load_state('networkidle', timeout=30000)
                        after_url = page.url
                        if after_url != before_url:
                            self.logger.info(f"测试通过: {test_id} - 链接点击成功，导航到: {after_url}")
                        else:
                            self.logger.info(f"测试通过: {test_id} - 链接点击成功，但未导航")
                    else:
                        raise Exception(f"元素未找到 - 选择器: {selector}")
                
                elif element_type in ['checkbox', 'radio']:
                    # 测试复选框和单选按钮
                    input_elem = page.query_selector(selector)
                    if input_elem:
                        # 获取元素信息
                        name = input_elem.get_attribute('name') or ''
                        value = input_elem.get_attribute('value') or ''
                        self.logger.info(f"找到{element_type}: 名称={name}, 值={value}")
                        # 点击元素
                        input_elem.click()
                        page.wait_for_timeout(1000)
                        # 验证是否选中
                        is_checked = input_elem.is_checked()
                        if is_checked:
                            self.logger.info(f"测试通过: {test_id} - {element_type}选中成功")
                        else:
                            raise Exception(f"{element_type}未选中")
                    else:
                        raise Exception(f"元素未找到 - 选择器: {selector}")
                
                elif element_type == 'select':
                    # 测试下拉菜单
                    select_elem = page.query_selector(selector)
                    if select_elem:
                        # 获取元素信息
                        name = select_elem.get_attribute('name') or ''
                        self.logger.info(f"找到下拉菜单: 名称={name}")
                        # 选择第一个选项
                        select_elem.select_option(index=0)
                        page.wait_for_timeout(1000)
                        # 验证选择是否成功
                        selected_value = select_elem.input_value()
                        if selected_value:
                            self.logger.info(f"测试通过: {test_id} - 下拉菜单选择成功，选中值: {selected_value}")
                        else:
                            raise Exception("下拉菜单选择失败")
                    else:
                        raise Exception(f"元素未找到 - 选择器: {selector}")
                
                elif element_type == 'textarea':
                    # 测试文本域
                    textarea_elem = page.query_selector(selector)
                    if textarea_elem:
                        # 获取元素信息
                        name = textarea_elem.get_attribute('name') or ''
                        placeholder = textarea_elem.get_attribute('placeholder') or '无占位符'
                        self.logger.info(f"找到文本域: 名称={name}, 占位符={placeholder}")
                        # 填写文本
                        test_text = '测试文本内容'
                        textarea_elem.fill(test_text)
                        page.wait_for_timeout(1000)
                        # 验证填写是否成功
                        textarea_value = textarea_elem.input_value()
                        if textarea_value == test_text:
                            self.logger.info(f"测试通过: {test_id} - 文本域填写成功")
                        else:
                            raise Exception(f"文本域填写失败 - 期望值: '{test_text}', 实际值: '{textarea_value}'")
                    else:
                        raise Exception(f"元素未找到 - 选择器: {selector}")
                
                elif element_type == 'form':
                    # 测试表单
                    form_elem = page.query_selector(selector)
                    if form_elem:
                        # 获取元素信息
                        action = form_elem.get_attribute('action') or ''
                        method = form_elem.get_attribute('method') or 'get'
                        self.logger.info(f"找到表单: 动作={action}, 方法={method}")
                        # 检查表单是否存在提交按钮
                        submit_button = form_elem.query_selector('button[type="submit"], input[type="submit"]')
                        if submit_button:
                            self.logger.info("表单包含提交按钮")
                        else:
                            self.logger.info("表单不包含提交按钮")
                        self.logger.info(f"测试通过: {test_id} - 表单分析成功")
                    else:
                        raise Exception(f"元素未找到 - 选择器: {selector}")
                
                browser.close()
                return True  # 测试通过
                
        except Exception as e:
            # 测试失败，截图并记录详细错误信息
            error_detail = f"测试失败: {test_id} - {element_type} - 错误: {str(e)}"
            self.logger.error(error_detail)
            # 尝试截图
            try:
                if 'page' in locals():
                    screenshot_path = os.path.join(self.screenshot_dir, f"{test_id}_failure.png")
                    page.screenshot(path=screenshot_path, full_page=True)
                    self.logger.info(f"已保存失败截图: {screenshot_path}")
                    error_detail += f" - 截图已保存: {screenshot_path}"
            except Exception as screenshot_error:
                self.logger.warning(f"截图失败: {str(screenshot_error)}")
            # 记录详细错误到日志
            self.logger.error(f"详细错误信息: 元素类型={element_type}, 选择器={selector}, 错误={str(e)}")
            return False  # 测试失败
    
    def _show_test_summary(self):
        """展示测试结果汇总"""
        print("\n" + "-" * 80)
        print("测试结果汇总:")
        print(f"总测试数: {self.test_results['total']}")
        print(f"通过: {self.test_results['passed']}")
        print(f"失败: {self.test_results['failed']}")
        
        if self.failed_tests:
            print(f"\n失败的测试: {', '.join(self.failed_tests)}")
            print("\n失败详情请查看test.log文件")
        
        print("-" * 80)
        
        # 生成测试报告
        self.generate_test_report()
    
    def generate_test_report(self):
        """生成HTML格式的测试报告"""
        import datetime
        import os
        
        # 创建报告目录
        report_dir = self.report_dir
        os.makedirs(report_dir, exist_ok=True)
        
        # 生成报告文件名
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = os.path.join(report_dir, f'test_report_{timestamp}.html')
        
        # 构建报告内容
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>测试报告</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        h1, h2, h3 {{
            color: #333;
        }}
        .summary {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 30px;
        }}
        .summary-item {{
            display: inline-block;
            margin-right: 30px;
            font-size: 18px;
        }}
        .summary-item .value {{
            font-weight: bold;
            font-size: 24px;
        }}
        .passed {{ color: green; }}
        .failed {{ color: red; }}
        .test-results {{ margin-top: 30px; }}
        .test-item {{
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 10px;
        }}
        .test-item.passed {{ border-left: 5px solid green; }}
        .test-item.failed {{ border-left: 5px solid red; }}
        .screenshot {{ margin-top: 10px; }}
        .screenshot img {{ max-width: 100%; border: 1px solid #ddd; }}
        .timestamp {{ color: #666; font-size: 14px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>网页测试工具 - 测试报告</h1>
        <div class="timestamp">生成时间: {timestamp}</div>
        <div class="summary">
            <h2>测试摘要</h2>
            <div class="summary-item">
                总测试数: <span class="value">{self.test_results['total']}</span>
            </div>
            <div class="summary-item">
                通过: <span class="value passed">{self.test_results['passed']}</span>
            </div>
            <div class="summary-item">
                失败: <span class="value failed">{self.test_results['failed']}</span>
            </div>
            <div class="summary-item">
                成功率: <span class="value">{self.test_results['passed'] / self.test_results['total'] * 100:.2f}%</span>
            </div>
        </div>
        
        <div class="test-results">
            <h2>测试详情</h2>
"""
        
        # 添加测试详情
        for test_id in [tp['id'] for tp in self.test_points]:
            test_point = next((tp for tp in self.test_points if tp['id'] == test_id), None)
            if test_point:
                status = 'passed' if test_id not in self.failed_tests else 'failed'
                status_class = 'passed' if status == 'passed' else 'failed'
                status_text = '通过' if status == 'passed' else '失败'
                
                # 构建测试详情
                test_detail = f"""
            <div class="test-item {status_class}">
                <h3>{test_id} - {test_point['type']} - {test_point['priority']}优先级</h3>
                <p><strong>状态:</strong> <span class="{status_class}">{status_text}</span></p>
                <p><strong>选择器:</strong> {test_point['selector']}</p>
"""
                
                # 添加元素特定信息
                if test_point['type'] == 'button':
                    test_detail += f"<p><strong>文本:</strong> {test_point['text']}</p>"
                elif test_point['type'] == 'input':
                    test_detail += f"<p><strong>类型:</strong> {test_point['input_type']}</p>"
                    test_detail += f"<p><strong>占位符:</strong> {test_point['placeholder']}</p>"
                elif test_point['type'] == 'link':
                    test_detail += f"<p><strong>文本:</strong> {test_point['text']}</p>"
                    test_detail += f"<p><strong>链接:</strong> {test_point['href']}</p>"
                elif test_point['type'] in ['checkbox', 'radio']:
                    test_detail += f"<p><strong>名称:</strong> {test_point['name']}</p>"
                    test_detail += f"<p><strong>值:</strong> {test_point['value']}</p>"
                elif test_point['type'] == 'select':
                    test_detail += f"<p><strong>名称:</strong> {test_point['name']}</p>"
                    test_detail += f"<p><strong>选项数量:</strong> {test_point['option_count']}</p>"
                elif test_point['type'] == 'textarea':
                    test_detail += f"<p><strong>名称:</strong> {test_point['name']}</p>"
                    test_detail += f"<p><strong>占位符:</strong> {test_point['placeholder']}</p>"
                elif test_point['type'] == 'form':
                    test_detail += f"<p><strong>动作:</strong> {test_point['action']}</p>"
                    test_detail += f"<p><strong>方法:</strong> {test_point['method']}</p>"
                
                # 添加失败截图
                if status == 'failed':
                    screenshot_path = os.path.join(self.screenshot_dir, f"{test_id}_failure.png")
                    if os.path.exists(screenshot_path):
                        # 使用相对路径
                        relative_path = os.path.relpath(screenshot_path, report_dir)
                        test_detail += f"""
                <div class="screenshot">
                    <p><strong>失败截图:</strong></p>
                    <img src="{relative_path}" alt="{test_id} 失败截图">
                </div>
"""
                
                test_detail += "</div>"
                html_content += test_detail
        
        # 结束HTML
        html_content += f"""
        </div>
    </div>
</body>
</html>
"""
        
        # 写入报告文件
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"测试报告已生成: {report_file}")
        print(f"\n测试报告已生成: {report_file}")
    

