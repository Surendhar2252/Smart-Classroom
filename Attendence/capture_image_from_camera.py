import cv2
import os
from matplotlib import pyplot as plt

# Define the folder path where images will be saved
folder_path = r"C:\Users\suren\Desktop\New folder\Attendence\capture"

# Create the folder if it doesn't exist 
if not os.path.exists(folder_path):
    os.makedirs(folder_path)

cam_port = 0
cam = cv2.VideoCapture(cam_port)

# Reading the input using the camera
inp = input('Enter person name: ')

while True:
    result, image = cam.read()
    if result:
        # Display the image
        plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        plt.title(inp)
        plt.show()

        # Ask the user if they want to save the image
        save = input("Do you want to save the image? (y/n): ")
        if save.lower() == 'y':
            file_path = os.path.join(folder_path, inp + ".png")
            cv2.imwrite(file_path, image)
            print("Image saved as", file_path)
            break
        else:
            print("Image not saved. Retaking image.")
    else:
        print("No image detected. Please try again.")

# Release the camera
cam.release()
