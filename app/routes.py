import os
import uuid
from flask import render_template, redirect, url_for, flash, request, send_from_directory, abort
from werkzeug.utils import secure_filename
from app import app, db
from app.models import Student, Teacher, Course, GradeSheet, activities, Notification
from app.forms import StudentForm, TeacherForm, CourseForm, activityForm, LoginForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'pdf'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file_storage):
    if not file_storage or not file_storage.filename:
        return None
    if not allowed_file(file_storage.filename):
        return None
    ext = file_storage.filename.rsplit('.', 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    file_storage.save(os.path.join(UPLOAD_FOLDER, unique_name))
    return unique_name

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
            flash('Invalid username or password.')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('index'))
    return render_template('login.html', title='Login', form=form)


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
        flash("Only students can access this page.")
        return redirect(url_for('index'))
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash("Student record not found. Please contact admin.")
        return redirect(url_for('index'))
    all_tasks = Task.query.all()
    form = ECSubmissionForm()
    form.task_id.choices = [(t.id, t.title) for t in all_tasks]
    if form.validate_on_submit():
        filename = save_uploaded_file(form.evidence_file.data)
        new_ec = ECRequest(
            student_id=student.id,
            task_id=form.task_id.data,
            reason=form.reason.data,
            evidence_link=form.evidence_link.data or None,
            evidence_filename=filename,
            status='pending'
        )
        db.session.add(new_ec)
        db.session.commit()
        flash("EC application submitted successfully. Pending Wellbeing review.")
        return redirect(url_for('my_tasks'))
    my_ecs = ECRequest.query.filter_by(student_id=student.id).all()
    return render_template('my_tasks.html', tasks=all_tasks, form=form, my_ecs=my_ecs)


@app.route('/evidence/view/<int:ec_id>')
@login_required
def view_evidence(ec_id):
    ec = db.session.get(ECRequest, ec_id)
    if not ec:
        abort(404)
    is_owner = (current_user.role == 'student' and ec.student.user_id == current_user.id)
    is_staff = current_user.role in ('admin', 'wellbeing')
    if not is_owner and not is_staff:
        abort(403)
    if not ec.evidence_filename:
        abort(404)
    return send_from_directory(UPLOAD_FOLDER, ec.evidence_filename)


@app.route('/evidence/download/<int:ec_id>')
@login_required
def download_evidence(ec_id):
    ec = db.session.get(ECRequest, ec_id)
    if not ec:
        abort(404)
    is_staff = current_user.role in ('admin', 'wellbeing')
    if not is_staff:
        abort(403)
    if not ec.evidence_filename:
        abort(404)
    ext = ec.evidence_filename.rsplit('.', 1)[1]
    download_name = secure_filename(f"{ec.student.name}_{ec.task.title}.{ext}")
    return send_from_directory(UPLOAD_FOLDER, ec.evidence_filename,
                               as_attachment=True, download_name=download_name)


@app.route('/wellbeing/manage')
@login_required
def wellbeing_manage():
    if current_user.role not in ('wellbeing', 'admin'):
        flash("You do not have permission to access this page.")
        return redirect(url_for('index'))
    all_ecs = ECRequest.query.all()
    return render_template('wellbeing_manage.html', ecs=all_ecs)


@app.route('/wellbeing/approve/<int:ec_id>/<string:action>')
@login_required
def approve_ec(ec_id, action):
    if current_user.role not in ('wellbeing', 'admin'):
        flash("Permission denied.")
        return redirect(url_for('index'))
    ec = db.session.get(ECRequest, ec_id)
    if ec:
        if action == 'approve':
            ec.status = 'approved'
            flash(f"Application by {ec.student.name} has been approved.")
            notify_teacher_of_task(
                ec.task, ntype='ec_approved',
                message=(
                    f"Student {ec.student.name}'s EC application for '{ec.task.title}' "
                    f"has been approved, with an extension of {ec.extension_days} day(s)."
                ), ec=ec
            )
        elif action == 'reject':
            ec.status = 'rejected'
            flash(f"Application by {ec.student.name} has been rejected.")
            notify_teacher_of_task(
                ec.task, ntype='ec_rejected',
                message=(
                    f"Student {ec.student.name}'s EC application for '{ec.task.title}' has been rejected."
                ), ec=ec
            )
        db.session.commit()
    return redirect(url_for('wellbeing_manage'))


@app.route('/admin/ec/edit/<int:ec_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_ec(ec_id):
    if current_user.role != 'admin':
        flash("Admin access only.")
        return redirect(url_for('index'))
    ec = db.session.get(ECRequest, ec_id)
    if not ec:
        flash("Application not found.")
        return redirect(url_for('wellbeing_manage'))
    form = ECEditForm(obj=ec)
    if form.validate_on_submit():
        ec.status = form.status.data
        ec.extension_days = form.extension_days.data
        notify_teacher_of_task(
            ec.task, ntype='ec_updated',
            message=(
                f"Admin has updated {ec.student.name}'s EC application for '{ec.task.title}': "
                f"status changed to {ec.status}, extension of {ec.extension_days} day(s)."
            ), ec=ec
        )
        db.session.commit()
        flash(f"Updated {ec.student.name}'s EC application — status: {ec.status}, extension: {ec.extension_days} day(s).")
        return redirect(url_for('wellbeing_manage'))
    return render_template('admin_edit_ec.html', form=form, ec=ec)


@app.route('/admin/tasks', methods=['GET'])
@login_required
def admin_tasks():
    if current_user.role != 'admin':
        flash("Admin access only.")
        return redirect(url_for('index'))
    tasks = Task.query.order_by(Task.deadline).all()
    return render_template('admin_tasks.html', tasks=tasks)


@app.route('/admin/tasks/edit/<int:task_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_deadline(task_id):
    if current_user.role != 'admin':
        flash("Admin access only.")
        return redirect(url_for('index'))
    task = db.session.get(Task, task_id)
    if not task:
        flash("Task not found.")
        return redirect(url_for('admin_tasks'))
    form = DeadlineEditForm(obj=task)
    if form.validate_on_submit():
        old_deadline = task.deadline.strftime('%Y-%m-%d %H:%M')
        task.deadline = form.deadline.data
        new_deadline = task.deadline.strftime('%Y-%m-%d %H:%M')
        notify_teacher_of_task(
            task, ntype='deadline_changed',
            message=(
                f"The deadline for '{task.title}' has been updated "
                f"from {old_deadline} to {new_deadline}."
            )
        )
        db.session.commit()
        flash(f"Deadline for '{task.title}' updated to {new_deadline}.")
        return redirect(url_for('admin_tasks'))
    if request.method == 'GET':
        form.deadline.data = task.deadline
    return render_template('admin_edit_deadline.html', form=form, task=task)


@app.route('/teacher/notifications')
@login_required
def teacher_notifications():
    if current_user.role != 'teacher':
        flash("Teacher access only.")
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
    flash("All notifications marked as read.")
    return redirect(url_for('teacher_notifications'))


@app.context_processor
def inject_unread_notification_count():
    count = 0
    if current_user.is_authenticated and current_user.role == 'teacher':
        count = Notification.query.filter_by(
            recipient_id=current_user.id, is_read=False
        ).count()
    return dict(unread_notification_count=count)