from flask import Flask, render_template, request, redirect, url_for
import pg8000
from datetime import datetime

app = Flask(__name__)
APP_NAME = "Collaborative Study Hub"

# Database Connection Details (Replace with your actual credentials)
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_HOST = "eldor-2t.ct6ei6agkus4.ap-south-1.rds.amazonaws.com"
DB_PORT = 5432
DB_NAME = "postgres"

# Database Table Names
RESOURCES_TABLE = "StudyResources"
QUESTIONS_TABLE = "CourseQuestions"
ANSWERS_TABLE = "QuestionAnswers"
USERS_TABLE = "StudyUsers"
VOTES_TABLE = "ResourceVotes"

def connect_db():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = pg8000.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME
        )
        return conn, conn.cursor()
    except pg8000.Error as e:
        print(f"Database connection error: {e}")
        return None, None

def close_db(conn, cur):
    """Closes the database connection and cursor."""
    if cur:
        cur.close()
    if conn:
        conn.close()

@app.route("/")
def index():
    """Homepage displaying available subjects/courses."""
    conn, cur = connect_db()
    if cur:
        cur.execute(f"SELECT DISTINCT course_name FROM {RESOURCES_TABLE} ORDER BY course_name;")
        courses = [row[0] for row in cur.fetchall()]
        close_db(conn, cur)
        return render_template("index.html", app_name=APP_NAME, courses=courses)
    else:
        return render_template("error.html", app_name=APP_NAME, message="Failed to connect to the database.")

@app.route("/course/<course_name>")
def course_dashboard(course_name):
    """Dashboard for a specific course, showing resources and questions."""
    conn, cur = connect_db()
    resources = []
    questions = []
    if cur:
        # Fetch resources for the course
        cur.execute(f"SELECT resource_id, title, file_url, uploaded_by, upload_date FROM {RESOURCES_TABLE} WHERE course_name = %s ORDER BY upload_date DESC;", (course_name,))
        resources_columns = [desc[0] for desc in cur.description]
        resources = [dict(zip(resources_columns, row)) for row in cur.fetchall()]

        # Fetch recent questions for the course
        cur.execute(f"SELECT question_id, title, asked_by, ask_date FROM {QUESTIONS_TABLE} WHERE course_name = %s ORDER BY ask_date DESC LIMIT 10;", (course_name,))
        questions_columns = [desc[0] for desc in cur.description]
        questions = [dict(zip(questions_columns, row)) for row in cur.fetchall()]

        close_db(conn, cur)
        return render_template("course_dashboard.html", app_name=APP_NAME, course_name=course_name, resources=resources, questions=questions)
    else:
        return render_template("error.html", app_name=APP_NAME, message="Failed to connect to the database.")
@app.route("/ask", methods=["POST"])
def submit_question():
    if request.method == "POST":
        course_name = request.form.get("course_name")
        title = request.form.get("question_title")
        content = request.form.get("question_content")
        asked_by = "test_user" # Replace with actual user authentication later
        ask_date = datetime.now()

        conn, cur = connect_db()
        if cur:
            cur.execute(f"INSERT INTO {QUESTIONS_TABLE} (course_name, title, content, asked_by, ask_date) VALUES (%s, %s, %s, %s, %s);",
                        (course_name, title, content, asked_by, ask_date))
            conn.commit()
            close_db(conn, cur)
            return redirect(url_for("all_questions")) # Redirect to the all questions page
        else:
            return render_template("error.html", app_name=APP_NAME, message="Failed to connect to the database.")
    # Should not reach here if the form is handled correctly
    return redirect(url_for("all_questions"))
@app.route("/profile")
def profile():
    # For now, we'll just render a basic profile page.
    # In the future, this is where you'd fetch user-specific data.
    return render_template("profile.html", app_name=APP_NAME)
@app.route("/information")
def information():
    return render_template("information.html", app_name=APP_NAME)
@app.route("/upload_resource/<course_name>", methods=["GET", "POST"])
def upload_resource(course_name):
    """Allows users to upload new learning resources."""
    if request.method == "POST":
        title = request.form.get("title")
        file_url = request.form.get("file_url") # In a real app, you'd handle file uploads differently
        uploaded_by = "test_user" # Replace with actual user authentication
        upload_date = datetime.now()

        conn, cur = connect_db()
        if cur:
            cur.execute(f"INSERT INTO {RESOURCES_TABLE} (course_name, title, file_url, uploaded_by, upload_date) VALUES (%s, %s, %s, %s, %s);",
                        (course_name, title, file_url, uploaded_by, upload_date))
            conn.commit()
            close_db(conn, cur)
            return redirect(url_for("course_dashboard", course_name=course_name))
        else:
            return render_template("error.html", app_name=APP_NAME, message="Failed to connect to the database.")
    return render_template("upload_resource.html", app_name=APP_NAME, course_name=course_name)

@app.route("/ask_question/<course_name>", methods=["GET", "POST"])
def ask_question(course_name):
    """Allows users to ask questions related to a course."""
    if request.method == "POST":
        title = request.form.get("question_title")
        content = request.form.get("question_content")
        asked_by = "test_user" # Replace with actual user authentication
        ask_date = datetime.now()

        conn, cur = connect_db()
        if cur:
            cur.execute(f"INSERT INTO {QUESTIONS_TABLE} (course_name, title, content, asked_by, ask_date) VALUES (%s, %s, %s, %s, %s);",
                        (course_name, title, content, asked_by, ask_date))
            conn.commit()
            close_db(conn, cur)
            return redirect(url_for("course_dashboard", course_name=course_name))
        else:
            return render_template("error.html", app_name=APP_NAME, message="Failed to connect to the database.")
    return render_template("ask_question.html", app_name=APP_NAME, course_name=course_name)
@app.context_processor
def inject_year():
    return {'year': datetime.now().year}

# You would add more routes for viewing resources, answering questions, voting, etc.

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
