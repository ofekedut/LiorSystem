import cv2
import pytesseract
from PIL import Image
from pathlib import Path
import numpy as np

def preprocess_image(image_path: Path) -> Image.Image:
    """
    Preprocess the image to enhance OCR accuracy.

    Args:
        image_path (Path): Path to the image file.

    Returns:
        Image.Image: The preprocessed image.
    """
    try:
        # Read the image using OpenCV
        img = cv2.imread(str(image_path))

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Apply Otsu's thresholding to binarize the image
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Invert the image if text is white on black background
        if np.mean(binary) > 127:
            binary = cv2.bitwise_not(binary)

        # Convert the processed image back to PIL format
        preprocessed_img = Image.fromarray(binary)

        return preprocessed_img

    except Exception as e:
        print(f"Error preprocessing image: {e}")
        return None

def extract_hebrew_text(image_path: str) -> str:
    """
    Extract Hebrew text from an image using Tesseract OCR.

    Args:
        image_path (str): Path to the image file.

    Returns:
        str: Extracted Hebrew text.
    """
    try:
        # Convert to Path object
        # image_path = Path(image_path)

        # Check if file exists
        # if not image_path.is_file():
        #     raise FileNotFoundError(f"Image file not found: {image_path}")
        #
        # # Preprocess the image
        # img = preprocess_image(image_path)
        # if img is None:
        #     return ""

        # Specify the path to the Tesseract executable if necessary
        # pytesseract.pytesseract.tesseract_cmd = r'/path/to/tesseract'

        # Extract text using Tesseract with Hebrew language support
        custom_config = r'--oem 3 --psm 6 -l heb'
        text = pytesseract.image_to_string(cv2.imread(image_path), config=custom_config)

        return text.strip()

    except Exception as e:
        print(f"Error extracting text: {e}")
        return ""

if __name__ == "__main__":
    # Path to your image file
    image_path = '/test_extraction_service/test_files/כרטיס ת.ז חדש.png'

    # Extract text from the image
    extracted_text = extract_hebrew_text(image_path)

    if extracted_text:
        print("Extracted Text:")
        print("-" * 40)
        print(extracted_text)
    else:
        print("No text could be extracted from the image.")
