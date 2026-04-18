from playwright.sync_api import sync_playwright
import logging
from urllib.parse import urlparse, urljoin

class PageAnalyzer:
    def __init__(self, url, config=None, username=None, password=None):
        self.url = url
        self.test_points = []
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.username = username
        self.password = password
        # 默认配置
        self.browser_type = config.get('DEFAULT', 'browser', fallback='chromium') if config else 'chromium'
        self.headless = config.getboolean('DEFAULT', 'headless', fallback=False) if config else False
        self.page_load_timeout = int(config.get('DEFAULT', 'page_load_timeout', fallback='30')) if config else 30
        # 多页面爬取配置
        self.visited_urls = set()  # 已访问的URL集合
        self.max_pages = int(config.get('DEFAULT', 'max_pages', fallback=20)) if config else 20  # 最大爬取页面数，防止无限爬取
        self.current_pages = 0  # 当前已爬取页面数
        self.base_domain = urlparse(url).netloc  # 基础域名，只爬取同域名页面
    
    def analyze_page(self):
        """分析页面元素，生成测试点（支持多页面）"""
        try:
            with sync_playwright() as p:
                # 根据配置选择浏览器
                browser = getattr(p, self.browser_type).launch(headless=self.headless)
                page = browser.new_page()
                # 设置超时时间
                page.set_default_timeout(self.page_load_timeout * 1000)
                page.goto(self.url)

                # ========== 新增自动登录逻辑 ==========
                if self.username and self.password:
                    # 适配登录页选择器，根据实际情况修改
                    try:
                        # 等待用户名输入框出现（判断是否在登录页）
                        # 优先使用placeholder匹配，更通用
                        username_selector = "input[placeholder*='用户名'], input[placeholder*='账号'], input[placeholder*='邮箱'], input[name='username'], input#username, input[type='text']"
                        password_selector = "input[placeholder*='密码'], input[name='password'], input#password, input[type='password']"

                        page.wait_for_selector(username_selector, timeout=3000)
                        # 填充账号密码
                        page.fill(username_selector, self.username)
                        page.fill(password_selector, self.password)
                        # 点击登录按钮
                        login_button_selector = "button[type='submit'], input[type='submit'], button:has-text('登录'), button:has-text('Login')"
                        page.click(login_button_selector)
                        # 等待登录完成跳转，最多等待5秒检查URL变化
                        login_success = False
                        for _ in range(10):
                            page.wait_for_timeout(500)
                            current_url = page.url
                            if 'dashboard' in current_url.lower() or 'login' not in current_url.lower():
                                login_success = True
                                break

                        page.wait_for_load_state('networkidle', timeout=5000)
                        page.wait_for_timeout(1000)

                        if login_success:
                            print(f"✅ 自动登录成功，已跳转到: {page.url}")
                        else:
                            print(f"⚠️  登录后URL未变化，当前页面: {page.url}")
                    except Exception as e:
                        print(f"ℹ️ 未检测到登录页或登录失败: {str(e)}")
                # ======================================

                # 登录完成后，获取当前页面URL（可能已经跳转到首页/dashboard）
                current_url = page.url
                print(f"🔍 登录后当前页面: {current_url}")
                print(f"🔍 开始多页面分析，最大分析页面数: {self.max_pages}")
                # 清空登录页面分析的测试点（如果有的话）
                self.test_points = []
                self._analyze_single_page(page, current_url)

                # 对测试点进行排序
                self._sort_test_points()

                # 为测试点添加标识
                self._add_test_identifiers()

                browser.close()
                print(f"✅ 页面分析完成，共分析了 {self.current_pages} 个页面，生成 {len(self.test_points)} 个测试点")
                return self.test_points
        except Exception as e:
            self.logger.error(f"页面分析失败: {str(e)}")
            return []

    def _analyze_single_page(self, page, current_url):
        """分析单个页面的元素，并收集内部链接"""
        # 暂时取消登录页面过滤，确保能分析到元素
        if current_url in self.visited_urls or self.current_pages >= self.max_pages:
            return

        # 标记为已访问
        self.visited_urls.add(current_url)
        self.current_pages += 1
        print(f"📄 正在分析页面 {self.current_pages}/{self.max_pages}: {current_url}")

        try:
            # 等待页面加载完成
            page.wait_for_load_state('networkidle', timeout=self.page_load_timeout * 1000)

            # 分析当前页面的可交互元素
            self._analyze_interactive_elements(page, current_url)

            # 收集页面上的所有内部链接，包括标准<a>标签和动态路由链接
            links = page.query_selector_all('a, [href], [to], [router-link]')
            internal_links = []

            for link in links:
                try:
                    # 尝试获取不同属性的链接
                    href = link.get_attribute('href') or link.get_attribute('to') or ''
                    if href:
                        # 解析链接，判断是否为内部链接
                        parsed_href = urlparse(href)
                        absolute_url = urljoin(current_url, href)
                        parsed_absolute = urlparse(absolute_url)

                        # 只处理同域名的http/https链接，排除静态资源和非页面链接
                        static_extensions = ('.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
                                            '.woff', '.woff2', '.ttf', '.eot', '.mp4', '.mp3', '.pdf',
                                            '.zip', '.rar', '.7z', '.exe', '.doc', '.docx', '.xls', '.xlsx')

                        if (parsed_absolute.netloc == self.base_domain
                            and parsed_absolute.scheme in ['http', 'https']
                            and not parsed_absolute.fragment
                            and not href.startswith('mailto:')
                            and not href.startswith('tel:')
                            and not href.startswith('javascript:')
                            and not href.startswith('#')
                            and not any(href.lower().endswith(ext) for ext in static_extensions)
                            and not any(parsed_absolute.path.lower().endswith(ext) for ext in static_extensions)):

                            if absolute_url not in self.visited_urls:
                                internal_links.append(absolute_url)

                except Exception as e:
                    self.logger.warning(f"处理链接失败: {str(e)}")

            # 去重
            internal_links = list(set(internal_links))
            print(f"🔗 当前页面找到 {len(internal_links)} 个内部链接")

            # 递归分析内部链接
            for link in internal_links:
                if self.current_pages >= self.max_pages:
                    break
                try:
                    page.goto(link)
                    self._analyze_single_page(page, link)
                except Exception as e:
                    self.logger.warning(f"访问链接失败 {link}: {str(e)}")

        except Exception as e:
            self.logger.warning(f"分析页面失败 {current_url}: {str(e)}")
    
    def _analyze_interactive_elements(self, page, page_url):
        """分析页面中的可交互元素 - 优化：去重+过滤无意义元素"""
        # 用于去重的集合
        unique_elements = set()

        # 分析按钮元素
        buttons = page.query_selector_all('button')
        for button in buttons:
            try:
                text = button.text_content().strip() if button.text_content() else ''
                selector = button.evaluate('(el) => el.tagName.toLowerCase() + (el.id ? `#${el.id}` : ``) + (el.className ? `.${el.className.split(" ").join(".")}` : ``)')

                # 过滤无意义的按钮
                useless_keywords = ['close', '关闭', 'collapse', '折叠', 'bell', '通知', 'tooltip', '提示',
                                'drawer__close', 'el-drawer__close', 'el-tooltip', 'action-btn']
                is_useless = any(keyword in selector.lower() for keyword in useless_keywords)
                if is_useless and not text:
                    continue

                # 去重：相同页面+相同选择器只保留一个
                element_key = f"{page_url}|{selector}"
                if element_key in unique_elements:
                    continue
                unique_elements.add(element_key)

                self.test_points.append({
                    'type': 'button',
                    'text': text,
                    'selector': selector,
                    'priority': self._calculate_priority('button', text),
                    'page_url': page_url
                })
            except Exception as e:
                self.logger.warning(f"分析按钮元素失败: {str(e)}")

        # 分析输入框元素
        inputs = page.query_selector_all('input')
        for input_elem in inputs:
            try:
                input_type = input_elem.get_attribute('type') or 'text'
                placeholder = input_elem.get_attribute('placeholder') or ''
                selector = input_elem.evaluate('(el) => el.tagName.toLowerCase() + (el.id ? `#${el.id}` : ``) + (el.className ? `.${el.className.split(" ").join(".")}` : ``)')

                # 过滤无意义的输入框（隐藏、搜索、下拉内部输入框等）
                if input_type in ['hidden', 'search', 'file'] or 'el-select__input' in selector.lower():
                    continue

                # 去重
                element_key = f"{page_url}|{selector}"
                if element_key in unique_elements:
                    continue
                unique_elements.add(element_key)

                # 根据输入类型进行分类
                if input_type in ['checkbox', 'radio']:
                    # 复选框和单选按钮
                    name = input_elem.get_attribute('name') or ''
                    value = input_elem.get_attribute('value') or ''
                    self.test_points.append({
                        'type': input_type,
                        'name': name,
                        'value': value,
                        'selector': selector,
                        'priority': self._calculate_priority(input_type, name),
                        'page_url': page_url
                    })
                else:
                    # 普通输入框
                    self.test_points.append({
                        'type': 'input',
                        'input_type': input_type,
                        'placeholder': placeholder,
                        'selector': selector,
                        'priority': self._calculate_priority('input', placeholder),
                        'page_url': page_url
                    })
            except Exception as e:
                self.logger.warning(f"分析输入框元素失败: {str(e)}")

        # 分析链接元素
        links = page.query_selector_all('a')
        for link in links:
            try:
                text = link.text_content().strip() if link.text_content() else ''
                href = link.get_attribute('href') or ''
                selector = link.evaluate('(el) => el.tagName.toLowerCase() + (el.id ? `#${el.id}` : ``) + (el.className ? `.${el.className.split(" ").join(".")}` : ``)')

                # 过滤空文本和无意义链接
                if not text and not href:
                    continue

                # 去重
                element_key = f"{page_url}|{selector}"
                if element_key in unique_elements:
                    continue
                unique_elements.add(element_key)

                self.test_points.append({
                    'type': 'link',
                    'text': text,
                    'href': href,
                    'selector': selector,
                    'priority': self._calculate_priority('link', text),
                    'page_url': page_url
                })
            except Exception as e:
                self.logger.warning(f"分析链接元素失败: {str(e)}")

        # 分析下拉菜单元素
        selects = page.query_selector_all('select')
        for select in selects:
            try:
                name = select.get_attribute('name') or ''
                id = select.get_attribute('id') or ''
                selector = select.evaluate('(el) => el.tagName.toLowerCase() + (el.id ? `#${el.id}` : ``) + (el.className ? `.${el.className.split(" ").join(".")}` : ``)')
                # 获取选项数量
                options = select.query_selector_all('option')
                option_count = len(options)

                # 去重
                element_key = f"{page_url}|{selector}"
                if element_key in unique_elements:
                    continue
                unique_elements.add(element_key)

                self.test_points.append({
                    'type': 'select',
                    'name': name,
                    'id': id,
                    'option_count': option_count,
                    'selector': selector,
                    'priority': self._calculate_priority('select', name),
                    'page_url': page_url
                })
            except Exception as e:
                self.logger.warning(f"分析下拉菜单元素失败: {str(e)}")

        # 分析文本域元素
        textareas = page.query_selector_all('textarea')
        for textarea in textareas:
            try:
                name = textarea.get_attribute('name') or ''
                placeholder = textarea.get_attribute('placeholder') or ''
                selector = textarea.evaluate('(el) => el.tagName.toLowerCase() + (el.id ? `#${el.id}` : ``) + (el.className ? `.${el.className.split(" ").join(".")}` : ``)')

                # 去重
                element_key = f"{page_url}|{selector}"
                if element_key in unique_elements:
                    continue
                unique_elements.add(element_key)

                self.test_points.append({
                    'type': 'textarea',
                    'name': name,
                    'placeholder': placeholder,
                    'selector': selector,
                    'priority': self._calculate_priority('textarea', name),
                    'page_url': page_url
                })
            except Exception as e:
                self.logger.warning(f"分析文本域元素失败: {str(e)}")

        # 分析表单元素
        forms = page.query_selector_all('form')
        for form in forms:
            try:
                action = form.get_attribute('action') or ''
                method = form.get_attribute('method') or 'get'
                selector = form.evaluate('(el) => el.tagName.toLowerCase() + (el.id ? `#${el.id}` : ``) + (el.className ? `.${el.className.split(" ").join(".")}` : ``)')

                # 去重
                element_key = f"{page_url}|{selector}"
                if element_key in unique_elements:
                    continue
                unique_elements.add(element_key)

                self.test_points.append({
                    'type': 'form',
                    'action': action,
                    'method': method,
                    'selector': selector,
                    'priority': self._calculate_priority('form', action),
                    'page_url': page_url
                })
            except Exception as e:
                self.logger.warning(f"分析表单元素失败: {str(e)}")
    
    def _calculate_priority(self, element_type, text):
        """计算元素的优先级 - 优化：更合理的优先级判断"""
        high_priority_keywords = ['提交', '登录', '删除', '保存', '确认', '搜索', '发送', '发布',
                                '创建', '新增', '确定', '同意', '拒绝', '审核', '提交']
        medium_priority_keywords = ['编辑', '修改', '查看', '详情', '返回', '导出', '导入',
                                    '下载', '上传', '重置', '取消', '预览']

        text_lower = text.lower()

        # 有文本的按钮优先级更高
        if element_type == 'button' and text:
            for keyword in high_priority_keywords:
                if keyword in text:
                    return 'high'
            for keyword in medium_priority_keywords:
                if keyword in text:
                    return 'medium'
            return 'medium'  # 只要有文本的按钮至少是medium优先级

        # 有placeholder的输入框优先级更高
        if element_type in ['input', 'textarea'] and text:
            return 'medium'

        # 有文本的链接优先级更高
        if element_type == 'link' and text:
            return 'medium'

        return 'low'
    
    def _sort_test_points(self):
        """根据优先级排序测试点"""
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        self.test_points.sort(key=lambda x: priority_order.get(x['priority'], 2))
    
    def _add_test_identifiers(self):
        """为测试点添加标识"""
        for i, test_point in enumerate(self.test_points, 1):
            test_point['id'] = f'test{i:03d}'
    
    def print_test_points(self):
        """打印测试点列表"""
        print("\n分析出的测试点:")
        print("-" * 80)
        for test_point in self.test_points:
            print(f"{test_point['id']} - {test_point['type']} - {test_point['priority']}优先级")
            print(f"  所属页面: {test_point['page_url']}")
            if test_point['type'] == 'button':
                print(f"  文本: {test_point['text']}")
            elif test_point['type'] == 'input':
                print(f"  类型: {test_point['input_type']}")
                print(f"  占位符: {test_point['placeholder']}")
            elif test_point['type'] == 'link':
                print(f"  文本: {test_point['text']}")
                print(f"  链接: {test_point['href']}")
            elif test_point['type'] in ['checkbox', 'radio']:
                print(f"  名称: {test_point['name']}")
                print(f"  值: {test_point['value']}")
            elif test_point['type'] == 'select':
                print(f"  名称: {test_point['name']}")
                print(f"  ID: {test_point['id']}")
                print(f"  选项数量: {test_point['option_count']}")
            elif test_point['type'] == 'textarea':
                print(f"  名称: {test_point['name']}")
                print(f"  占位符: {test_point['placeholder']}")
            elif test_point['type'] == 'form':
                print(f"  动作: {test_point['action']}")
                print(f"  方法: {test_point['method']}")
            print(f"  选择器: {test_point['selector']}")
            print("-" * 80)