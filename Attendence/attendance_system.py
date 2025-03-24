import cv2
import os
import numpy as np
import datetime
import openpyxl
import tkinter as tk
from tkinter import messagebox
from deepface import DeepFace
from PIL import Image, ImageTk

# Define period hours
period_hours = [
    ("09:00:00", "09:50:00", "1st Hour"),
    ("09:50:00", "10:40:00", "2nd Hour"),
    ("10:50:00", "11:40:00", "3rd Hour"),
    ("11:40:00", "12:30:00", "4th Hour"),
    ("13:30:00", "14:20:00", "5th Hour"),
    ("14:20:00", "15:10:00", "6th Hour"),
    ("15:10:00", "16:00:00", "7th Hour")
]

# Load known faces
known_faces = []
face_dir = r"C:\Users\ASUS\PYTHON\Attendence\capture"

def load_known_faces():
    """Loads face encodings from the 'capture' directory using DeepFace."""
    global known_faces
    if not os.path.exists(face_dir):
        os.makedirs(face_dir)
    
    for filename in os.listdir(face_dir):
        if filename.endswith(".jpg") or filename.endswith(".png"):
            img_path = os.path.join(face_dir, filename)
            try:
                face_embedding = DeepFace.represent(img_path, model_name="Facenet", enforce_detection=True)[0]['embedding']
                known_faces.append((os.path.splitext(filename)[0], np.array(face_embedding)))
            except:
                print(f"Skipping {filename}: No face detected.")

load_known_faces()

def get_current_period():
    """Determine the current period based on system time."""
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
        messagebox.showinfo("Success", f"Attendance marked for {name} in {subject} during {period}")
    else:
        messagebox.showwarning("Warning", "Attendance not marked. Outside class hours.")

def capture_and_recognize():
    """Captures an image, detects a face, and recognizes it."""
    subject = subject_entry.get()
    if subject == "":
        messagebox.showerror("Error", "Please enter a subject name before capturing.")
        return

    cam = cv2.VideoCapture(0)
    ret, frame = cam.read()
    cam.release()

    if not ret:
        messagebox.showerror("Error", "Failed to capture image.")
        return

    temp_image_path = "temp.jpg"
    cv2.imwrite(temp_image_path, frame)

    try:
        result = DeepFace.find(img_path=temp_image_path, db_path=face_dir, model_name="Facenet", enforce_detection=True)
        if len(result) > 0 and len(result[0]) > 0:
            recognized_name = os.path.splitext(os.path.basename(result[0]['identity'][0]))[0]
            mark_attendance(recognized_name, subject)
        else:
            messagebox.showwarning("Face Not Recognized", "No matching student found. Register their photo first.")
    except Exception as e:
        messagebox.showerror("Error", f"Face recognition failed: {str(e)}")

# GUI using Tkinter with modern design
root = tk.Tk()
root.title("Automated Attendance System")
root.geometry("500x400")
root.configure(bg="#f4f4f4")

frame = tk.Frame(root, bg="#ffffff", padx=20, pady=20, relief=tk.RIDGE, bd=2)
frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

header_label = tk.Label(frame, text="Automated Attendance System", font=("Arial", 14, "bold"), bg="#ffffff")
header_label.pack(pady=10)

subject_label = tk.Label(frame, text="Enter Subject Name:", font=("Arial", 12), bg="#ffffff")
subject_label.pack(pady=5)

subject_entry = tk.Entry(frame, font=("Arial", 12), width=25, bd=2, relief=tk.GROOVE)
subject_entry.pack(pady=5)

capture_btn = tk.Button(frame, text="Capture Attendance", font=("Arial", 12, "bold"), bg="#28a745", fg="white", padx=10, pady=5, relief=tk.RAISED, command=capture_and_recognize)
capture_btn.pack(pady=20)

footer_label = tk.Label(root, text="© 2025 Attendance System", font=("Arial", 10), bg="#f4f4f4", fg="#555")
footer_label.pack(side=tk.BOTTOM, pady=10)

root.mainloop()
