#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL数据库初始化脚本
使用前请确保：
1. PostgreSQL服务已启动
2. 已创建数据库 student
3. 用户名和密码正确配置
"""

import psycopg2
from psycopg2 import sql
import sys
import os

# 设置环境编码
os.environ['PGCLIENTENCODING'] = 'UTF8'

def create_database():
    """创建PostgreSQL数据库"""
    try:
        print("🔗 尝试连接到PostgreSQL服务器...")
        # 连接到PostgreSQL服务器（连接到默认的postgres数据库）
        # 使用连接字符串方式，避免编码问题
        conn_string = "host='localhost' port='2454' user='postgres' password='ytagqk12' dbname='postgres' client_encoding='UTF8'"
        conn = psycopg2.connect(conn_string)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("✅ 成功连接到PostgreSQL服务器")
        
        # 检查数据库是否已存在
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'student'")
        exists = cursor.fetchone()
        
        if not exists:
            # 创建数据库
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier("student")
            ))
            print("✅ 数据库 'student' 创建成功！")
        else:
            print("ℹ️  数据库 'student' 已存在")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ 数据库连接失败: {e}")
        print("💡 请检查：")
        print("   - PostgreSQL服务是否运行")
        print("   - 端口2454是否正确")
        print("   - 用户名和密码是否正确")
        return False
    except UnicodeDecodeError as e:
        print(f"❌ 编码错误: {e}")
        print("💡 这可能是系统编码问题，请尝试设置环境变量 PGCLIENTENCODING=UTF8")
        return False
    except Exception as e:
        print(f"❌ 数据库创建失败: {e}")
        print(f"❌ 错误类型: {type(e).__name__}")
        return False

def verify_connection():
    """测试数据库连接"""
    try:
        print("🔗 尝试连接到student数据库...")
        # 使用连接字符串方式，避免编码问题
        conn_string = "host='localhost' port='2454' user='postgres' password='ytagqk12' dbname='student' client_encoding='UTF8'"
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ 数据库连接成功！PostgreSQL版本: {version[0]}")
        cursor.close()
        conn.close()
        return True
    except psycopg2.OperationalError as e:
        print(f"❌ 数据库连接失败: {e}")
        print("💡 请检查：")
        print("   - student数据库是否存在")
        print("   - PostgreSQL服务是否运行")
        print("   - 端口2454是否正确")
        print("   - 用户名和密码是否正确")
        return False
    except UnicodeDecodeError as e:
        print(f"❌ 编码错误: {e}")
        print("💡 这可能是系统编码问题，请尝试设置环境变量 PGCLIENTENCODING=UTF8")
        return False
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        print(f"❌ 错误类型: {type(e).__name__}")
        return False

if __name__ == "__main__":
    print("🚀 开始初始化PostgreSQL数据库...")
    print("📋 配置信息:")
    print("   - 主机: localhost")
    print("   - 端口: 2454")
    print("   - 用户: postgres")
    print("   - 数据库: student")
    print()
    
    # 创建数据库
    if create_database():
        # 验证连接
        if verify_connection():
            print()
            print("🎉 数据库初始化完成！")
            print("📝 下一步:")
            print("   1. 安装依赖: pip install -r requirements.txt")
            print("   2. 初始化Flask应用: flask --app student init-db")
            print("   3. 运行应用: flask --app student run")
        else:
            sys.exit(1)
    else:
        sys.exit(1) 