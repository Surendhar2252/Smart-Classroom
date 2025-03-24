from flask import Flask, render_template, request, redirect, url_for, flash
import cv2
import os
import numpy as np
import datetime
import openpyxl
from deepface import DeepFace

app = Flask(__name__,static_folder='static') 
app.secret_key = 'your_secret_key'

# Define class periods
period_hours = [
    ("09:00:00", "09:50:00", "1st Hour"),
    ("09:50:00", "10:40:00", "2nd Hour"),
    ("10:50:00", "11:40:00", "3rd Hour"),
    ("11:40:00", "12:30:00", "4th Hour"),
    ("13:30:00", "14:20:00", "5th Hour"),
    ("14:20:00", "15:10:00", "6th Hour"),
    ("15:10:00", "16:00:00", "7th Hour"),
    ("21:00:00", "22:00:00", "8th Hour")
]

# Folder containing stored face images
face_dir = r"C:\Users\suren\Desktop\New folder\Attendence\capture"

# Dictionary to store known face embeddings
known_faces = {}

def load_known_faces():
    """Loads face embeddings from the 'capture' folder using DeepFace."""
    global known_faces
    known_faces.clear()

    if not os.path.exists(face_dir):
        os.makedirs(face_dir)

    for filename in os.listdir(face_dir):
        if filename.endswith(".jpg") or filename.endswith(".png"):
            img_path = os.path.join(face_dir, filename)
            try:
                face_embedding = DeepFace.represent(img_path, model_name="Facenet", enforce_detection=False)[0]['embedding']
                known_faces[os.path.splitext(filename)[0]] = np.array(face_embedding)
                print(f"✅ Loaded: {filename}")
            except Exception as e:
                print(f"⚠️ Skipping {filename}: No face detected. Error: {str(e)}")

# Load faces at startup
load_known_faces()

def get_current_period():
    """Determines the current period based on system time."""
    current_time = datetime.datetime.now().time()
    for start, end, period in period_hours:
        start_time = datetime.datetime.strptime(start, "%H:%M:%S").time()
        end_time = datetime.datetime.strptime(end, "%H:%M:%S").time()
        if start_time <= current_time <= end_time:
            return period
    return "Outside Class Hours"

def mark_attendance(name, subject):
    """Marks attendance in an Excel sheet."""
    file_name = "attendance.xlsx"

    if not os.path.exists(file_name):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["Date", "Time", "Period", "Subject", "Student Name", "Status"])
        wb.save(file_name)

    wb = openpyxl.load_workbook(file_name)
    ws = wb.active

    current_time = datetime.datetime.now().strftime("%H:%M:%S")
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    period = get_current_period()

    if period != "Outside Class Hours":
        ws.append([current_date, current_time, period, subject, name, "Present"])
        wb.save(file_name)
        flash(f"✅ Attendance marked for {name} in {subject} during {period}", "success")
    else:
        flash("⚠️ Attendance not marked. Outside class hours.", "warning")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/capture', methods=['POST'])
def capture_and_recognize():
    subject = request.form['subject']
    if not subject:
        flash("⚠️ Please enter a subject name before capturing.", "error")
        return redirect(url_for('index'))

    # Capture image from webcam
    cam = cv2.VideoCapture(0)
    ret, frame = cam.read()
    cam.release()

    if not ret:
        flash("⚠️ Failed to capture image.", "error")
        return redirect(url_for('index'))

    temp_image_path = "temp.jpg"
    cv2.imwrite(temp_image_path, frame)

    try:
        # Extract face embedding from captured image
        face_embedding = DeepFace.represent(temp_image_path, model_name="Facenet", enforce_detection=False)[0]['embedding']
        face_embedding = np.array(face_embedding)

        # Compare with stored face embeddings
        recognized_name = None
        min_distance = float('inf')

        for name, stored_embedding in known_faces.items():
            distance = np.linalg.norm(stored_embedding - face_embedding)
            if distance < 10:  # Adjust threshold as needed
                recognized_name = name
                min_distance = distance

        if recognized_name:
            mark_attendance(recognized_name, subject)
        else:
            flash("⚠️ No matching student found. Register their photo first.", "warning")

    except Exception as e:
        flash(f"⚠️ Face recognition failed: {str(e)}", "error")

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
