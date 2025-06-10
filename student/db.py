from functools import wraps

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum
import click
from flask import current_app, abort
from flask.cli import with_appcontext
from flask_login import current_user

# 创建SQLAlchemy实例
db = SQLAlchemy()


# 定义用户角色枚举
class UserRole(PyEnum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


# 定义User模型
class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(80), unique=True, nullable=False)
    password = Column(String(200), nullable=False)
    # 添加角色字段
    role = Column(Enum(UserRole), nullable=False, default=UserRole.STUDENT)

    # 关系：学生的成绩记录
    grades = relationship('Grade', backref='student', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.username}({self.role.value})>'

    # Flask-Login所需的方法（UserMixin已提供默认实现，这里可以自定义）
    def get_id(self):
        """返回用户唯一标识符"""
        return str(self.id)

    @property
    def is_authenticated(self):
        """返回用户是否已认证"""
        return True

    @property
    def is_active(self):
        """返回用户是否激活"""
        return True

    @property
    def is_anonymous(self):
        """返回用户是否为匿名用户"""
        return False

    # 权限检查方法
    def is_admin(self):
        """检查是否为管理员"""
        return self.role == UserRole.ADMIN

    def is_teacher(self):
        """检查是否为老师"""
        return self.role == UserRole.TEACHER

    def is_student(self):
        """检查是否为学生"""
        return self.role == UserRole.STUDENT

    def can_view_user(self, target_user):
        """检查是否可以查看目标用户信息"""
        # admin可以查看所有用户
        if self.is_admin():
            return True
        # teacher可以查看所有学生
        if self.is_teacher() and target_user.is_student():
            return True
        # 用户可以查看自己的信息
        if self.id == target_user.id:
            return True
        return False

    def can_delete_user(self, target_user):
        """检查是否可以删除目标用户"""
        # 只有admin可以删除用户
        if not self.is_admin():
            return False
        # admin不能删除自己
        if self.id == target_user.id:
            return False
        # admin可以删除student和teacher
        return target_user.is_student() or target_user.is_teacher()

    def can_view_all_students(self):
        """检查是否可以查看所有学生信息"""
        return self.is_admin() or self.is_teacher()

    def can_manage_courses(self):
        """检查是否可以管理课程"""
        return self.is_admin()

    def can_view_student_grades(self, target_student):
        """检查是否可以查看学生成绩"""
        # admin和teacher可以查看所有学生成绩
        if self.is_admin() or self.is_teacher():
            return True
        # 学生只能查看自己的成绩
        if self.is_student() and self.id == target_student.id:
            return True
        return False

    def get_courses(self):
        """获取学生的所有课程"""
        if not self.is_student():
            return []
        return [grade.course for grade in self.grades]

    def get_grade_in_course(self, course_id):
        """获取学生在某门课程的成绩"""
        if not self.is_student():
            return None
        grade = Grade.query.filter_by(student_id=self.id, course_id=course_id).first()
        return grade.score if grade else None

    def check_password(self, password):
        """验证密码"""
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password, password)

    def set_password(self, password):
        """设置新密码"""
        from werkzeug.security import generate_password_hash
        self.password = generate_password_hash(password)


# 定义Course模型（课程）
class Course(db.Model):
    __tablename__ = 'course'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(500))
    credits = Column(Integer, default=1)  # 学分
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系：课程的成绩记录
    grades = relationship('Grade', backref='course', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Course {self.name}>'

    def get_students(self):
        """获取选修此课程的所有学生"""
        return [grade.student for grade in self.grades]

    def get_student_count(self):
        """获取选修此课程的学生数量"""
        return len(self.grades)

    def get_average_score(self):
        """获取此课程的平均分"""
        scores = [grade.score for grade in self.grades if grade.score is not None]
        return sum(scores) / len(scores) if scores else 0


# 定义Grade模型（成绩，连接学生和课程）
class Grade(db.Model):
    __tablename__ = 'grade'

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    course_id = Column(Integer, ForeignKey('course.id'), nullable=False)
    score = Column(Float)  # 成绩分数
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Grade {self.student.username}-{self.course.name}: {self.score}>'

    def get_letter_grade(self):
        """将数字成绩转换为等级"""
        if self.score is None:
            return "未评分"
        elif self.score >= 90:
            return "A"
        elif self.score >= 80:
            return "B"
        elif self.score >= 70:
            return "C"
        elif self.score >= 60:
            return "D"
        else:
            return "F"



def get_db():
    """获取数据库session"""
    return db.session


def init_db():
    """初始化数据库表"""
    db.create_all()



def require_role(*allowed_roles):
    """要求特定角色的装饰器"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)  # 未认证

            if current_user.role not in allowed_roles:
                abort(403)  # 权限不足

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def require_admin(f):
    """要求管理员权限的装饰器"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            abort(403)
        return f(*args, **kwargs)

    return decorated_function


def can_access_user(target_user_id):
    """检查是否可以访问指定用户信息的装饰器"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)

            target_user = User.query.get_or_404(target_user_id)

            if not current_user.can_view_user(target_user):
                abort(403)

            return f(*args, **kwargs)

        return decorated_function

    return decorator


@click.command('init-db')
@with_appcontext
def init_db_command():
    """清除现有数据并创建新表"""
    init_db()
    click.echo('数据库初始化完成。')


def init_app(app):
    """初始化数据库配置"""
    # 配置PostgreSQL连接
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:ytagqk12@localhost:2454/student'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 初始化数据库
    db.init_app(app)

    # 添加命令
    app.cli.add_command(init_db_command)



