import os
import re
from urllib.parse import urlparse

def optimize_selector(test_point):
    """优化选择器，避开动态ID，优先使用属性选择器或文本定位"""
    element_type = test_point['type']
    selector = test_point['selector']

    # 检查是否包含动态ID（如el-id-数字-数字）
    if re.search(r'el-id-\d+-\d+', selector):
        # 根据元素类型生成更稳定的选择器
        if element_type == 'input':
            # 对于输入框，优先使用placeholder属性
            if 'placeholder' in test_point and test_point['placeholder']:
                placeholder = test_point['placeholder']
                return f"input[placeholder='{placeholder}']"
            # 如果没有placeholder，使用type属性
            elif 'input_type' in test_point and test_point['input_type']:
                input_type = test_point['input_type']
                return f"input[type='{input_type}']"
            # 否则使用class选择器（去掉ID部分）
            else:
                # 提取class部分
                classes = re.findall(r'\.([a-zA-Z0-9_-]+)', selector)
                if classes:
                    return f"input.{'.'.join(classes)}"
                return selector

        elif element_type == 'button':
            # 对于按钮，优先使用文本内容
            if 'text' in test_point and test_point['text']:
                text = test_point['text']
                return f"button:has-text('{text}')"
            # 如果没有文本，使用class选择器（去掉ID部分）
            else:
                classes = re.findall(r'\.([a-zA-Z0-9_-]+)', selector)
                if classes:
                    return f"button.{'.'.join(classes)}"
                return selector

        elif element_type == 'link':
            # 对于链接，优先使用文本内容
            if 'text' in test_point and test_point['text']:
                text = test_point['text']
                return f"a:has-text('{text}')"
            # 如果没有文本，使用class选择器（去掉ID部分）
            else:
                classes = re.findall(r'\.([a-zA-Z0-9_-]+)', selector)
                if classes:
                    return f"a.{'.'.join(classes)}"
                return selector

        elif element_type == 'checkbox':
            # 对于复选框，使用class选择器（去掉ID部分）
            classes = re.findall(r'\.([a-zA-Z0-9_-]+)', selector)
            if classes:
                return f"input[type='checkbox'].{'.'.join(classes)}"
            return selector

        elif element_type == 'radio':
            # 对于单选按钮，使用class选择器（去掉ID部分）
            classes = re.findall(r'\.([a-zA-Z0-9_-]+)', selector)
            if classes:
                return f"input[type='radio'].{'.'.join(classes)}"
            return selector

        elif element_type == 'select':
            # 对于下拉菜单，使用class选择器（去掉ID部分）
            classes = re.findall(r'\.([a-zA-Z0-9_-]+)', selector)
            if classes:
                return f"select.{'.'.join(classes)}"
            return selector

        elif element_type == 'textarea':
            # 对于文本域，优先使用placeholder属性
            if 'placeholder' in test_point and test_point['placeholder']:
                placeholder = test_point['placeholder']
                return f"textarea[placeholder='{placeholder}']"
            # 如果没有placeholder，使用class选择器（去掉ID部分）
            else:
                classes = re.findall(r'\.([a-zA-Z0-9_-]+)', selector)
                if classes:
                    return f"textarea.{'.'.join(classes)}"
                return selector

        elif element_type == 'form':
            # 对于表单，使用class选择器（去掉ID部分）
            classes = re.findall(r'\.([a-zA-Z0-9_-]+)', selector)
            if classes:
                return f"form.{'.'.join(classes)}"
            return selector

        else:
            # 对于其他元素，使用class选择器（去掉ID部分）
            classes = re.findall(r'\.([a-zA-Z0-9_-]+)', selector)
            if classes:
                return f"{element_type}.{'.'.join(classes)}"
            return selector

    # 如果不包含动态ID，直接返回原选择器
    return selector

def generate_pytest_tests(url, test_points, config=None, username=None, password=None):
    """生成pytest测试文件 - 使用参数化测试，避免重复代码"""
    # 创建tests目录
    os.makedirs('tests', exist_ok=True)

    # 从配置中读取设置
    browser_type = config.get('DEFAULT', 'browser', fallback='chromium') if config else 'chromium'
    headless = config.getboolean('DEFAULT', 'headless', fallback=True) if config else True
    page_load_timeout = int(config.get('DEFAULT', 'page_load_timeout', fallback='30')) if config else 30
    log_level = config.get('DEFAULT', 'log_level', fallback='INFO') if config else 'INFO'
    screenshot_dir = config.get('DEFAULT', 'screenshot_dir', fallback='screenshots') if config else 'screenshots'

    # 过滤掉登录页面的测试点，只保留登录后的页面测试点（放宽规则）
    filtered_test_points = []
    for tp in test_points:
        page_url = tp.get('page_url', '')
        # 只排除纯登录页面，带redirect或已经有业务元素的页面不排除
        if not (('login' in page_url.lower() or 'signin' in page_url.lower()) and 'redirect' not in page_url.lower()):
            # 优化选择器
            tp['optimized_selector'] = optimize_selector(tp)
            filtered_test_points.append(tp)

    if not filtered_test_points:
        print("⚠️  没有找到登录后的页面测试点")
        return None

    # 构建参数化测试用例列表
    test_cases = []
    for i, tp in enumerate(filtered_test_points, 1):
        test_cases.append({
            'id': tp['id'],
            'type': tp['type'],
            'page_url': tp.get('page_url', url),
            'selector': tp['optimized_selector'],
            'priority': tp['priority'],
            'meta': {k: v for k, v in tp.items() if k not in ['id', 'type', 'selector', 'priority']}
        })

    # 手动构建测试文件内容，避免字符串嵌套问题
    test_file_content = '''
import pytest
from playwright.sync_api import sync_playwright
import logging
import os

# 配置日志
logging.basicConfig(
    level=logging.{},
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class TestPageElements:
    @pytest.fixture(scope="class")
    def page(self):
        with sync_playwright() as p:
            browser = p.{}.launch(headless={})
            page = browser.new_page()
            page.set_default_timeout({} * 1000)

            # 自动登录
            self._auto_login(page)

            yield page
            browser.close()

    def _auto_login(self, page):
        """统一封装登录逻辑"""
        username = "{}"
        password = "{}"
        if not username or not password:
            return

        try:
            page.goto("{}")
            page.wait_for_load_state('networkidle', timeout={} * 1000)

            # 优先使用placeholder匹配，更通用
            username_selector = "input[placeholder*='用户名'], input[placeholder*='账号'], input[placeholder*='邮箱'], input[name='username'], input#username, input[type='text']"
            password_selector = "input[placeholder*='密码'], input[name='password'], input#password, input[type='password']"
            login_button_selector = "button[type='submit'], input[type='submit'], button:has-text('登录'), button:has-text('Login')"

            # 等待登录输入框出现，最多等3秒
            login_input = page.wait_for_selector(username_selector, timeout=3000)
            if login_input and login_input.is_visible():
                # 填充账号密码
                page.fill(username_selector, username)
                page.fill(password_selector, password)
                # 点击登录按钮
                page.click(login_button_selector)
                # 等待登录完成跳转
                page.wait_for_load_state('networkidle', timeout=10000)
                page.wait_for_timeout(2000)  # 额外等待页面稳定
                logger.info("✅ 自动登录成功")
        except Exception as e:
            logger.info("ℹ️ 登录失败或无需登录: " + str(e))

    def _run_element_test(self, page, test_case):
        """统一测试执行逻辑"""
        test_id = test_case['id']
        element_type = test_case['type']
        selector = test_case['selector']
        page_url = test_case['page_url']
        meta = test_case['meta']

        logger.info(f'开始测试: {{test_id}} - {{element_type}} - 页面: {{page_url}}')

        try:
            # 跳转到测试点所属页面
            if page_url != page.url:
                logger.info(f'🔄 跳转到测试页面: {{page_url}}')
                page.goto(page_url)
                page.wait_for_load_state('networkidle', timeout={} * 1000)

            # 根据元素类型执行对应测试
            if element_type == "button":
                button = page.wait_for_selector(selector, timeout=5000)  # 最多等待5秒元素出现
                assert button is not None, "按钮元素未找到"
                # 获取按钮文本
                button_text = button.text_content().strip() if button.text_content() else '无文本'
                logger.info(f"找到按钮: {button_text}")
                # 如果是登录按钮，先输入账号密码
                if "login-btn" in selector:
                    # 输入用户名
                    username_input = page.query_selector("input[placeholder='请输入用户名或邮箱']")
                    if username_input:
                        username_input.fill("{username}")
                        page.wait_for_timeout(500)
                        logger.info(f"已输入用户名: {{username}}")
                    # 输入密码
                    password_input = page.query_selector("input[placeholder='请输入密码']")
                    if password_input:
                        password_input.fill("{password}")
                        page.wait_for_timeout(500)
                        logger.info("已输入密码")

                # 点击前记录当前状态
                before_url = page.url

                button.click()

                # 根据按钮文本做针对性等待
                button_text_lower = button_text.lower()
                wait_success = False

                # 1. 新建/添加/创建类按钮：等待弹窗出现
                if any(keyword in button_text_lower for keyword in ['新建', '添加', '创建', '新增', 'new', 'add', 'create']):
                    try:
                        # 等待弹窗类元素出现（适配element-ui等常见框架）
                        page.wait_for_selector('.el-dialog, .modal, .dialog, .popup', timeout=3000)
                        logger.info(f"✅ 点击后弹窗成功弹出")
                        wait_success = True
                    except:
                        logger.info(f"ℹ️ 点击后未检测到弹窗，可能为其他操作")

                # 2. 提交/保存/确认类按钮：等待成功提示或页面跳转
                elif any(keyword in button_text_lower for keyword in ['提交', '保存', '确认', '确定', 'submit', 'save', 'confirm']):
                    try:
                        # 先等待成功提示
                        page.wait_for_selector('.el-message, .message, .notification, .toast', timeout=3000)
                        logger.info(f"✅ 点击后出现成功提示")
                        wait_success = True
                    except:
                        # 没有提示则等待页面跳转
                        try:
                            page.wait_for_url(lambda url: url != before_url, timeout=3000)
                            logger.info(f"✅ 点击后成功跳转到新页面: {page.url}")
                            wait_success = True
                        except:
                            logger.info(f"ℹ️ 点击后未检测到提示或跳转")

                # 3. 搜索/查询/筛选类按钮：等待列表加载
                elif any(keyword in button_text_lower for keyword in ['搜索', '查询', '筛选', '查找', 'search', 'query', 'filter']):
                    try:
                        # 等待列表类元素加载完成
                        page.wait_for_selector('.el-table, .table, .list, .grid', timeout=3000)
                        logger.info(f"✅ 点击后列表成功加载")
                        wait_success = True
                    except:
                        logger.info(f"ℹ️ 点击后未检测到列表变化")

                # 4. 下一页/上一页/翻页类按钮：等待URL参数变化或列表刷新
                elif any(keyword in button_text_lower for keyword in ['下一页', '上一页', '翻页', '分页', 'page', 'next', 'prev']):
                    try:
                        page.wait_for_url(lambda url: url != before_url, timeout=3000)
                        logger.info(f"✅ 点击后成功翻页，新URL: {page.url}")
                        wait_success = True
                    except:
                        logger.info(f"ℹ️ 点击后未检测到翻页")

                # 其他按钮：至少等待1秒让动态操作完成
                if not wait_success:
                    page.wait_for_timeout(1000)

                # 统一等待网络空闲
                page.wait_for_load_state('networkidle', timeout={page_load_timeout} * 1000)
                logger.info(f'测试通过: {{test_id}} - 按钮点击成功')

            elif element_type == "input":
                input_elem = page.wait_for_selector(selector, timeout=5000)
                assert input_elem is not None, "输入框元素未找到"
                input_elem.fill('测试输入')
                page.wait_for_timeout(1000)
                input_value = input_elem.input_value()
                assert input_value == '测试输入', f'输入失败 - 期望值: "测试输入", 实际值: "{{input_value}}"'
                logger.info(f'测试通过: {{test_id}} - 输入框填写成功')

            elif element_type == "link":
                link = page.wait_for_selector(selector, timeout=5000)
                assert link is not None, "链接元素未找到"
                # 获取链接文本和href
                link_text = link.text_content().strip() if link.text_content() else '无文本'
                href = link.get_attribute('href') or '无链接'
                logger.info(f"找到链接: {link_text}, 目标: {href}")
                # 记录点击前的URL
                before_url = page.url

                link.click()

                # 等待页面导航完成，最多等5秒
                try:
                    page.wait_for_url(lambda url: url != before_url, timeout=5000)
                    after_url = page.url
                    logger.info(f"✅ 链接点击成功，跳转到: {after_url}")
                except:
                    # 没有跳转则等待动态内容加载
                    page.wait_for_load_state('networkidle', timeout=3000)
                    logger.info(f"ℹ️ 链接点击成功，未发生页面跳转（可能为内部路由或js操作）")

                logger.info(f'测试通过: {{test_id}} - 链接点击成功')

            elif element_type in ["checkbox", "radio"]:
                input_elem = page.wait_for_selector(selector, timeout=5000)
                assert input_elem is not None, f'{{element_type}}元素未找到'
                input_elem.click()
                page.wait_for_timeout(1000)
                is_checked = input_elem.is_checked()
                assert is_checked, f'{{element_type}}未选中'
                logger.info(f'测试通过: {{test_id}} - {{element_type}}选中成功')

            elif element_type == "select":
                select_elem = page.wait_for_selector(selector, timeout=5000)
                assert select_elem is not None, "下拉菜单元素未找到"
                select_elem.select_option(index=0)
                page.wait_for_timeout(1000)
                selected_value = select_elem.input_value()
                assert selected_value, "下拉菜单选择失败"
                logger.info(f'测试通过: {{test_id}} - 下拉菜单选择成功')

            elif element_type == "textarea":
                textarea_elem = page.wait_for_selector(selector, timeout=5000)
                assert textarea_elem is not None, "文本域元素未找到"
                test_text = '测试文本内容'
                textarea_elem.fill(test_text)
                page.wait_for_timeout(1000)
                textarea_value = textarea_elem.input_value()
                assert textarea_value == test_text, f'文本域填写失败 - 期望值: "{{test_text}}", 实际值: "{{textarea_value}}"'
                logger.info(f'测试通过: {{test_id}} - 文本域填写成功')

            elif element_type == "form":
                form_elem = page.wait_for_selector(selector, timeout=5000)
                assert form_elem is not None, "表单元素未找到"
                logger.info(f'测试通过: {{test_id}} - 表单元素存在')

            else:
                logger.info(f'测试通过: {{test_id}} - {{element_type}}元素存在')

        except Exception as e:
            logger.error(f'测试失败: {{test_id}} - {{element_type}} - {{str(e)}}')
            # 尝试截图
            try:
                screenshot_dir = '{}'
                os.makedirs(screenshot_dir, exist_ok=True)
                screenshot_path = os.path.join(screenshot_dir, f'test_{{test_id}}_failure.png')
                page.screenshot(path=screenshot_path)
                logger.info(f'已保存失败截图: {{screenshot_path}}')
            except Exception as screenshot_error:
                logger.warning(f'截图失败: {{str(screenshot_error)}}')
            raise

    # 参数化测试用例
    @pytest.mark.parametrize("test_case", {}, ids=lambda x: x['id'])
    def test_element(self, page, test_case):
        """参数化测试入口"""
        self._run_element_test(page, test_case)
'''.format(
        log_level.upper(),
        browser_type,
        headless,
        page_load_timeout,
        username if username else "test002",
        password if password else "123456",
        url,
        page_load_timeout,
        page_load_timeout,
        page_load_timeout,
        page_load_timeout,
        screenshot_dir,
        test_cases
    ).strip()

    # 写入测试文件
    test_file_path = os.path.join('tests', 'test_page_elements.py')
    with open(test_file_path, 'w', encoding='utf-8') as f:
        f.write(test_file_content)

    print(f"✅ 已生成参数化测试文件，共 {len(filtered_test_points)} 个登录后页面测试点")
    return test_file_path
