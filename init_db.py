from app import app, db
from app.models import User, Teacher, Student, Course, Task
from datetime import datetime, timedelta



#no need to read it is just a database creat tool


with app.app_context():
    # ── 1. 清空并重建所有表 ──────────────────────────────────────────────
    db.drop_all()
    db.create_all()
    print("✅ 数据库表已重建")

    # ── 2. 创建用户账号 ──────────────────────────────────────────────────
    admin = User(username='admin', role='admin')
    admin.set_password('admin123')

    wellbeing = User(username='wellbeing1', role='wellbeing')
    wellbeing.set_password('wellbeing123')

    teacher_user = User(username='teacher1', role='teacher')
    teacher_user.set_password('teacher123')

    student_user = User(username='student1', role='student')
    student_user.set_password('student123')

    db.session.add_all([admin, wellbeing, teacher_user, student_user])
    db.session.flush()  # 让 id 生效，不用 commit
    print("✅ 用户账号已创建")

    # ── 3. 创建 Teacher 记录，绑定 user_id ──────────────────────────────
    teacher = Teacher(
        name='张伟',
        major='计算机学院',
        TeacherNumber=10001,
        Teacheremail='zhangwei@edu.com',
        user_id=teacher_user.id      # 关键：绑定到 teacher1 账号
    )
    db.session.add(teacher)
    db.session.flush()
    print("✅ Teacher 记录已创建并关联账号")

    # ── 4. 创建 Course，归属该 teacher ───────────────────────────────────
    course = Course(
        classname='Python 程序设计',
        teacher_id=teacher.id
    )
    db.session.add(course)
    db.session.flush()
    print("✅ Course 已创建")

    # ── 5. 创建 Student 记录，绑定 user_id ──────────────────────────────
    student = Student(
        name='李明',
        major='计算机科学',
        studentnumber=20240001,
        gpa=3.5,
        user_id=student_user.id      # 关键：绑定到 student1 账号
    )
    db.session.add(student)
    db.session.flush()
    print("✅ Student 记录已创建并关联账号")

    # ── 6. 创建 Task（截止日期分别为 7 天后和 14 天后）───────────────────
    task1 = Task(
        title='作业一：Python 基础练习',
        description='完成教材第三章所有练习题',
        deadline=datetime.now() + timedelta(days=7),
        course_id=course.id
    )
    task2 = Task(
        title='期中项目：数据分析报告',
        description='使用 pandas 对给定数据集进行分析并撰写报告',
        deadline=datetime.now() + timedelta(days=14),
        course_id=course.id
    )
    db.session.add_all([task1, task2])

    # ── 7. 提交所有数据 ──────────────────────────────────────────────────
    db.session.commit()
    print("✅ Task 已创建")

    print("\n" + "="*50)
    print("🎉 初始化完成！以下是登录账号：")
    print("="*50)
    print(f"  角色        用户名         密码")
    print(f"  admin     admin          admin123")
    print(f"  wellbeing wellbeing1     wellbeing123")
    print(f"  teacher   teacher1       teacher123")
    print(f"  student   student1       student123")
    print("="*50)
    print("\n测试通知功能流程：")
    print("  1. 用 admin 登录 → 修改 Task deadline 或审批 EC")
    print("  2. 用 teacher1 登录 → 侧边栏出现红点 → 点击查看通知")
    print("="*50)