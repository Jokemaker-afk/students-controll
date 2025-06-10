#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模板路径修复脚本
检查并修复可能的模板路径问题
"""

import os
import re

def check_templates():
    """检查模板文件和引用路径的匹配情况"""
    print("🔍 开始检查模板文件...")
    
    # 获取所有模板文件
    templates_dir = "student/templates"
    template_files = []
    
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                rel_path = os.path.relpath(os.path.join(root, file), templates_dir)
                template_files.append(rel_path.replace('\\', '/'))
    
    print(f"📄 找到模板文件 {len(template_files)} 个:")
    for tf in sorted(template_files):
        print(f"  ✅ {tf}")
    
    # 检查Python文件中的render_template调用
    print(f"\n🔍 检查Python文件中的模板引用...")
    
    python_files = ['student/view.py', 'student/auth.py']
    template_refs = []
    
    for py_file in python_files:
        if os.path.exists(py_file):
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # 查找render_template调用
                matches = re.findall(r"render_template\(['\"]([^'\"]+)['\"]", content)
                for match in matches:
                    template_refs.append((py_file, match))
    
    print(f"📋 找到模板引用 {len(template_refs)} 个:")
    missing_templates = []
    
    for py_file, template_ref in template_refs:
        exists = template_ref in template_files
        status = "✅" if exists else "❌"
        print(f"  {status} {py_file}: {template_ref}")
        if not exists:
            missing_templates.append((py_file, template_ref))
    
    if missing_templates:
        print(f"\n⚠️  发现 {len(missing_templates)} 个缺失的模板引用:")
        for py_file, template_ref in missing_templates:
            print(f"  ❌ {py_file} -> {template_ref}")
            
            # 尝试找到相似的模板文件
            similar = find_similar_template(template_ref, template_files)
            if similar:
                print(f"     💡 建议使用: {similar}")
    else:
        print(f"\n🎉 所有模板引用都正确!")

def find_similar_template(target, template_files):
    """找到相似的模板文件"""
    target_name = os.path.basename(target)
    target_dir = os.path.dirname(target)
    
    # 先尝试找同名文件
    for template in template_files:
        if os.path.basename(template) == target_name:
            return template
    
    # 尝试找相似名称
    target_lower = target_name.lower()
    for template in template_files:
        template_name = os.path.basename(template).lower()
        if target_lower in template_name or template_name in target_lower:
            return template
    
    return None

if __name__ == "__main__":
    print("🚀 开始检查模板路径...")
    check_templates()
    print("\n✅ 检查完成！") 