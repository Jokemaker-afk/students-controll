from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from .db import db, User, Course, Grade, UserRole, require_role, require_admin

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """首页"""
    return render_template('index.html')


@bp.route('/dashboard')
@login_required
def dashboard():
    """根据用户角色重定向到相应仪表板"""
    if current_user.is_admin():
        return redirect(url_for('main.admin_dashboard'))
    elif current_user.is_teacher():
        return redirect(url_for('main.teacher_dashboard'))
    else:
        return redirect(url_for('main.student_dashboard'))


@bp.route('/admin')
@login_required
@require_admin
def admin_dashboard():
    """管理员仪表板"""
    # 获取统计信息
    total_users = User.query.count()
    total_students = User.query.filter_by(role=UserRole.STUDENT).count()
    total_teachers = User.query.filter_by(role=UserRole.TEACHER).count()
    total_courses = Course.query.count()

    # 获取最近注册的用户
    recent_users = User.query.order_by(User.id.desc()).limit(5).all()

    return render_template('admin/dashboardadmin.html',
                           total_users=total_users,
                           total_students=total_students,
                           total_teachers=total_teachers,
                           total_courses=total_courses,
                           recent_users=recent_users)


@bp.route('/teacher')
@login_required
@require_role(UserRole.TEACHER, UserRole.ADMIN)
def teacher_dashboard():
    """教师仪表板"""
    # 获取所有课程
    courses = Course.query.all()

    # 获取所有学生
    students = User.query.filter_by(role=UserRole.STUDENT).all()

    # 获取最近的成绩记录
    recent_grades = Grade.query.order_by(Grade.updated_at.desc()).limit(10).all()

    return render_template('teacher/dashboardteacher.html',
                           courses=courses,
                           students=students,
                           recent_grades=recent_grades)


@bp.route('/student')
@login_required
@require_role(UserRole.STUDENT, UserRole.TEACHER, UserRole.ADMIN)
def student_dashboard():
    """学生仪表板"""
    if current_user.is_student():
        # 学生只能看自己的信息
        grades = current_user.grades
        courses = current_user.get_courses()
    else:
        # 教师和管理员可以看到概览
        grades = Grade.query.limit(10).all()
        courses = Course.query.limit(10).all()

    return render_template('student/dashboardstudent.html',
                           grades=grades,
                           courses=courses)


@bp.route('/users')
@login_required
@require_role(UserRole.ADMIN, UserRole.TEACHER)
def list_users():
    """用户列表页面"""
    if current_user.is_teacher():
        # 教师只能看学生
        users = User.query.filter_by(role=UserRole.STUDENT).all()
    else:
        # 管理员可以看所有用户
        users = User.query.all()

    return render_template('admin/users.html', users=users)


@bp.route('/courses')
@login_required
def list_courses():
    """课程列表"""
    courses = Course.query.all()
    return render_template('courses/courselist.html', courses=courses)


@bp.route('/courses/<int:course_id>')
@login_required
def course_detail(course_id):
    """课程详情"""
    course = Course.query.get_or_404(course_id)

    # 检查权限
    if current_user.is_student():
        # 学生只能查看自己选修的课程
        grade = Grade.query.filter_by(student_id=current_user.id, course_id=course_id).first()
        if not grade:
            flash('您没有选修此课程', 'error')
            return redirect(url_for('main.list_courses'))

    students = course.get_students()
    grades = course.grades

    return render_template('courses/detail.html',
                           course=course,
                           students=students,
                           grades=grades)


@bp.route('/grades')
@login_required
def list_grades():
    """成绩列表"""
    if current_user.is_student():
        grades = current_user.grades
    else:
        grades = Grade.query.all()

    return render_template('grade/list.html', grades=grades)


# API路由
@bp.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
@require_admin
def delete_user(user_id):
    """删除用户API"""
    target_user = User.query.get_or_404(user_id)

    if not current_user.can_delete_user(target_user):
        return jsonify({'error': '权限不足'}), 403

    try:
        db.session.delete(target_user)
        db.session.commit()
        return jsonify({'message': '用户删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'删除失败: {str(e)}'}), 500


# 课程管理路由
@bp.route('/courses/add', methods=['POST'])
@login_required
@require_admin
def add_course():
    """添加新课程"""
    name = request.form.get('name')
    description = request.form.get('description')
    credits = request.form.get('credits', 3, type=int)
    
    if not name:
        flash('课程名称不能为空', 'error')
        return redirect(url_for('main.list_courses'))
    
    # 检查课程是否已存在
    existing_course = Course.query.filter_by(name=name).first()
    if existing_course:
        flash(f'课程 "{name}" 已存在', 'error')
        return redirect(url_for('main.list_courses'))
    
    try:
        new_course = Course(
            name=name,
            description=description,
            credits=credits
        )
        db.session.add(new_course)
        db.session.commit()
        flash(f'课程 "{name}" 添加成功！', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'添加课程失败: {str(e)}', 'error')
    
    return redirect(url_for('main.list_courses'))


@bp.route('/courses/<int:course_id>/delete', methods=['DELETE'])
@login_required
@require_admin
def delete_course(course_id):
    """删除课程"""
    course = Course.query.get_or_404(course_id)
    
    try:
        course_name = course.name
        # 删除课程会自动删除相关的成绩记录（cascade设置）
        db.session.delete(course)
        db.session.commit()
        return jsonify({'message': f'课程 "{course_name}" 删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'删除课程失败: {str(e)}'}), 500


