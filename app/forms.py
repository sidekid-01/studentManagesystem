from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, FloatField, IntegerField
from wtforms.validators import DataRequired, Email, NumberRange, Optional
from wtforms import PasswordField, BooleanField
from wtforms import StringField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired
from wtforms.fields import DateTimeLocalField


class StudentForm(FlaskForm):
    name = StringField('姓名 / Name', validators=[DataRequired()])
    major = StringField('专业 / Major', validators=[DataRequired()])
    studentnumber = IntegerField('学号 / Student ID', validators=[DataRequired()])
    gpa = FloatField('GPA', validators=[DataRequired()])
    submit = SubmitField('添加学生 / Add Student')

class TeacherForm(FlaskForm):
    name = StringField('老师姓名 / Teacher Name', validators=[DataRequired()])
    major = StringField('所属学院/专业 / Faculty  Department', validators=[DataRequired()])
    teacher_number = IntegerField('教工号 / Staff ID', validators=[DataRequired()])
    email = StringField('邮箱 / Email', validators=[DataRequired(), Email()])
    submit = SubmitField('添加老师信息 / Add Teacher')

class CourseForm(FlaskForm):
    classname = StringField('课程名称 / Course Name', validators=[DataRequired()])
    teacher_id = IntegerField('授课教师ID / Teacher ID', validators=[DataRequired()])
    submit = SubmitField('创建课程 / Create Course')

class activityForm(FlaskForm):
    activityname = StringField('活动名称 / Activity Name', validators=[DataRequired()])

class LoginForm(FlaskForm):
    username = StringField('用户名 / Username', validators=[DataRequired()])
    password = PasswordField('密码 / Password', validators=[DataRequired()])
    remember_me = BooleanField('记住我 / Remember Me')
    submit = SubmitField('登录 / Login')

class ECSubmissionForm(FlaskForm):
    task_id = SelectField('选择需要延期的任务 / Select Task', coerce=int, validators=[DataRequired()])
    reason = TextAreaField('申请理由 / Reason for Extension', validators=[DataRequired()], render_kw={"rows": 5})
    evidence_link = StringField('证明材料链接 (可选) / Evidence Link (Optional)')
    submit = SubmitField('提交 EC 申请 / Submit EC Application')

class ECEditForm(FlaskForm):
    """Admin 修改 EC 申请的延期天数和状态 / Admin edit EC application status and extension days"""
    status = SelectField('审批状态 / Approval Status', choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], validators=[DataRequired()])
    extension_days = IntegerField('延期天数 / Extension Days', validators=[DataRequired(), NumberRange(min=0, max=365)])
    submit = SubmitField('保存修改 / Save Changes')

class DeadlineEditForm(FlaskForm):
    """Admin 修改任务截止日期 / Admin edit task deadline"""
    deadline = DateTimeLocalField('新截止日期 / New Deadline', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    submit = SubmitField('更新 Deadline / Update Deadline')