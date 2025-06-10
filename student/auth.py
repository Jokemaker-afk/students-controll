import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from student.db import db, User, get_db, UserRole

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form.get('role', 'student')  # 默认为学生角色
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'

        valid_roles = [role.value for role in UserRole]
        if role not in valid_roles:
            error = '请选择有效的角色。'

        if error is None:
            # 检查用户是否已存在
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                error = f"User {username} is already registered."
            else:
                try:
                    # 将字符串角色转换为枚举
                    user_role = UserRole(role)

                    new_user = User(
                        username=username,
                        password=generate_password_hash(password),
                        role=user_role
                    )
                    db.session.add(new_user)
                    db.session.commit()

                    flash(f'注册成功！欢迎您，{username}（{user_role.value}）', 'success')
                    return redirect(url_for("auth.login"))
                except Exception as e:
                    db.session.rollback()
                    error = f"注册失败: {str(e)}"
        flash(error, 'error')
    return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None
        if not username:
            error = '用户名不能为空。'
        elif not password:
            error = '密码不能为空。'
        if error is None:
            user = User.query.filter_by(username=username).first()
            if user is None:
                error = '用户名不存在。'
            elif not user.check_password(password):     #---------------------------
                error = '密码错误。'

        if error is None:
            login_user(user)  # Flask-Login登录用户
            flash(f'欢迎回来，{user.username}！', 'success')

            # 根据角色重定向到不同页面
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            elif user.is_admin():
                return redirect(url_for('main.admin_dashboard'))
            elif user.is_teacher():
                return redirect(url_for('main.teacher_dashboard'))
            else:
                return redirect(url_for('main.student_dashboard'))
        else:
            flash(error, 'error')

    return render_template('auth/login.html')

@bp.route('/logout')
@login_required
def logout():
    username = current_user.username
    logout_user()  # Flask-Login登出用户
    flash(f'再见，{username}！', 'info')
    return redirect(url_for('main.index'))


@bp.route('/profile')
@login_required
def profile():
    """用户个人资料页面"""
    return render_template('auth/profile.html', user=current_user)


@bp.route('/change_password', methods=('GET', 'POST'))
@login_required
def change_password():
    """修改密码"""
    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        error = None

        if not old_password:
            error = '请输入当前密码。'
        elif not new_password:
            error = '请输入新密码。'
        elif new_password != confirm_password:
            error = '两次输入的新密码不一致。'
        elif not current_user.check_password(old_password):     #----------------------
            error = '当前密码错误。'

        if error is None:
            try:
                current_user.set_password(new_password)            # ------------------
                db.session.commit()
                flash('密码修改成功！', 'success')
                return redirect(url_for('auth.profile'))
            except Exception as e:
                db.session.rollback()
                error = f"密码修改失败: {str(e)}"

        if error:
            flash(error, 'error')

    return render_template('auth/changepassword.html')