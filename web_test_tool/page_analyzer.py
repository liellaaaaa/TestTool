from playwright.sync_api import sync_playwright
import logging

class PageAnalyzer:
    def __init__(self, url, config=None):
        self.url = url
        self.test_points = []
        self.logger = logging.getLogger(__name__)
        self.config = config
        # 默认配置
        self.browser_type = config.get('DEFAULT', 'browser', fallback='chromium') if config else 'chromium'
        self.headless = config.getboolean('DEFAULT', 'headless', fallback=False) if config else False
        self.page_load_timeout = int(config.get('DEFAULT', 'page_load_timeout', fallback='30')) if config else 30
    
    def analyze_page(self):
        """分析页面元素，生成测试点"""
        try:
            with sync_playwright() as p:
                # 根据配置选择浏览器
                browser = getattr(p, self.browser_type).launch(headless=self.headless)
                page = browser.new_page()
                # 设置超时时间
                page.set_default_timeout(self.page_load_timeout * 1000)
                page.goto(self.url)
                
                # 分析可交互元素
                self._analyze_interactive_elements(page)
                
                # 对测试点进行排序
                self._sort_test_points()
                
                # 为测试点添加标识
                self._add_test_identifiers()
                
                browser.close()
                return self.test_points
        except Exception as e:
            self.logger.error(f"页面分析失败: {str(e)}")
            return []
    
    def _analyze_interactive_elements(self, page):
        """分析页面中的可交互元素"""
        # 分析按钮元素
        buttons = page.query_selector_all('button')
        for button in buttons:
            try:
                text = button.text_content().strip() if button.text_content() else ''
                selector = button.evaluate('(el) => el.tagName.toLowerCase() + (el.id ? `#${el.id}` : ``) + (el.className ? `.${el.className.split(" ").join(".")}` : ``)')
                self.test_points.append({
                    'type': 'button',
                    'text': text,
                    'selector': selector,
                    'priority': self._calculate_priority('button', text)
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
                        'priority': self._calculate_priority(input_type, name)
                    })
                else:
                    # 普通输入框
                    self.test_points.append({
                        'type': 'input',
                        'input_type': input_type,
                        'placeholder': placeholder,
                        'selector': selector,
                        'priority': self._calculate_priority('input', placeholder)
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
                self.test_points.append({
                    'type': 'link',
                    'text': text,
                    'href': href,
                    'selector': selector,
                    'priority': self._calculate_priority('link', text)
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
                self.test_points.append({
                    'type': 'select',
                    'name': name,
                    'id': id,
                    'option_count': option_count,
                    'selector': selector,
                    'priority': self._calculate_priority('select', name)
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
                self.test_points.append({
                    'type': 'textarea',
                    'name': name,
                    'placeholder': placeholder,
                    'selector': selector,
                    'priority': self._calculate_priority('textarea', name)
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
                self.test_points.append({
                    'type': 'form',
                    'action': action,
                    'method': method,
                    'selector': selector,
                    'priority': self._calculate_priority('form', action)
                })
            except Exception as e:
                self.logger.warning(f"分析表单元素失败: {str(e)}")
    
    def _calculate_priority(self, element_type, text):
        """计算元素的优先级"""
        high_priority_keywords = ['提交', '登录', '删除', '保存', '确认', '搜索']
        medium_priority_keywords = ['编辑', '修改', '查看', '详情', '返回']
        
        text_lower = text.lower()
        
        for keyword in high_priority_keywords:
            if keyword in text:
                return 'high'
        
        for keyword in medium_priority_keywords:
            if keyword in text:
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