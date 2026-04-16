虚拟环境
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
cd web_test_tool
.venv\Scripts\activate
python main.py

## 1. 工具简介

网页测试工具是一个自动化测试工具，用于模拟用户行为测试网页程序，特别适用于需求文档助手这样的应用。它可以：

- 自动分析页面元素并生成测试点
- 支持多种测试选择方式
- 执行测试并生成详细的测试报告
- 提供失败截图和错误日志

## 2. 安装和依赖

### 2.1 安装Python

工具需要Python 3.7或更高版本。请从[Python官网](https://www.python.org/downloads/)下载并安装。

### 2.2 安装依赖

```bash
# 安装playwright
pip install playwright

# 安装浏览器驱动
playwright install
```

## 3. 配置说明

工具使用`config.ini`文件进行配置，位于项目根目录。以下是配置项说明：

| 配置项 | 说明 | 默认值 |
|-------|------|-------|
| browser | 浏览器类型（chromium, firefox, webkit） | chromium |
| headless | 是否使用无头模式 | false |
| page_load_timeout | 页面加载超时时间（秒） | 30 |
| element_timeout | 元素操作超时时间（秒） | 10 |
| screenshot_dir | 截图保存目录 | screenshots |
| report_dir | 报告保存目录 | reports |
| log_level | 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL） | INFO |
| default_test_selection | 默认测试选择 | all |
| generate_pytest | 是否生成pytest测试文件 | true |

## 4. 使用步骤

### 4.1 启动工具

在项目根目录执行：

```bash
python main.py
```

### 4.2 输入测试URL

工具会提示输入要测试的网页URL：

```
请输入要测试的网页URL: https://example.com
```

### 4.3 分析页面元素

工具会自动分析页面中的可交互元素，包括：
- 按钮
- 输入框
- 链接
- 复选框
- 单选按钮
- 下拉菜单
- 文本域
- 表单

分析完成后，工具会按优先级排序并显示所有测试点：

```
分析出的测试点:
--------------------------------------------------------------------------------
test001 - button - high优先级
  文本: 提交
  选择器: button#submit
--------------------------------------------------------------------------------
test002 - input - medium优先级
  类型: text
  占位符: 请输入用户名
  选择器: input#username
--------------------------------------------------------------------------------
```

### 4.4 选择测试方式

工具支持多种测试选择方式：

1. 输入 `all` 运行所有测试
2. 输入测试ID，如 `1,3,5` 运行指定测试
3. 输入范围，如 `1-5` 运行test001到test005
4. 输入元素类型，如 `button` 运行所有按钮测试
5. 输入优先级，如 `high` 运行所有高优先级测试

示例：
```
请选择要运行的测试:
1. 输入 'all' 运行所有测试
2. 输入测试ID，如 '1,3,5' 运行指定测试
3. 输入范围，如 '1-5' 运行test001到test005
4. 输入元素类型，如 'button' 运行所有按钮测试
5. 输入优先级，如 'high' 运行所有高优先级测试
请输入选择: 1-3
```

### 4.5 执行测试

工具会执行选定的测试，并实时显示测试进度：

```
开始运行测试: test001, test002, test003
```

### 4.6 查看测试结果

测试完成后，工具会显示测试结果汇总：

```
--------------------------------------------------------------------------------
测试结果汇总:
总测试数: 3
通过: 2
失败: 1

失败的测试: test002
失败详情请查看test.log文件
--------------------------------------------------------------------------------

测试报告已生成: reports/test_report_20260416_123456.html
```

## 5. 测试结果分析

### 5.1 日志文件

测试过程中的详细信息会记录在 `test.log` 文件中，包括：
- 测试开始和结束时间
- 测试执行过程
- 错误信息
- 截图路径

### 5.2 测试报告

工具会生成HTML格式的测试报告，位于 `reports` 目录中。报告包含：
- 测试摘要（总测试数、通过数、失败数、成功率）
- 详细测试结果
- 失败测试的截图

### 5.3 失败截图

测试失败时，工具会自动截图并保存在 `screenshots` 目录中，文件名为 `{test_id}_failure.png`。

## 6. 生成pytest测试文件

工具会自动生成pytest测试文件，位于 `tests` 目录中。您可以使用pytest运行这些测试：

```bash
pytest tests/test_page_elements.py -v
```

## 7. 常见问题和解决方案

### 7.1 模块导入错误

**错误信息**：`ModuleNotFoundError: No module named 'playwright'`

**解决方案**：安装playwright模块：
```bash
pip install playwright
playwright install
```

### 7.2 浏览器启动失败

**错误信息**：`Error: Failed to launch browser`

**解决方案**：确保已安装浏览器驱动：
```bash
playwright install
```

### 7.3 测试超时

**错误信息**：`TimeoutError: Page load timed out`

**解决方案**：在 `config.ini` 文件中增加超时时间：
```ini
page_load_timeout = 60
```

### 7.4 元素未找到

**错误信息**：`元素未找到 - 选择器: xxx`

**解决方案**：检查选择器是否正确，或调整页面加载等待时间。

## 8. 项目结构

```
web_test_tool/
├── main.py              # 主入口文件
├── page_analyzer.py     # 页面元素分析模块
├── test_runner.py       # 测试运行模块
├── pytest_generator.py  # pytest测试文件生成模块
├── config.ini           # 配置文件
├── screenshots/         # 失败截图目录
├── reports/             # 测试报告目录
└── tests/               # pytest测试文件目录
```

## 9. 总结

网页测试工具是一个功能强大的自动化测试工具，可以帮助您快速测试网页程序的各种功能。通过简单的配置和操作，您可以：

- 自动分析页面元素并生成测试点
- 灵活选择测试范围
- 执行测试并获取详细的测试结果
- 生成美观的测试报告
- 利用pytest进行更深入的测试

该工具特别适合测试需求文档助手这样的应用，帮助您确保网页功能的正常运行。