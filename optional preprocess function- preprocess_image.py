#Optional Pre Processing

def preprocess_image(image):
    """Preprocess the image to improve OCR results."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    adaptive_thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
    )
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
    cleaned = cv2.morphologyEx(adaptive_thresh, cv2.MORPH_CLOSE, kernel)
    sharpen_kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    final_image = cv2.filter2D(cleaned, -1, sharpen_kernel)

    # Save processed image for debugging
    cv2.imwrite("processed_image.jpg", final_image)
    print("Processed image saved as 'processed_image.jpg'")
    return final_image


 # Put this code in the beginning of extract name
 # """Extract the student's name from the exam paper image."""
 # if preprocess:
 #     image = preprocess_image(image)
 
 # put this code in preprocess image function after try
 # Preprocess the image if required
 # if preprocess:
 #     image = preprocess_image(image)