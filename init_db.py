from app import app, db
from app.models import User, Teacher, Student, Course, Task
from datetime import datetime, timedelta


with app.app_context():
    db.drop_all()
    db.create_all()
    print("✅ Database tables rebuilt")

    admin = User(username='admin', role='admin')
    admin.set_password('admin123')

    wellbeing = User(username='wellbeing1', role='wellbeing')
    wellbeing.set_password('wellbeing123')

    teacher_user = User(username='teacher1', role='teacher')
    teacher_user.set_password('teacher123')

    student_user = User(username='student1', role='student')
    student_user.set_password('student123')

    db.session.add_all([admin, wellbeing, teacher_user, student_user])
    db.session.flush()
    print("✅ User accounts created")

    teacher = Teacher(
        name='John Smith',
        major='School of Computing',
        TeacherNumber=10001,
        Teacheremail='johnsmith@edu.com',
        user_id=teacher_user.id
    )
    db.session.add(teacher)
    db.session.flush()
    print("✅ Teacher record created and linked")

    course = Course(
        classname='Introduction to Python',
        teacher_id=teacher.id
    )
    db.session.add(course)
    db.session.flush()
    print("✅ Course created")

    student = Student(
        name='Alice Lee',
        major='Computer Science',
        studentnumber=20240001,
        gpa=3.5,
        user_id=student_user.id
    )
    db.session.add(student)
    db.session.flush()
    print("✅ Student record created and linked")

    task1 = Task(
        title='Assignment 1: Python Basics',
        description='Complete all exercises in Chapter 3 of the textbook',
        deadline=datetime.now() + timedelta(days=7),
        course_id=course.id
    )
    task2 = Task(
        title='Midterm Project: Data Analysis Report',
        description='Analyse the provided dataset using pandas and write a report',
        deadline=datetime.now() + timedelta(days=14),
        course_id=course.id
    )
    db.session.add_all([task1, task2])

    db.session.commit()
    print("✅ Tasks created")

    print("\n" + "=" * 50)
    print("🎉 Initialisation complete! Login credentials:")
    print("=" * 50)
    print(f"  Role        Username       Password")
    print(f"  admin       admin          admin123")
    print(f"  wellbeing   wellbeing1     wellbeing123")
    print(f"  teacher     teacher1       teacher123")
    print(f"  student     student1       student123")
    print("=" * 50)
    print("\nTo test the notification flow:")
    print("  1. Log in as admin → edit a Task deadline or approve an EC")
    print("  2. Log in as teacher1 → red badge appears in sidebar → click to view notifications")
    print("=" * 50)