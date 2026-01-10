import os
from flask import Flask, request, session, redirect, render_template
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# APP SETUP 
app = Flask(__name__)
app.secret_key = "secret123"

# PATH FIX 
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")

if not os.path.exists(INSTANCE_DIR):
    os.makedirs(INSTANCE_DIR)

# DATABASE CONFIG 
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///" + os.path.join(INSTANCE_DIR, "users.db")
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# DATABASE MODELS 

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, nullable=False)
    issue_type = db.Column(db.String(100))
    description = db.Column(db.String(500))
    status = db.Column(db.String(50), default="Pending")

# HOME 
@app.route("/")
def home():
    return redirect("/student/login")

# STUDENT SIGNUP 
@app.route("/student/signup", methods=["GET", "POST"])
def student_signup():
    if request.method == "POST":
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        if Student.query.filter_by(email=email).first():
            return "Student already exists"

        student = Student(email=email, password=password)
        db.session.add(student)
        db.session.commit()
        return redirect("/student/login")

    return render_template("student_signup.html")

# STUDENT LOGIN 
@app.route("/student/login", methods=["GET", "POST"])
def student_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        student = Student.query.filter_by(email=email).first()
        if student and check_password_hash(student.password, password):
            session["role"] = "student"
            session["student_id"] = student.id
            return redirect("/student/dashboard")

        return "Invalid student credentials"

    return render_template("student_login.html")

# STUDENT DASHBOARD 
@app.route("/student/dashboard")
def student_dashboard():
    if session.get("role") != "student":
        return redirect("/student/login")

    complaints = Complaint.query.filter_by(
        student_id=session["student_id"]
    ).all()

    return render_template("dashboard.html", complaints=complaints)

# ADD COMPLAINT (STUDENT ONLY)
@app.route("/add_complaint", methods=["POST"])
def add_complaint():
    if session.get("role") != "student":
        return "Unauthorized", 403

    issue_type = request.form["issue_type"]
    description = request.form["description"]

    c = Complaint(
        student_id=session["student_id"],
        issue_type=issue_type,
        description=description
    )
    db.session.add(c)
    db.session.commit()

    return redirect("/student/dashboard")

# ADMIN LOGIN 
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password, password):
            session["role"] = "admin"
            session["admin_id"] = admin.id
            return redirect("/admin/dashboard")

        return "Invalid admin credentials"

    return render_template("admin_login.html")

# ADMIN DASHBOARD 
@app.route("/admin/dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect("/admin/login")

    complaints = Complaint.query.all()
    return render_template("admin_dashboard.html", complaints=complaints)

#UPDATE STATUS (ADMIN ONLY) 
@app.route("/update_status/<int:cid>")
def update_status(cid):
    if session.get("role") != "admin":
        return "Unauthorized", 403

    complaint = Complaint.query.get(cid)
    if complaint:
        complaint.status = "Resolved"
        db.session.commit()

    return redirect("/admin/dashboard")

# DELETE COMPLAINT (ADMIN ONLY) 
@app.route("/delete_complaint/<int:cid>")
def delete_complaint(cid):
    if session.get("role") != "admin":
        return "Unauthorized", 403

    complaint = Complaint.query.get(cid)
    if complaint:
        db.session.delete(complaint)
        db.session.commit()

    return redirect("/admin/dashboard")

# LOGOUT 
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

#  MAIN 
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        # default admin create (one-time)
        if not Admin.query.filter_by(username="admin").first():
            admin = Admin(
                username="admin",
                password=generate_password_hash("admin")
            )
            db.session.add(admin)
            db.session.commit()

    app.run(debug=True)
