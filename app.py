from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_secret_key')
APP_NAME = "Collaborative Study Hub"

# Configure database (replace with your actual URI)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@eldor-2t.ct6ei6agkus4.ap-south-1.rds.amazonaws.com:5432/postgres')
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)  # Ensure this is 256

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    resources = db.relationship('Resource', backref='course', lazy=True)
    questions = db.relationship('Question', backref='course', lazy=True)

class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    file_url = db.Column(db.String(500), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    uploaded_by = db.Column(db.String(80)) # Basic tracking, expand with user auth

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    ask_date = db.Column(db.DateTime, default=datetime.utcnow)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    asked_by = db.Column(db.String(80)) # Basic tracking

with app.app_context():
    db.create_all()

@app.route("/")
def index():
    courses = Course.query.all()
    return render_template("index.html", app_name=APP_NAME, courses=[course.name for course in courses])

@app.route("/course/<course_name>")
def course_dashboard(course_name):
    course = Course.query.filter_by(name=course_name).first_or_404()
    resources = Resource.query.filter_by(course_id=course.id).order_by(Resource.upload_date.desc()).all()
    questions = Question.query.filter_by(course_id=course.id).order_by(Question.ask_date.desc()).limit(10).all()
    return render_template("course_dashboard.html", app_name=APP_NAME, course_name=course_name, resources=resources, questions=questions)

@app.route("/ask", methods=["GET", "POST"])
def ask():
    if request.method == "POST":
        course_name = request.form.get("course_name")
        question_title = request.form.get("question_title")
        question_content = request.form.get("question_content")
        course = Course.query.filter_by(name=course_name).first()
        if course:
            new_question = Question(title=question_title, content=question_content, course_id=course.id, asked_by="Anonymous") # Add user info later
            db.session.add(new_question)
            db.session.commit()
            flash(f'Question submitted for {course_name}!', 'success')
            return redirect(url_for("course_dashboard", course_name=course_name))
        else:
            flash('Invalid course selected.', 'danger')
    courses = Course.query.all()
    return render_template("ask.html", app_name=APP_NAME, courses=[course.name for course in courses])

@app.route("/course/<course_name>/ask_question", methods=["GET", "POST"])
def ask_question(course_name):
    course = Course.query.filter_by(name=course_name).first_or_404()
    if request.method == "POST":
        title = request.form.get("question_title")
        content = request.form.get("question_content")
        new_question = Question(title=title, content=content, course_id=course.id, asked_by="Anonymous") # Add user info later
        db.session.add(new_question)
        db.session.commit()
        flash('Question submitted!', 'success')
        return redirect(url_for("course_dashboard", course_name=course_name))
    return render_template("ask_question.html", app_name=APP_NAME, course_name=course_name)

@app.route("/profile")
def profile():
    return render_template("profile.html", app_name=APP_NAME)

@app.route("/information")
def information():
    return render_template("information.html", app_name=APP_NAME)

@app.route("/upload_resource/<course_name>", methods=["GET", "POST"])
def upload_resource(course_name):
    course = Course.query.filter_by(name=course_name).first_or_404()
    if request.method == "POST":
        title = request.form.get("title")
        file_url = request.form.get("file_url") # In a real app, you'd handle file uploads differently
        new_resource = Resource(title=title, file_url=file_url, course_id=course.id, uploaded_by="Anonymous") # Add user info later
        db.session.add(new_resource)
        db.session.commit()
        flash('Resource uploaded successfully!', 'success')
        return redirect(url_for("course_dashboard", course_name=course_name))
    return render_template("upload_resource.html", app_name=APP_NAME, course_name=course_name)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'danger')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('Email address already registered!', 'danger')
            return render_template('register.html')

        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('profile')) # <--- ENSURE THIS LINE IS CORRECT

    return render_template('register.html', app_name=APP_NAME)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', app_name=APP_NAME, error="Page not found"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', app_name=APP_NAME, error="Internal server error"), 500

@app.context_processor
def inject_year():
    return {'year': datetime.now().year}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
