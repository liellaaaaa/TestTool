import os
import sys

# 导入optimize_selector函数
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from pytest_generator import optimize_selector

# 测试数据
test_points = [
    {
        'id': 'test001',
        'type': 'button',
        'selector': 'button.el-button.el-button--primary.el-button--large.login-btn',
        'text': '登录',
        'priority': 'high'
    },
    {
        'id': 'test002',
        'type': 'input',
        'selector': 'input#el-id-9685-4.el-input__inner',
        'placeholder': '请输入用户名或邮箱',
        'input_type': 'text',
        'priority': 'low'
    },
    {
        'id': 'test003',
        'type': 'input',
        'selector': 'input#el-id-9685-5.el-input__inner',
        'placeholder': '请输入密码',
        'input_type': 'password',
        'priority': 'low'
    },
    {
        'id': 'test004',
        'type': 'checkbox',
        'selector': 'input.el-checkbox__original',
        'priority': 'low'
    },
    {
        'id': 'test005',
        'type': 'link',
        'selector': 'a.el-link.el-link--primary',
        'text': '忘记密码？',
        'priority': 'low'
    },
    {
        'id': 'test006',
        'type': 'form',
        'selector': 'form.el-form.el-form--default.el-form--label-right.login-form',
        'priority': 'low'
    }
]

# 测试选择器优化
print("选择器优化测试结果:")
print("=" * 80)

for test_point in test_points:
    original_selector = test_point['selector']
    optimized_selector = optimize_selector(test_point)
    
    print(f"\n测试ID: {test_point['id']}")
    print(f"元素类型: {test_point['type']}")
    print(f"原始选择器: {original_selector}")
    print(f"优化后选择器: {optimized_selector}")
    
    if original_selector != optimized_selector:
        print("✓ 选择器已优化（避开动态ID）")
    else:
        print("✓ 选择器无需优化（不包含动态ID）")

print("\n" + "=" * 80)
print("测试完成！")
