import cv2
import pyttsx3
import numpy as np
from collections import defaultdict
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
import pytesseract

# Initialize text-to-speech engine
engine = pyttsx3.init()

def text_to_speech(message):
    """Speak a message aloud."""
    engine.say(message)
    engine.runAndWait()

# Define pile ranges
PILES = {
    "A-E": ("A", "E"),
    "F-J": ("F", "J"),
    "K-O": ("K", "O"),
    "P-T": ("P", "T"),
    "U-Z": ("U", "Z"),
}

def determine_pile(last_name):
    """Determine which pile a student belongs to based on their last name."""
    first_letter = last_name[0].upper()
    for pile, (start, end) in PILES.items():
        if start <= first_letter <= end:
            return pile
    return None

def sort_pile(pile):
    """Sort the pile alphabetically by last name, then by first name."""
    return sorted(pile, key=lambda name: (name.split(" ")[1], name.split(" ")[0]))

def find_insert_position(pile, student_name):
    """Find the alphabetical position of the student in the pile."""
    for i, name in enumerate(pile):
        if student_name < name:
            return i, name
    return len(pile), None

def extract_name_from_exam(image):
    """
    Extract the name from the exam paper using OCR.
    Assumes the name is located in a fixed region on the exam paper.
    """
    # Preprocess the image (convert to grayscale)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Define the region of interest (ROI) where the name is expected
    # Adjust these coordinates to match where the name appears on the paper
    height, width = gray.shape
    roi = gray[int(height * 0.1):int(height * 0.2), int(width * 0.2):int(width * 0.8)]

    # Perform OCR on the ROI
    custom_config = r'--oem 3 --psm 6'  # OCR Engine and page segmentation mode
    extracted_text = pytesseract.image_to_string(roi, config=custom_config)

    # Clean up the extracted text to return the name
    # Assuming names follow "First Last" format
    name = extracted_text.strip().split("\n")[0]  # Take the first line as the name
    return name

def process_student_paper(image, piles):
    """Process a single student's paper, determine its pile, and provide sorting instruction."""
    try:
        student_name = extract_name_from_exam(image)
        if not student_name or len(student_name.split()) < 2:
            text_to_speech("Error: Unable to extract a valid name from the paper.")
            return

        last_name = student_name.split(" ")[1]
        pile_name = determine_pile(last_name)

        if pile_name is None:
            text_to_speech("Error: Unable to determine pile for the student.")
            return

        # Sort the relevant pile
        pile = piles[pile_name]
        pile = sort_pile(pile)

        # Determine insert position
        position, next_name = find_insert_position(pile, student_name)

        # Update the pile
        pile.insert(position, student_name)
        piles[pile_name] = pile

        # Voice command for sorting
        if next_name:
            message = f"Place {student_name}'s paper in the {pile_name} pile, after {next_name}."
        else:
            message = f"Place {student_name}'s paper as the first in the {pile_name} pile."

        text_to_speech(message)

    except Exception as e:
        text_to_speech(f"Error processing the paper: {e}")

# GUI for file selection and camera input
def select_file(piles):
    """Allow the user to select an image file and process it."""
    file_path = filedialog.askopenfilename(title="Select an image of the exam paper", filetypes=[("Image Files", "*.jpg;*.jpeg;*.png")])
    if not file_path:
        return

    try:
        image = cv2.imread(file_path)
        if image is None:
            raise ValueError("Invalid image file.")
        process_student_paper(image, piles)
        messagebox.showinfo("Success", "The paper has been processed successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to process the paper: {e}")

def use_camera(piles):
    """Capture an image using the computer's camera and process it."""
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        messagebox.showerror("Error", "Failed to access the camera.")
        return

    messagebox.showinfo("Instructions", "Press 's' to capture the image, or 'q' to quit.")

    while True:
        ret, frame = camera.read()
        if not ret:
            messagebox.showerror("Error", "Failed to capture image from the camera.")
            break

        cv2.imshow("Capture Exam Paper", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('s'):
            process_student_paper(frame, piles)
            messagebox.showinfo("Success", "The paper has been processed successfully.")
            break
        elif key == ord('q'):
            break

    camera.release()
    cv2.destroyAllWindows()

def view_virtual_piles(piles):
    """Display a virtual representation of the sorted piles."""
    window = tk.Toplevel()
    window.title("Virtual Representation of Piles")

    label = tk.Label(window, text="Sorted Representation of Papers", font=("Arial", 14))
    label.pack(pady=10)

    for pile_name, pile in piles.items():
        frame = tk.Frame(window)
        frame.pack(fill=tk.X, pady=5)

        pile_label = tk.Label(frame, text=pile_name, font=("Arial", 12), anchor="w")
        pile_label.pack(side=tk.LEFT, padx=10)

        if pile:
            pile_list = tk.Listbox(frame, height=5, width=50)
            for student in pile:
                pile_list.insert(tk.END, student)
            pile_list.pack(side=tk.RIGHT, padx=10)
        else:
            empty_label = tk.Label(frame, text="No papers in this pile", anchor="w")
            empty_label.pack(side=tk.RIGHT, padx=10)

# Main function to run the program with a GUI
def main():
    # Initialize piles as a dictionary of lists
    piles = defaultdict(list)

    # Create the GUI
    root = tk.Tk()
    root.title("Student Paper Sorting")

    label = tk.Label(root, text="Choose an option to process an exam paper.")
    label.pack(pady=10)

    file_button = tk.Button(root, text="Select File", command=lambda: select_file(piles))
    file_button.pack(pady=10)

    camera_button = tk.Button(root, text="Use Camera", command=lambda: use_camera(piles))
    camera_button.pack(pady=10)

    view_button = tk.Button(root, text="View Virtual Piles", command=lambda: view_virtual_piles(piles))
    view_button.pack(pady=10)

    exit_button = tk.Button(root, text="Exit", command=root.destroy)
    exit_button.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()
