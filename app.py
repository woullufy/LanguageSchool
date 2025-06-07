from flask import Flask, render_template, request, redirect # need to be installed in docker!
import mysql.connector
import uuid
import subprocess
import traceback

app = Flask(__name__)

def get_connection():
    return mysql.connector.connect(
        host="mariadb",                 # <- service name from docker-compose
        user="root",
        password="rootpass",
        database="language_school"
    )

@app.route('/generate-data')
def generate_data():
    try:
        # Run data_generator.py using subprocess
        subprocess.run(['python', 'data_generator.py'], check=True)
        return redirect('/tables')
    except subprocess.CalledProcessError as e:
        print("Subprocess error: ", e)
        traceback.print_exc()
        return "Error generating data", 500
    
@app.route('/tables')
def show_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # Get all table names
    cursor.execute("SHOW TABLES")
    tables = [row[0] for row in cursor.fetchall()]

    # Fetch rows for each table
    data = {}
    for table in tables:
        cursor.execute(f"SELECT * FROM {table}")
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        data[table] = {'columns': columns, 'rows': rows}

    cursor.close()
    conn.close()
    return render_template('tables.html', data=data)

@app.route('/select-course')
def select_course():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM course")
    courses = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('select_course.html', courses=courses)

@app.route('/course-groups/<course_id>')
def course_groups(course_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM student_group WHERE course_id = %s", (course_id,))
    groups = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('course_groups.html', groups=groups)


@app.route('/')
def index():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM student")
    students = cursor.fetchall()

    cursor.execute("SELECT mentor_id FROM mentor")
    mentors = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('students.html', students=students, mentors=mentors)



@app.route('/add', methods=['POST'])
def add_student():
    student_id = str(uuid.uuid4())
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    email = request.form['email']
    age = int(request.form['age'])
    mentor_id = request.form.get('mentor') or None


    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO student (student_id, first_name, last_name, email, age, mentor) VALUES (%s, %s, %s, %s, %s, %s)",
        (student_id, first_name, last_name, email, age, mentor_id)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/')



if __name__ == '__main__':
    app.run(host='0.0.0.0', port= 5000, debug=True)
