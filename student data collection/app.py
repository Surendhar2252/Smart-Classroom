from flask import Flask, render_template, request, redirect, url_for
import os
import mysql.connector
import matplotlib.pyplot as plt
import datetime

app = Flask(__name__)
UPLOAD_FOLDER = 'static/images/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Database Connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",  # Replace with your MySQL password
        database="performance"
    )

# Initialize Database
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create Students Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS students (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(100),
                        roll_number VARCHAR(50),
                        department VARCHAR(100),
                        image VARCHAR(255))
                    ''')

    # Create Grades Table (Ensure SGPA & CGPA columns exist)
    cursor.execute('''CREATE TABLE IF NOT EXISTS grades (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        student_id INT,
                        semester INT CHECK (semester BETWEEN 1 AND 8),
                        sgpa FLOAT,
                        cgpa FLOAT DEFAULT NULL,
                        FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE)
                    ''')

    conn.commit()
    cursor.close()
    conn.close()

init_db()

# Home Route
@app.route('/')
def home():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get latest student
    cursor.execute("SELECT * FROM students ORDER BY id DESC LIMIT 1")
    student = cursor.fetchone()

    graph_path = None
    semester_data = []

    if student:
        student_id = student["id"]
        
        # Fetch all semesters' SGPA and CGPA
        cursor.execute("SELECT semester, sgpa, cgpa FROM grades WHERE student_id = %s ORDER BY semester", (student_id,))
        grades = cursor.fetchall()

        if grades:
            semesters = [g["semester"] for g in grades]
            sgpas = [g["sgpa"] for g in grades]
            cgpas = [g["cgpa"] for g in grades]

            # Generate Performance Graph
            plt.figure(figsize=(6, 4))
            plt.plot(semesters, sgpas, marker='o', linestyle='-', color='b', label="SGPA")
            plt.plot(semesters, cgpas, marker='s', linestyle='-', color='g', label="CGPA")
            plt.xlabel('Semester')
            plt.ylabel('Score')
            plt.title('Semester-wise Performance')
            plt.legend()
            plt.grid()

            graph_path = os.path.join(app.config['UPLOAD_FOLDER'], 'performance_graph.png')
            plt.savefig(graph_path)
            plt.close()

            semester_data = grades

    cursor.close()
    conn.close()
    return render_template('index.html', student=student, graph_path=graph_path, semesters=semester_data)

# Upload Student Details
@app.route('/upload', methods=['POST'])
def upload():
    name = request.form['name']
    roll_number = request.form['roll_number']
    department = request.form['department']
    image = request.files['image']

    # Generate unique filename for image
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{timestamp}_{image.filename}"
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    image.save(image_path)

    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert Student Data
    cursor.execute("INSERT INTO students (name, roll_number, department, image) VALUES (%s, %s, %s, %s)",
                   (name, roll_number, department, filename))
    student_id = cursor.lastrowid

    # Insert SGPA & CGPA for each semester
    for semester in range(1, 9):
        sgpa = float(request.form.get(f'sgpa_sem{semester}', 0))
        cgpa = float(request.form.get(f'cgpa_sem{semester}', 0))
        cursor.execute("INSERT INTO grades (student_id, semester, sgpa, cgpa) VALUES (%s, %s, %s, %s)",
                       (student_id, semester, sgpa, cgpa))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
