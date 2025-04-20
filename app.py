from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from db_connection import get_db_connection

app = Flask(__name__)
app.secret_key = "qwe"

@app.route('/test_message')
def test_message():
    message = "This is a test message!"
    return render_template('index.html', message=message)




# Login Authentication
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    role = request.form['role'].lower()

    print(f"Username: {username}, Password: {password}, Role: {role}")  # Debugging

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch user details from the database
    query = "SELECT * FROM user WHERE name = %s AND password = %s AND role = %s"
    cursor.execute(query, (username, password, role))
    user = cursor.fetchone()
    print(f"User: {user}")
    conn.close()

    if user:
        # Store user ID and role in the session
        session['user_id'] = user[0]
        session['role'] = role
        print(f"Role set in session: {session['role']}")

        if role == "teacher":
            session['teacher_id'] = user[0]
        elif role == "student":
            session['student_id'] = user[1]
        elif role == "admin":
            session['admin_id'] = user[0]  # Store admin ID as well if needed

        flash(f"Login successful as {role.capitalize()}!", "success")
        return redirect(url_for('dashboard'))  # Redirect to dashboard after successful login
    else:
        # Invalid credentials
        flash("Invalid credentials! Please try again.", "error")
        return redirect('/') # Redirect back to the login page if login fails


# Registration Route
@app.route('/register')
def register():
    return render_template('register.html')


# Registration Logic
@app.route('/register_user', methods=['POST'])
def register_user():
    username = request.form['username']
    email = request.form['email']  # Get the email from the form
    password = request.form['password']
    role = request.form['role']

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Insert data including the email
        query = "INSERT INTO user (name, email, password, role) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (username, email, password, role))
        conn.commit()
        flash("Registration successful!", "success")
    except mysql.connector.Error as err:
        flash(f"Error: {err}", "danger")
    finally:
        conn.close()

    return redirect(url_for('register'))



# Dashboard
@app.route('/dashboard', methods=['GET'])
def dashboard():
    # Get the role from the session
    role = session.get('role')
    print(f"Role from session: {role}")

    if not role:
        return "Role not found in session", 400  # Ensure that role is available

    if role == 'student':
        return render_template('student.html', role=role.capitalize())  # Pass the role from session
    elif role == 'teacher':
        return render_template('teacher.html', role=role.capitalize())  # Pass the role from session
    elif role == 'admin':
        return render_template('admin.html', role=role.capitalize())  # Pass the role from session
    else:
        return "Invalid Role", 400

@app.route('/')
def home():
    flash("Welcome to RDBMS EXAM!", "info")
    return render_template('login.html')  # Ensure login.html exists in the templates folder

@app.route('/profile')
def profile():
    role = session.get('role')
    user_id = session.get('user_id')

    if not user_id:
        return redirect(url_for('login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch user details from the 'user' table
        cursor.execute("SELECT name, email, password, role FROM user WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()

        if result:
            user_name, email, password, role = result
        else:
            user_name, email, password, role = "Unknown User", "", "", ""

        # Initialize role-specific variables
        extra_id, extra_id2, extra_id3 = None, None, None

        if role == "student":
            cursor.execute("SELECT student_id, course_id, enrollment_date FROM student WHERE user_id = %s", (user_id,))
            student_data = cursor.fetchone()
            if student_data:
                extra_id, extra_id2, extra_id3 = student_data

        elif role == "teacher":
            cursor.execute("SELECT teacher_id, subject_id, course_id FROM teachers WHERE user_id = %s", (user_id,))
            teacher_data = cursor.fetchone()
            if teacher_data:
                extra_id, extra_id2, extra_id3 = teacher_data

        # Since admin info is in 'user', no need to query another table
        admin_id = user_id if role == "admin" else None

        cursor.close()
        conn.close()

        return render_template(
            'profile.html',
            role=role,
            user_name=user_name,
            email=email,
            password=password,
            extra_id=extra_id,
            extra_id2=extra_id2,
            extra_id3=extra_id3,
            admin_id=admin_id
        )
    except Exception as e:
        print("Error fetching profile data:", str(e))
        return f"Error loading profile: {str(e)}", 500

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        flash("You must be logged in to update your profile.", "danger")
        return redirect(url_for('login'))

    user_id = session['user_id']
    name = request.form['name']
    email = request.form['email']
    new_password = request.form['password']  # New password input

    conn = get_db_connection()
    cursor = conn.cursor()

    if new_password:
        cursor.execute("UPDATE user SET name=%s, email=%s, password=%s WHERE user_id=%s",
                       (name, email, new_password, user_id))
    else:
        cursor.execute("UPDATE user SET name=%s, email=%s WHERE user_id=%s",
                       (name, email, user_id))

    conn.commit()
    conn.close()

    flash("Profile updated successfully!", "success")
    return redirect(url_for('profile'))

# User Management Route
@app.route('/user_management', methods=['GET', 'POST'])
def user_management():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get the selected role from the request
    role_filter = request.args.get('roleFilter')

    # If a role filter is provided, adjust the query
    if role_filter:
        cursor.execute("SELECT user_id, name, email, role FROM user WHERE role = %s", (role_filter,))
    else:
        cursor.execute("SELECT user_id, name, email, role FROM user")

    users = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('user_management.html', users=users)


@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO user (name, email, password, role) VALUES (%s, %s, %s, %s)",
                           (name, email, password, role))
            conn.commit()
            flash(f"User '{name}' added successfully!", "success")
        except Exception as e:
            flash(f"Error adding user: {str(e)}", "danger")
        finally:
            conn.close()
        return redirect(url_for('user_management'))
    return render_template('add_user.html')


@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch the user's role before deletion
    cursor.execute("SELECT role FROM user WHERE user_id = %s", (user_id,))
    role = cursor.fetchone()

    if role and role[0] == 'Admin':  # Prevent admin deletion
        conn.close()
        flash("Cannot delete an Admin user!", "danger")
        return redirect(url_for('user_management'))

    try:
        cursor.execute("DELETE FROM user WHERE user_id = %s", (user_id,))
        conn.commit()
        flash("User deleted successfully!", "success")
    except Exception as e:
        flash(f"Error deleting user: {str(e)}", "danger")
    finally:
        conn.close()

    return redirect(url_for('user_management'))


# Course Management Route
@app.route('/course_management')
def course_management():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT course_id, course_name FROM course")
    courses = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('course_management.html', courses=courses)


# Add Course Page
@app.route('/add_course', methods=['GET', 'POST'])
def add_course():
    if request.method == 'POST':
        course_name = request.form['course_name']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO course (course_name) VALUES (%s)", (course_name,))
        conn.commit()
        conn.close()

        flash("Course added successfully!")
        return redirect(url_for('course_management'))
    return render_template('add_course.html')

@app.route('/edit_course/<int:course_id>', methods=['GET', 'POST'])
def edit_course(course_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        new_course_name = request.form['course_name']
        cursor.execute("UPDATE course SET course_name = %s WHERE course_id = %s", (new_course_name, course_id))
        conn.commit()
        conn.close()
        flash("Course updated successfully!")
        return redirect(url_for('course_management'))

    cursor.execute("SELECT * FROM course WHERE course_id = %s", (course_id,))
    course = cursor.fetchone()
    conn.close()
    return render_template('edit_course.html', course=course)

@app.route('/delete_course/<int:course_id>', methods=['POST'])
def delete_course(course_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM course WHERE course_id = %s", (course_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('course_management'))  # Redirect to the course management page after deletion


@app.route('/subject_management')
def subject_management():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Query to get all subjects from the database
    cursor.execute("SELECT subject_id, subject_name, subject_code FROM subject")
    subjects = cursor.fetchall()

    cursor.close()
    conn.close()

    # Render the subject management page and pass the subjects
    return render_template('subject_management.html', subjects=subjects)



@app.route('/delete_subject/<int:subject_id>', methods=['POST'])
def delete_subject(subject_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Delete the subject based on the provided subject_id
    cursor.execute("DELETE FROM subject WHERE subject_id = %s", (subject_id,))
    conn.commit()

    cursor.close()
    conn.close()

    flash('Subject deleted successfully!', 'success')
    return redirect(url_for('subject_management'))


@app.route('/add_subject', methods=['GET', 'POST'])
def add_subject():
    if request.method == 'POST':
        subject_name = request.form['subject_name']
        subject_code = request.form['subject_code']
        course_id = request.form['course_id']  # Add an input field for course selection if needed
        add_subject_to_db(subject_name, subject_code, course_id)
        flash('Subject added successfully!', 'success')
        return redirect(url_for('subject_management'))
    return render_template('add_subject.html', courses=get_all_courses())

@app.route('/edit_subject/<int:subject_id>', methods=['GET', 'POST'])
def edit_subject(subject_id):
    subject = get_subject_by_id(subject_id)
    if request.method == 'POST':
        print(request.form)  # Debugging: Check the form data
        updated_name = request.form['subject_name']
        updated_code = request.form['subject_code']
        course_id = request.form['course_id']  # Get the course ID from the form
        update_subject_in_db(subject_id, updated_name, updated_code, course_id)
        flash('Subject updated successfully!', 'success')
        return redirect(url_for('subject_management'))
    return render_template('edit_subject.html', subject=subject, courses=get_all_courses())

def add_subject_to_db(subject_name, subject_code, course_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO subject (subject_name, subject_code, course_id) VALUES (%s, %s, %s)",
                       (subject_name, subject_code, course_id))
        conn.commit()
    except Exception as e:
        print(f"Error adding subject: {str(e)}")
    finally:
        cursor.close()
        conn.close()

def get_subject_by_id(subject_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT subject_id, subject_name, subject_code, course_id FROM subject WHERE subject_id = %s", (subject_id,))
        subject = cursor.fetchone()
        return subject
    except Exception as e:
        print(f"Error fetching subject by ID: {str(e)}")
        return None
    finally:
        cursor.close()
        conn.close()


def update_subject_in_db(subject_id, updated_name, updated_code, course_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE subject
            SET subject_name = %s, subject_code = %s, course_id = %s
            WHERE subject_id = %s
        """, (updated_name, updated_code, course_id, subject_id))
        conn.commit()
        flash("Subject updated successfully!", "success")
    except Exception as e:
        flash(f"Error updating subject: {str(e)}", "danger")
    finally:
        cursor.close()  # Make sure to close the cursor
        conn.close()




def get_all_courses():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT course_id, course_name FROM course")
        courses = cursor.fetchall()
        return courses
    except Exception as e:
        print(f"Error fetching courses: {str(e)}")
        return []
    finally:
        cursor.close()
        conn.close()




# Take Exams Route (for students)
@app.route('/exam_management')
def exam_management():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM exam")
    exams = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('exam_management.html', exams=exams)




@app.route('/edit_exam/<int:exam_id>', methods=['GET', 'POST'])
def edit_exam(exam_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        exam_name = request.form['exam_name']
        subject_id = request.form['subject_id']
        teacher_id = request.form['teacher_id']
        total_marks = request.form['total_marks']
        exam_type = request.form['exam_type']

        cursor.execute("""
            UPDATE exam SET exam_name=%s, subject_id=%s, teacher_id=%s, total_marks=%s, exam_type=%s WHERE exam_id=%s
        """, (exam_name, subject_id, teacher_id, total_marks, exam_type, exam_id))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('exam_management'))

    cursor.execute("SELECT * FROM exam WHERE exam_id = %s", (exam_id,))
    exam = cursor.fetchone()
    cursor.execute("SELECT * FROM subject")
    subjects = cursor.fetchall()
    cursor.execute("SELECT * FROM teachers")
    teachers = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('edit_exam.html', exam=exam, subjects=subjects, teachers=teachers)


@app.route('/delete_exam/<int:exam_id>', methods=['POST'])
def delete_exam(exam_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM exam WHERE exam_id = %s", (exam_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('exam_management'))


@app.route('/add_notification', methods=['GET', 'POST'])
def add_notification():
    if request.method == 'POST':
        user_id = request.form['user_id']
        message = request.form['message']
        priority = request.form['priority']

        # Insert into notifications table
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO notification (user_id, message, priority) VALUES (%s, %s, %s)",
                           (user_id, message, priority))
            conn.commit()
            flash("Notification added successfully!", "success")
        except Exception as e:
            flash(f"Error adding notification: {str(e)}", "danger")
        finally:
            conn.close()
        return redirect(url_for('view_notification'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, name FROM user")
    users = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('add_notification.html', users=users)

@app.route('/view_notification', methods=['GET'])
def view_notification():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch all notifications along with usernames
    cursor.execute("""
        SELECT n.notification_id, u.name, n.message, n.priority 
        FROM notification n
        JOIN user u ON n.user_id = u.user_id
    """)
    notifications = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('view_notification.html', notifications=notifications)

@app.route('/view_course')
def view_course():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT course_id,course_name FROM Course")
    courses = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('view_course.html', courses=courses)

@app.route('/view_subjects')
def view_subjects():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT subject_id,subject_name FROM Subject")
    subjects = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('view_subject.html', subjects=subjects)

@app.route('/take_exams')
def take_exams():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT exam_id, exam_name, subject_id FROM Exam")
    exams = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('take_exam.html', exams=exams)

from flask import flash, redirect, url_for

@app.route('/start_exam/<int:exam_id>', methods=['GET', 'POST'])
def start_exam(exam_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT question_id, question_text FROM Question WHERE exam_id = %s", (exam_id,))
    questions = cursor.fetchall()

    if request.method == 'POST':
        responses = []
        for question in questions:
            answer = request.form.get(f"answer_{question[0]}")
            responses.append((exam_id, question[0], answer))

        for response in responses:
            cursor.execute("INSERT INTO Student_Responses (exam_id, question_id, answer) VALUES (%s, %s, %s)", response)
        conn.commit()

        cursor.close()
        conn.close()

        flash("Exam submitted successfully!", "success")  # Flash message here
        return redirect(url_for('take_exams'))  # Redirect to Take Exams

    cursor.close()
    conn.close()
    return render_template('start_exam.html', questions=questions)


@app.route('/submit_exam', methods=['POST'])
def submit_exam():
    student_id = session.get('user_id')  # Fetching student ID from session
    if not student_id:
        flash("Student not logged in!", "error")
        return redirect(url_for('login'))  # Redirect to login if not logged in

    exam_id = request.form.get('exam_id')
    question_id = request.form.get('question_id')
    answer = request.form.get('answer')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Student_Responses (student_id, exam_id, question_id, answer) VALUES (%s, %s, %s, %s)",
        (student_id, exam_id, question_id, answer)
    )
    conn.commit()
    cursor.close()
    conn.close()

    flash("Exam submitted successfully!", "success")  # Flash success message

    return redirect(url_for('take_exams'))  # Redirect to Take Exam page


@app.route('/results')
def view_results():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get the logged-in student ID
    student_id = session.get('student_id')
    print("Raw student_id from session:", student_id, type(student_id))



    query = """
        SELECT e.exam_name, e.total_marks, r.marks_obtained 
        FROM Exam e
        JOIN Results r ON e.exam_id = r.exam_id
        WHERE r.student_id = %s
    """

    cursor.execute(query, (student_id,))
    results = cursor.fetchall()
    print("Fetched results:", results)
    cursor.close()
    conn.close()

    return render_template('view_result.html', results=results)


@app.route('/feedback', methods=['POST', 'GET'])
def give_feedback():
    if request.method == 'POST':
        feedback_text = request.form['feedback_text']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Feedback (feedback_text) VALUES (%s)", (feedback_text,))
        conn.commit()
        cursor.close()
        conn.close()

        flash("Feedback submitted successfully!", "success")  # Flash success message
        return redirect(url_for('give_feedback'))  # Redirect back to feedback page

    return render_template('give_feedback.html')



@app.route('/student/notifications')
def view_student_notifications():
    user_id = session.get('user_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT message, priority 
        FROM Notification
        WHERE user_id = %s
    """, (user_id,))
    notifications = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('view_student_notification.html', notifications=notifications)


@app.route('/evaluate_exam/<int:exam_id>/<int:student_id>', methods=['GET', 'POST'])
def evaluate_exam(exam_id,student_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch submitted responses for the given exam
    cursor.execute("""
        SELECT sr.question_id, q.question_text, sr.answer
        FROM Student_Responses sr
        JOIN Question q ON sr.question_id = q.question_id
        WHERE sr.exam_id = %s AND sr.student_id = %s
    """, (exam_id, student_id))
    responses = cursor.fetchall()

    if request.method == 'POST':
        for response in responses:
            marks = request.form.get(f"marks_{response[0]}")
            cursor.execute("""UPDATE Student_Responses SET marks = %s WHERE question_id = %s AND exam_id = %s AND student_id = %s""", (marks, response[0], exam_id,student_id))
        conn.commit()
        cursor.close()
        conn.close()
        return "Marks assigned successfully!"

    cursor.close()
    conn.close()
    return render_template('evaluate_exam.html', responses=responses)


@app.route('/teacher/assigned_subjects/<int:teacher_id>')
def assigned_subjects(teacher_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch assigned subjects for the given teacher
    cursor.execute("""
        SELECT s.subject_id, s.subject_name 
        FROM Subject s
        JOIN teachers t ON s.subject_id = t.subject_id
        WHERE t.teacher_id = %s
    """, (teacher_id,))
    subjects = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('assigned_subjects.html', subjects=subjects)



@app.route('/teacher/question_paper_submission/<int:teacher_id>', methods=['GET', 'POST'])
def question_paper_submission(teacher_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch subjects assigned to the teacher
    cursor.execute("""
        SELECT s.subject_id, s.subject_name
        FROM subject s
        JOIN teachers t ON s.subject_id = t.subject_id
        WHERE t.teacher_id = %s
    """, (teacher_id,))
    subjects = cursor.fetchall()

    cursor.execute("""
            SELECT exam_id, exam_name
            FROM exam
            WHERE teacher_id = %s
        """, (teacher_id,))
    exams = cursor.fetchall()

    if request.method == 'POST':
        subject_id = request.form['subject_id']
        exam_id = request.form['exam_id']
        question_text = request.form['question_text']
        answer_text = request.form['answer_text']

        # Insert the question into the 'question' table
        cursor.execute("""
            INSERT INTO question (exam_id, question_text)
            VALUES (%s, %s)
        """, (exam_id, question_text, ))
        question_id = cursor.lastrowid  # Get the inserted question ID

        # Insert the answer into the 'answer' table
        cursor.execute("INSERT INTO answer (question_id, answer_text) VALUES (%s, %s)",
                       (question_id, answer_text))  # ✅ Correct

        conn.commit()
        flash("Question and Answer submitted successfully!", "success")

    cursor.close()
    conn.close()

    return render_template('question_paper_submission.html', subjects=subjects,exams=exams)



@app.route('/teacher/view_submissions/<int:teacher_id>', methods=['GET', 'POST'])
def view_submissions(teacher_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch subjects handled by the teacher
    cursor.execute("""
        SELECT s.subject_id, s.subject_name
        FROM subject s
        JOIN teachers t ON s.subject_id = t.subject_id
        WHERE t.teacher_id = %s
    """, (teacher_id,))
    subjects = cursor.fetchall()

    submissions = []
    selected_subject = None

    if request.method == 'POST':
        selected_subject = request.form['subject_id']

        # Fetch exam details for the selected subject
        cursor.execute("""
            SELECT exam_id, exam_name 
            FROM exam 
            WHERE subject_id = %s
        """, (selected_subject,))
        exams = cursor.fetchall()

        # Fetch submissions for the selected subject
        cursor.execute("""
            SELECT DISTINCT s.name, q.question_text, a.answer_text
            FROM answer a
            JOIN question q ON a.question_id = q.question_id
            JOIN exam e ON q.exam_id = e.exam_id
            JOIN student_exams se ON e.exam_id = se.exam_id
            JOIN student s ON se.student_id = s.student_id
            WHERE e.subject_id = %s
        """, (selected_subject,))

        submissions = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('view_submissions.html', subjects=subjects, submissions=submissions, selected_subject=selected_subject)


@app.route('/teacher/view_students/<int:teacher_id>', methods=['GET'])
def view_students(teacher_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch subjects handled by the teacher
    cursor.execute("""
        SELECT s.subject_id, s.subject_name
        FROM subject s
        JOIN teachers t ON s.subject_id = t.subject_id
        WHERE t.teacher_id = %s
    """, (teacher_id,))
    subjects = cursor.fetchall()

    students = []

    # Fetch students enrolled in the teacher's subjects
    cursor.execute("""
        SELECT st.name, st.email, st.phone_no
        FROM student st
        JOIN student_exams se ON st.student_id = se.student_id
        JOIN exam e ON se.exam_id = e.exam_id
        JOIN subject sb ON e.subject_id = sb.subject_id
        JOIN teachers t ON sb.subject_id = t.subject_id
        WHERE t.teacher_id = %s
    """, (teacher_id,))
    students = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('view_students.html', subjects=subjects, students=students)


@app.route('/update_result', methods=['GET', 'POST'])
def update_result():
    if 'teacher_id' not in session:
        return redirect(url_for('login'))  # Ensure only teachers can update

    conn = get_db_connection()
    cursor = conn.cursor()
    teacher_id = session['teacher_id']

    if request.method == 'POST':
        student_id = request.form['student_id']
        exam_id = request.form['exam_id']
        marks_obtained = request.form['marks_obtained']

        # Check if the result already exists
        cursor.execute(
            "SELECT * FROM Results WHERE student_id = %s AND exam_id = %s",
            (student_id, exam_id)
        )
        result = cursor.fetchone()

        if result:
            # Update existing result
            cursor.execute(
                "UPDATE Results SET marks_obtained = %s WHERE student_id = %s AND exam_id = %s",
                (marks_obtained, student_id, exam_id)
            )
        else:
            # Insert new result
            cursor.execute(
                "INSERT INTO Results (student_id, exam_id, marks_obtained) VALUES (%s, %s, %s)",
                (student_id, exam_id, marks_obtained)
            )

        conn.commit()
        flash("Result updated successfully!", "success")
        return redirect(url_for('update_result'))

    # **Fetch Assigned Subjects**
    cursor.execute("SELECT subject_id FROM Teachers WHERE teacher_id = %s", (teacher_id,))
    assigned_subjects = [row[0] for row in cursor.fetchall()]
    print("Assigned Subjects:", assigned_subjects)  # Debugging

    if not assigned_subjects:
        flash("No assigned subjects found!", "warning")
        return render_template('update_result.html', students=[], exams=[])

    # **Fetch Students Enrolled in Assigned Subjects**
    query = """
        SELECT DISTINCT s.student_id, s.name 
        FROM Student s
        JOIN Enrollment e ON s.student_id = e.student_id
        JOIN Subject sub ON e.course_id = sub.course_id  
        WHERE sub.subject_id IN ({})
    """.format(",".join(map(str, assigned_subjects)))

    cursor.execute(query)
    students = cursor.fetchall()
    print("Fetched Students:", students)  # Debugging
    # Debugging

    # **Fetch Exams Related to Assigned Subjects**
    query = """
        SELECT e.exam_id, e.exam_name
        FROM Exam e
        WHERE e.subject_id IN ({})
    """.format(",".join(map(str, assigned_subjects)))

    cursor.execute(query)
    exams = cursor.fetchall()
    print("Fetched Exams:", exams)  # Debugging

    cursor.close()
    conn.close()

    return render_template('update_result.html', students=students, exams=exams)


# Logout Route
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect(url_for('home'))




if __name__ == '__main__':
    app.run(debug=True)
