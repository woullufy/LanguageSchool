# RUN pip install mysql-connector-python for docker
from db_connections import get_mysql_connection
from datetime import date
from mysql.connector import Error
from faker import Faker

# need to be installed in docker
from random import randint

def delete_data(conn):
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM group_membership")
        cursor.execute("DELETE FROM checked_assignments")
        cursor.execute("DELETE FROM assignment")
        cursor.execute("DELETE FROM student_group")
        cursor.execute("DELETE FROM course")
        cursor.execute("DELETE FROM student")
        cursor.execute("DELETE FROM tutor")
        cursor.execute("DELETE FROM mentor")
        cursor.execute("DELETE FROM employee")

        conn.commit()
        print("All data deleted from tables.")

    except Error as e:
        print(f"Error deleting data: {e}")

    finally:
        cursor.close()


def generate_data_tutor(x, faker):
    data = {}
    languages = ["English", "French", "German", "Spanish", "Chinese", "Russian",
                 "Italian", "Japanese", "Korean", "Arabic", "Turkish"]
    for i in range(0, x):
        data[i] = {}
        id = f"TU{str(i+1).zfill(4)}"
        data[i]["employee_id"] = id
        data[i]["tutor_id"] = id
        data[i]["first_name"] = faker.first_name()
        data[i]["last_name"] = faker.last_name()
        data[i]["language_speciality"] = faker.random_element(languages)
        data[i]["years_of_experience"] = randint(0, 40)
    return data


def get_language(conn, tutor_id):
    cursor = conn.cursor()

    query = "SELECT language_speciality FROM tutor WHERE tutor_id = %s"
    cursor.execute(query, (tutor_id,))
    result = cursor.fetchone()
    cursor.close()
    return result[0] if result else None


def generate_data_course(conn, x, faker, tutor_data):
    data = {}
    language_school_titles = [
        "Language through Film",
        "Literature & Discussion",
        "Music & Lyrics Lab",
        "Culture & Customs",
        "Travel Talk",
        "Storytelling Circle",
        "Idioms and Expressions",
        "Speaking Club",
        "Fluency Boost",
        "Debate & Discussion",
        "Talk with Confidence",
        "Express Yourself",
        "Conversation Practice",
        "Small Talk Strategies",
        "Language for the Workplace",
        "Email Writing Workshop",
        "Presentation Skills",
        "Negotiation Practice",
        "Interview Preparation",
        "Business Communication",
        "Academic Writing Skills",
        "Everyday Conversations",
        "Grammar Essentials",
        "Mastering Pronunciation",
        "Confident Writing",
        "Listening Lab",
        "Accent Reduction",
        "Real-Life Dialogues",
    ]
    language_level = ["A1", "A2", "B1", "B2", "C1", "C2"]
    tutor_ids = [tutor["tutor_id"] for tutor in tutor_data.values()]
    for i in range(0, x):
        data[i] = {}
        tutor_id = faker.random_element(tutor_ids)
        data[i]["course_id"] = f"CO{str(i+1).zfill(4)}"
        data[i]["language"] = get_language(conn, tutor_id)
        data[i]["title"] = faker.random_element(language_school_titles)
        data[i]["level"] = faker.random_element(language_level)
        data[i]["tutor"] = tutor_id
    return data


def generate_data_group(x, faker, course_data):
    course_ids = [course["course_id"] for course in course_data.values()]
    age_category = ["Adult", "Teenager", "Kids"]
    data = {}
    for i in range(0, x):
        data[i] = {}
        data[i]["student_group_id"] = f"GR{str(i+1).zfill(4)}"
        id_course = faker.random_element(course_ids)
        data[i]["course_id"] = id_course
        data[i]["age_category"] = faker.random_element(age_category)
        data[i]["amount_of_participants"] = 0
        data[i]["max_participants"] = faker.random_int(3, 10)
    return data


def generate_data_mentor(x, faker):
    data = {}
    for i in range(0, x):
        data[i] = {}
        id = f"ME{str(i+1).zfill(4)}"
        data[i]["employee_id"] = id
        data[i]["mentor_id"] = id
        data[i]["first_name"] = faker.first_name()
        data[i]["last_name"] = faker.last_name()
        data[i]["xp_level"] = faker.random_int(0, 100)
        data[i]["amount_of_students"] = "0"
    return data


def generate_data_student(conn, x, faker, generated_mentor):
    data = {}
    mentor_ids = [mentor["mentor_id"] for mentor in generated_mentor.values()]
    for i in range(0, x):
        data[i] = {}
        data[i]["student_id"] = f"ST{str(i+1).zfill(4)}"
        data[i]["first_name"] = faker.first_name()
        data[i]["last_name"] = faker.last_name()
        data[i]["email"] = faker.email()
        data[i]["age"] = randint(5, 60)
        id_mentor = faker.random_element(mentor_ids)
        data[i]["mentor"] = id_mentor
        add_student(conn, id_mentor)

    return data


def generate_data_assigment(x, faker, student_data):
    data = {}
    student_ids = [student["student_id"] for student in student_data.values()]

    start_issued = date(2025, 5, 1)
    end_issued = date(2025, 5, 31)
    start_due = date(2025, 6, 1)
    end_due = date(2025, 6, 30)

    for i in range(0, x):
        data[i] = {}
        data[i]["assignment_id"] = f"AS{str(i+1).zfill(4)}"
        data[i]["date_issued"] = faker.date_between(
            start_date=start_issued, end_date=end_issued
        )
        data[i]["date_due"] = faker.date_between(start_date=start_due, end_date=end_due)
        data[i]["from_student"] = faker.random_element(student_ids)

    return data


def add_student(conn, id_mentor):
    cursor = conn.cursor()

    query = "SELECT amount_of_students FROM mentor WHERE mentor_id = %s"
    cursor.execute(query, (id_mentor,))
    result = cursor.fetchone()

    if result:
        amount_of_students = int(result[0]) + 1
        query_add = "UPDATE mentor SET amount_of_students = %s WHERE mentor_id = %s"
        cursor.execute(query_add, (amount_of_students, id_mentor))
        conn.commit()

    cursor.close()


def insert_sample_data(conn, table_name, generated_data):
    cursor = conn.cursor()

    # get column names dynamically from the table schema
    cursor.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name = %s AND table_schema = 'language_school'",
        (table_name,),
    )
    schema = cursor.fetchall()
    columns = [column[0] for column in schema]
    columns_str = ", ".join(columns)
    placeholders = ", ".join(["%s"] * len(columns))
    query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
    temp = [record for record in generated_data.values() if record in columns]
    for record in generated_data.values():
        values = tuple(record.get(col) for col in columns)
        cursor.execute(query, values)

    conn.commit()
    cursor.close()
    print(f"Inserted {len(generated_data)} records into {table_name}.")

connection = get_mysql_connection()
delete_data(connection)
faker = Faker()
tutor_data = generate_data_tutor(5, faker)
# insert_data_tutor(connection, tutor_data)
insert_sample_data(connection, "employee", tutor_data)
insert_sample_data(connection, "tutor", tutor_data)

mentor_data = generate_data_mentor(8, faker)
insert_sample_data(connection, "employee", mentor_data)
insert_sample_data(connection, "mentor", mentor_data)

student_data = generate_data_student(connection, 20, faker, mentor_data)
insert_sample_data(connection, "student", student_data)

course_data = generate_data_course(connection, 10, faker, tutor_data)
insert_sample_data(connection, "course", course_data)

group_data = generate_data_group(20, faker, course_data)
insert_sample_data(connection, "student_group", group_data)

assigment_data = generate_data_assigment(70, faker, student_data)
insert_sample_data(connection, "assignment", assigment_data)
connection.close()
