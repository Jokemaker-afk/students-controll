# 学生管理系统 - 设置说明

## ✅ 问题已解决！

你的Flask应用现在可以正常工作了！从日志可以看到：
- ✅ 应用启动成功
- ✅ 登录功能正常
- ✅ 用户认证工作正常
- ✅ 模板问题已修复

## 最新修复

### 模板文件名修复
修复了模板文件名不匹配的问题：
- `auth/change_password.html` → `auth/changepassword.html`
- `auth/login.html` 路径标准化

## 关于Flask-Login集成

### 为什么必须添加Flask-Login支持？

你的应用代码中使用了Flask-Login的功能：
- `login_user(user)` - 在 `auth.py` 中登录用户
- `logout_user()` - 在 `auth.py` 中登出用户
- `current_user` - 在模板中显示当前用户信息
- `@login_required` - 装饰器保护需要登录的页面

Flask-Login要求User模型实现特定的方法和属性：
- `is_authenticated` - 用户是否已认证
- `is_active` - 用户是否激活
- `is_anonymous` - 用户是否为匿名用户
- `get_id()` - 获取用户唯一标识符

### 解决方案

1. **继承UserMixin**: 这个类提供了Flask-Login所需的默认实现
2. **添加必要方法**: 确保Flask-Login能正确工作
3. **正确导入**: 使用`from flask_login import current_user`

## 安装依赖

在你的虚拟环境中运行：

```bash
pip install -r requirements.txt
```

## 数据库配置

请确保你的 PostgreSQL 数据库配置正确：

1. 数据库名: `student`
2. 用户名: `postgres` 
3. 密码: `ytagqk12`
4. 主机: `localhost`
5. 端口: `2454`

如果你的数据库配置不同，请修改 `student/db.py` 文件中的连接字符串。

## 初始化数据库

运行以下命令初始化数据库表：

```bash
flask --app student init-db
```

## 测试应用

你可以运行测试脚本来验证应用配置：

```bash
python test_app.py
```

## 运行应用

```bash
flask --app student run
```

现在你的应用应该可以正常运行了！访问 http://127.0.0.1:5000 即可看到首页。

## 功能验证

现在你可以测试以下功能：
- ✅ 访问首页
- ✅ 用户注册
- ✅ 用户登录
- ✅ 修改密码
- ✅ 个人资料
- ✅ 基于角色的访问控制

## 重要提示

**不要删除Flask-Login相关的代码**，因为你的应用依赖这些功能来实现用户认证。如果你不想使用Flask-Login，需要重写整个认证系统。 