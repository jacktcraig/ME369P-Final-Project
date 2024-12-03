import cv2
import pyttsx3
from collections import defaultdict
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import pytesseract
import numpy as np
import re

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
    return sorted(pile, key=lambda name: (name.split(" ")[1].upper(), name.split(" ")[0].upper()))

def find_insert_position(pile, student_name):
    """Find the alphabetical position of the student in the pile."""
    student_last_name = student_name.split(" ")[1].upper()
    student_first_name = student_name.split(" ")[0].upper()

    for i, name in enumerate(pile):
        pile_last_name = name.split(" ")[1].upper()
        pile_first_name = name.split(" ")[0].upper()

        if student_last_name < pile_last_name or (
            student_last_name == pile_last_name and student_first_name < pile_first_name
        ):
            return i, name

    return len(pile), None

def preprocess_image(image):
    """Preprocess the image to improve OCR results."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    adaptive_thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
    )
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
    cleaned = cv2.morphologyEx(adaptive_thresh, cv2.MORPH_CLOSE, kernel)
    sharpen_kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    return cv2.filter2D(cleaned, -1, sharpen_kernel)

def extract_name(image, preprocess=False):
    """Extract the student's name from the exam paper image."""
    if preprocess:
        image = preprocess_image(image)

    text = pytesseract.image_to_string(image, lang="eng", config="--psm 6")
    print("OCR Output:\n", text)  # Debugging

    for line in text.split("\n"):
        if "Name" in line or "name" in line:  # Handle case insensitivity
            # Normalize line
            line = line.replace("name", "Name").strip()
            # Regex to capture names, allowing for extra characters like [ or (
            match = re.search(r"Name\s*[:\-]*\s*[\[\(]*\s*([A-Za-z]+\s[A-Za-z]+)", line)
            if match:
                name = match.group(1).strip()
                return name

    return "Unknown Name"

def process_student_paper(image, piles, preprocess=False):
    """Process a single student's paper, determine its pile, and provide sorting instruction."""
    try:
        # Preprocess the image if required
        if preprocess:
            image = preprocess_image(image)

        student_name = extract_name(image)
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
        position, next_name = find_insert_position(pile, student_name)

        # Update the pile
        pile.insert(position, student_name)
        piles[pile_name] = pile

        # Voice command for sorting
        if position == 0:
            message = f"Place {student_name}'s paper as the first in the {pile_name} pile."
        elif next_name:
            message = f"Place {student_name}'s paper in the {pile_name} pile, before {next_name}."
        else:
            message = f"Place {student_name}'s paper at the end of the {pile_name} pile."

        text_to_speech(message)

    except Exception as e:
        text_to_speech(f"Error processing the paper: {e}")


def select_file(piles):
    """Allow the user to select an image file and process it."""
    file_path = filedialog.askopenfilename(
        title="Select an image of the exam paper", filetypes=[("Image Files", "*.jpg;*.jpeg;*.png")]
    )
    if not file_path:
        return

    try:
        image = cv2.imread(file_path)
        if image is None:
            raise ValueError("Invalid image file.")
        process_student_paper(image, piles, preprocess=False)
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

        # Show the captured frame
        cv2.imshow("Capture Exam Paper", frame)

        # Wait for user input
        key = cv2.waitKey(1) & 0xFF
        if key == ord('s'):  # Save and process the captured frame
            process_student_paper(frame, piles, preprocess=True)
            messagebox.showinfo("Success", "The paper has been processed successfully.")
            break
        elif key == ord('q'):  # Exit without processing
            break

    # Release resources
    camera.release()
    cv2.destroyAllWindows()


    messagebox.showinfo("Instructions", "Press 's' to capture the image, or 'q' to quit.")

    while True:
        ret, frame = camera.read()
        if not ret:
            messagebox.showerror("Error", "Failed to capture image from the camera.")
            break

        cv2.imshow("Capture Exam Paper", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('s'):  # Save image when 's' is pressed
            process_student_paper(frame, piles, preprocess=True)
            messagebox.showinfo("Success", "The paper has been processed successfully.")
            break
        elif key == ord('q'):  # Quit when 'q' is pressed
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
