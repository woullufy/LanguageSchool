from flask import Flask
from routes.main import main_bp
from routes.reports import reports_bp
from routes.assignments import assignments_bp
from routes.student_management import student_management_bp
from routes.student_management_mongo import student_management_mongo_bp

app = Flask(__name__)
app.secret_key = "supersecretkey123"
app.config['SECRET_KEY'] = 'a_very_long_and_random_secret_key_for_security' 

app.register_blueprint(main_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(assignments_bp)
app.register_blueprint(student_management_bp)
app.register_blueprint(student_management_mongo_bp)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
