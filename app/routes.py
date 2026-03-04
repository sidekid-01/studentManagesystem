from flask import render_template, redirect, url_for, flash, request
from sqlalchemy.exc import IntegrityError
from app import app, db
from app.models import Student, Teacher, Course, GradeSheet, activities, Notification
from app.forms import StudentForm, TeacherForm, CourseForm, activityForm, LoginForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User


def notify_teacher_of_task(task, ntype, message, ec=None):
    course = db.session.get(Course, task.course_id)
    if not course:
        return
    teacher = db.session.get(Teacher, course.teacher_id)
    if not teacher or not teacher.user_id:
        return

    notif = Notification(
        recipient_id=teacher.user_id,
        type=ntype,
        message=message,
        task_id=task.id,
        ec_id=ec.id if ec else None,
    )
    db.session.add(notif)


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    actform = activityForm()
    if actform.validate_on_submit():
        act = activities(activity_name=actform.activityname.data)
        db.session.add(act)
        db.session.commit()
        return redirect(url_for('index'))

    acts = activities.query.all()
    return render_template('index.html', form=actform, acts=acts)


@app.route('/studentpage', methods=['GET', 'POST'])
@login_required
def studentpage():
    sform = StudentForm()
    if sform.validate_on_submit():
        student = Student(
            name=sform.name.data,
            major=sform.major.data,
            studentnumber=sform.studentnumber.data,
            gpa=sform.gpa.data,
        )
        db.session.add(student)
        db.session.commit()
        return redirect(url_for('studentpage'))

    students = Student.query.all()
    return render_template('studentpage.html', form=sform, students=students)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('无效的用户名或密码 / Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('index'))
    return render_template('login.html', title='登录 / Login', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


from app.models import Task, ECRequest
from app.forms import ECSubmissionForm, ECEditForm, DeadlineEditForm


@app.route('/my_tasks', methods=['GET', 'POST'])
@login_required
def my_tasks():
    if current_user.role != 'student':
        flash("只有学生可以访问个人任务页面 / Only students can access this page")
        return redirect(url_for('index'))

    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash("未找到对应的学生信息，请联系管理员。/ Student record not found, please contact admin.")
        return redirect(url_for('index'))

    all_tasks = Task.query.all()
    form = ECSubmissionForm()
    form.task_id.choices = [(t.id, t.title) for t in all_tasks]

    if form.validate_on_submit():
        new_ec = ECRequest(
            student_id=student.id,
            task_id=form.task_id.data,
            reason=form.reason.data,
            evidence_link=form.evidence_link.data,
            status='pending'
        )
        db.session.add(new_ec)
        db.session.commit()
        flash("EC 申请已提交，请等待 Wellbeing 部门审核。/ EC application submitted, pending Wellbeing review.")
        return redirect(url_for('my_tasks'))

    my_ecs = ECRequest.query.filter_by(student_id=student.id).all()
    return render_template('my_tasks.html', tasks=all_tasks, form=form, my_ecs=my_ecs)


@app.route('/wellbeing/manage')
@login_required
def wellbeing_manage():
    if current_user.role != 'wellbeing' and current_user.role != 'admin':
        flash("无权访问该页面 / You do not have permission to access this page")
        return redirect(url_for('index'))

    all_ecs = ECRequest.query.all()
    return render_template('wellbeing_manage.html', ecs=all_ecs)


@app.route('/wellbeing/approve/<int:ec_id>/<string:action>')
@login_required
def approve_ec(ec_id, action):
    if current_user.role != 'wellbeing' and current_user.role != 'admin':
        flash("无权操作 / Permission denied")
        return redirect(url_for('index'))

    ec = db.session.get(ECRequest, ec_id)
    if ec:
        if action == 'approve':
            ec.status = 'approved'
            flash(f"已通过 {ec.student.name} 的申请 / Application by {ec.student.name} has been approved")
            notify_teacher_of_task(
                ec.task,
                ntype='ec_approved',
                message=(
                    f"学生 {ec.student.name} 对任务《{ec.task.title}》的 EC 申请已获批准，延期 {ec.extension_days} 天。"
                    f" / Student {ec.student.name}'s EC application for '{ec.task.title}' has been approved, "
                    f"with an extension of {ec.extension_days} day(s)."
                ),
                ec=ec
            )
        elif action == 'reject':
            ec.status = 'rejected'
            flash(f"已拒绝 {ec.student.name} 的申请 / Application by {ec.student.name} has been rejected")
            notify_teacher_of_task(
                ec.task,
                ntype='ec_rejected',
                message=(
                    f"学生 {ec.student.name} 对任务《{ec.task.title}》的 EC 申请已被拒绝。"
                    f" / Student {ec.student.name}'s EC application for '{ec.task.title}' has been rejected."
                ),
                ec=ec
            )
        db.session.commit()

    return redirect(url_for('wellbeing_manage'))


@app.route('/admin/ec/edit/<int:ec_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_ec(ec_id):
    if current_user.role != 'admin':
        flash("仅 Admin 可操作 / Admin access only")
        return redirect(url_for('index'))

    ec = db.session.get(ECRequest, ec_id)
    if not ec:
        flash("找不到该申请 / Application not found")
        return redirect(url_for('wellbeing_manage'))

    form = ECEditForm(obj=ec)

    if form.validate_on_submit():
        ec.status = form.status.data
        ec.extension_days = form.extension_days.data

        notify_teacher_of_task(
            ec.task,
            ntype='ec_updated',
            message=(
                f"Admin 已更新学生 {ec.student.name} 对任务《{ec.task.title}》的 EC 申请："
                f"状态变更为 {ec.status}，延期 {ec.extension_days} 天。"
                f" / Admin has updated {ec.student.name}'s EC application for '{ec.task.title}':"
                f" status changed to {ec.status}, extension of {ec.extension_days} day(s)."
            ),
            ec=ec
        )

        db.session.commit()
        flash(
            f"已更新 {ec.student.name} 的 EC 申请（延期 {ec.extension_days} 天，状态：{ec.status}）"
            f" / Updated {ec.student.name}'s EC application (extension: {ec.extension_days} day(s), status: {ec.status})"
        )
        return redirect(url_for('wellbeing_manage'))

    return render_template('admin_edit_ec.html', form=form, ec=ec)


@app.route('/admin/tasks', methods=['GET'])
@login_required
def admin_tasks():
    if current_user.role != 'admin':
        flash("仅 Admin 可操作 / Admin access only")
        return redirect(url_for('index'))

    tasks = Task.query.order_by(Task.deadline).all()
    return render_template('admin_tasks.html', tasks=tasks)


@app.route('/admin/tasks/edit/<int:task_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_deadline(task_id):
    if current_user.role != 'admin':
        flash("仅 Admin 可操作 / Admin access only")
        return redirect(url_for('index'))

    task = db.session.get(Task, task_id)
    if not task:
        flash("找不到该任务 / Task not found")
        return redirect(url_for('admin_tasks'))

    form = DeadlineEditForm(obj=task)

    if form.validate_on_submit():
        old_deadline = task.deadline.strftime('%Y-%m-%d %H:%M')
        task.deadline = form.deadline.data
        new_deadline = task.deadline.strftime('%Y-%m-%d %H:%M')

        notify_teacher_of_task(
            task,
            ntype='deadline_changed',
            message=(
                f"任务《{task.title}》的截止日期已由 {old_deadline} 更新为 {new_deadline}。"
                f" / The deadline for '{task.title}' has been updated from {old_deadline} to {new_deadline}."
            )
        )

        db.session.commit()
        flash(
            f"已将《{task.title}》的截止日期更新为 {new_deadline}"
            f" / Deadline for '{task.title}' updated to {new_deadline}"
        )
        return redirect(url_for('admin_tasks'))

    if request.method == 'GET':
        form.deadline.data = task.deadline

    return render_template('admin_edit_deadline.html', form=form, task=task)


@app.route('/teacher/notifications')
@login_required
def teacher_notifications():
    if current_user.role != 'teacher':
        flash("仅 Teacher 可访问 / Teacher access only")
        return redirect(url_for('index'))

    notifications = (
        Notification.query
        .filter_by(recipient_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )
    return render_template('teacher_notifications.html', notifications=notifications)


@app.route('/teacher/notifications/read/<int:notif_id>')
@login_required
def mark_notification_read(notif_id):
    notif = db.session.get(Notification, notif_id)
    if notif and notif.recipient_id == current_user.id:
        notif.is_read = True
        db.session.commit()
    return redirect(url_for('teacher_notifications'))


@app.route('/teacher/notifications/read_all')
@login_required
def mark_all_notifications_read():
    if current_user.role != 'teacher':
        return redirect(url_for('index'))
    Notification.query.filter_by(
        recipient_id=current_user.id, is_read=False
    ).update({'is_read': True})
    db.session.commit()
    flash("已将所有通知标为已读。/ All notifications marked as read.")
    return redirect(url_for('teacher_notifications'))


@app.context_processor
def inject_unread_notification_count():
    count = 0
    if current_user.is_authenticated and current_user.role == 'teacher':
        count = Notification.query.filter_by(
            recipient_id=current_user.id, is_read=False
        ).count()
    return dict(unread_notification_count=count)