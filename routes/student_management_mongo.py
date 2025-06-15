from bson import ObjectId
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from db_connections import get_mongo_connection

student_management_mongo_bp = Blueprint("student_management_mongo", __name__)


@student_management_mongo_bp.route(
    "/select-course-mongo/<student_id>", methods=["GET", "POST"]
)
def select_course(student_id):
    db = get_mongo_connection()
    courses = db["courses"].find()

    db_mode = session.get("active_db_mode", "sql")

    if request.method == "POST":
        course_id = request.form["id"]
        student_id = request.form["student_id"]
        return redirect(
            url_for(
                "student_management_mongo.course_groups",
                course_id=course_id,
                student_id=student_id,
            )
        )

    return render_template(
        "select_course.html", courses=courses, student_id=student_id, db_mode=db_mode
    )


@student_management_mongo_bp.route(
    "/course-groups-mongo/<course_id>/<student_id>", methods=["GET", "POST"]
)
def course_groups(course_id, student_id):
    db = get_mongo_connection()
    course = db["courses"].find_one(
        {"_id": ObjectId(course_id)}, {"_id": 0, "student_group": 1, "title": 1}
    )
    groups = course["student_group"] if course else []
    title = course["title"]
    
    print(groups)
    joined_ids = []
    for group in groups:
        if "students" in group and student_id in group["students"]:
            joined_ids.append(group["student_group_id"])

    db_mode = session.get("active_db_mode", "sql")

    return render_template(
        "course_groups.html",
        groups=groups,
        title=title,
        student_id=student_id,
        course_id=course_id,
        db_mode=db_mode,
        joined_ids= joined_ids
    )


@student_management_mongo_bp.route("/join-group-mongo/", methods=["POST"])
def join_group():
    db = get_mongo_connection()

    course_id = request.form["course_id"]
    print(course_id)
    student_group_id = request.form["student_group_id"]
    student_id = request.form["student_id"]

    group_data_res = db["courses"].find_one(
        {"_id": ObjectId(course_id)},
        {
            "_id": 0,
            "student_group": {"$elemMatch": {"student_group_id": student_group_id}},
        },
    )

    group_data = group_data_res["student_group"][0]

    age_category = group_data["age_category"]
    max_participants = group_data["max_participants"]

    if max_participants <= len(group_data["students"]):
        flash("❌ Cannot join: group is full.")
        return redirect(
            url_for(
                "student_management_mongo.course_groups",
                course_id=course_id,
                student_id=student_id,
            )
        )
    student = db["students"].find_one({"student_id": student_id})
    student_age = student["age"]
    if not check_age(age_category, student_age):
        flash("❌ Cannot join: it is not you age category.")
        return redirect(
            url_for(
                "student_management_mongo.course_groups",
                course_id=course_id,
                student_id=student_id,
            )
        )

    db["courses"].update_one(
        {"_id": ObjectId(course_id), "student_group.student_group_id": student_group_id},
        {"$push": {"student_group.$.students": student_id}},
    )
    db["courses"].update_one(
        {"_id": ObjectId(course_id), "student_group.student_group_id": student_group_id},
        {"$inc": {"student_group.$.amount_of_participants": 1}},
    )

    return redirect(
        url_for(
            "student_management_mongo.course_groups",
            course_id=course_id,
            student_id=student_id,
        )
    )


def check_age(age_category, age):
    if age_category == "Adult":
        return age >= 18
    if age_category == "Teenager":
        return 11 < age < 18
    if age_category == "Kids":
        return age <= 11
