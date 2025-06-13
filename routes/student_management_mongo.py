from flask import Blueprint, render_template, request, redirect, url_for, flash
from db_connections import get_mongo_connection

student_management_mongo_bp = Blueprint("student_management_mongo", __name__)


@student_management_mongo_bp.route("/select-student-mongo", methods=["GET", "POST"])
def select_student():
    db = get_mongo_connection()
    student_collection = db["students"]
    students = student_collection.find({}, {"student_id": 1, "first_name": 1, "last_name": 1, "_id": 0})

    if request.method == "POST":
        student_id = request.form["student_id"]
        return redirect(url_for("student_management_mongo.select_course", student_id=student_id))

    return render_template("select_student.html", students=students)


@student_management_mongo_bp.route("/select-course-mongo/<student_id>", methods=["GET", "POST"])
def select_course(student_id):
    db = get_mongo_connection()
    courses = db["courses"].find()

    if request.method == "POST":
        course_id = request.form["course_id"]
        student_id = request.form["student_id"]
        return redirect(
            url_for("student_management_mongo.course_groups", course_id=course_id, student_id=student_id)
        )

    return render_template("select_course_mongo.html", courses=courses, student_id=student_id)


@student_management_mongo_bp.route("/course-groups-mongo/<course_id>/<student_id>", methods=["GET", "POST"])
def course_groups(course_id, student_id):
    db = get_mongo_connection()
    course = db["courses"].find_one({"course_id": course_id}, {"_id": 0, "student_group": 1, "title": 1})
    groups = course["student_group"] if course else []
    title = course["title"]

    return render_template(
        "course_groups_mongo.html",
        groups=groups,
        title=title,
        student_id=student_id,
        course_id=course_id
    )


@student_management_mongo_bp.route("/join-group-mongo/", methods=["POST"])
def join_group():
    db = get_mongo_connection()

    course_id = request.form["course_id"]
    print(course_id)
    student_group_id = request.form["student_group_id"]
    student_id = request.form["student_id"]

    group_data_res = db["courses"].find_one(
        {"course_id": course_id},
        {"_id": 0, "student_group": {
            "$elemMatch": {"student_group_id": student_group_id}
        }})

    group_data = group_data_res["student_group"][0]

    age_category = group_data["age_category"]
    max_participant = group_data["max_participant"]

    if max_participant <= len(group_data["students"]):
        flash("❌ Cannot join: group is full.")
        return redirect(
            url_for("student_management_mongo.course_groups", course_id=course_id, student_id=student_id)
        )
    student = db["students"].find_one({"student_id": student_id})
    student_age = student["age"]
    if not check_age(age_category, student_age):
        flash("❌ Cannot join: it is not you age category.")
        return redirect(
            url_for("student_management_mongo.course_groups", course_id=course_id, student_id=student_id)
        )

    db["courses"].update_one(
        {"course_id": course_id, "student_group.student_group_id": student_group_id},
        {"$push": {"student_group.$.students": student_id}}
    )
    db["courses"].update_one(
        {"course_id": course_id, "student_group.student_group_id": student_group_id},
        {"$inc": {"student_group.$.amount_of_participants": 1}}
    )

    return redirect(
        url_for("student_management_mongo.course_groups", course_id=course_id, student_id=student_id)
    )


def check_age(age_category, age):
    if age_category == "Adult":
        return age >= 18
    if age_category == "Teenager":
        return 11 < age < 18
    if age_category == "Kids":
        return age <= 11
