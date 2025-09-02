import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

def preprocess_image(image_path: str, output_path: Optional[str] = None) -> str:
    """
    Preprocess image for better OCR results.
    
    Args:
        image_path: Path to input image
        output_path: Optional path to save processed image
        
    Returns:
        Path to processed image
    """
    try:
        # Load image
        img = cv2.imread(image_path)
        
        if img is None:
            raise ValueError(f"Could not load image from {image_path}")
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply denoising
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Apply adaptive thresholding for better text recognition
        binary = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Deskew image if needed
        deskewed = deskew_image(binary)
        
        # Enhance contrast
        enhanced = enhance_contrast(deskewed)
        
        # Save processed image
        if output_path is None:
            output_path = image_path.replace('.', '_processed.')
            
        cv2.imwrite(output_path, enhanced)
        logger.info(f"Image preprocessed and saved to {output_path}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"Error preprocessing image {image_path}: {e}")
        return image_path  # Return original path if processing fails

def deskew_image(image: np.ndarray) -> np.ndarray:
    """
    Deskew image to correct rotation.
    
    Args:
        image: Input image array
        
    Returns:
        Deskewed image array
    """
    try:
        # Find contours
        contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return image
        
        # Find largest contour (likely the page)
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Get minimum area rectangle
        rect = cv2.minAreaRect(largest_contour)
        angle = rect[2]
        
        # Correct angle
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
            
        # Only rotate if angle is significant
        if abs(angle) > 0.5:
            # Get rotation matrix
            (h, w) = image.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            
            # Perform rotation
            rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            return rotated
        
        return image
        
    except Exception as e:
        logger.error(f"Error deskewing image: {e}")
        return image

def enhance_contrast(image: np.ndarray) -> np.ndarray:
    """
    Enhance image contrast for better OCR.
    
    Args:
        image: Input image array
        
    Returns:
        Enhanced image array
    """
    try:
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(image)
        
        return enhanced
        
    except Exception as e:
        logger.error(f"Error enhancing contrast: {e}")
        return image

def resize_for_ocr(image_path: str, max_width: int = 2000, max_height: int = 2000) -> str:
    """
    Resize image to optimal size for OCR while maintaining aspect ratio.
    
    Args:
        image_path: Path to input image
        max_width: Maximum width
        max_height: Maximum height
        
    Returns:
        Path to resized image
    """
    try:
        with Image.open(image_path) as img:
            # Get current dimensions
            width, height = img.size
            
            # Calculate resize ratio
            ratio = min(max_width / width, max_height / height)
            
            # Only resize if image is too large
            if ratio < 1:
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                
                # Resize with high quality
                resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Save resized image
                output_path = image_path.replace('.', '_resized.')
                resized.save(output_path)
                
                logger.info(f"Image resized from {width}x{height} to {new_width}x{new_height}")
                return output_path
            
            return image_path
            
    except Exception as e:
        logger.error(f"Error resizing image {image_path}: {e}")
        return image_path

def validate_image(image_path: str) -> Tuple[bool, str]:
    """
    Validate image file and return status.
    
    Args:
        image_path: Path to image file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        with Image.open(image_path) as img:
            # Check if image can be opened
            img.verify()
            
            # Re-open for size check (verify() closes the image)
            with Image.open(image_path) as img:
                width, height = img.size
                
                # Check minimum dimensions
                if width < 100 or height < 100:
                    return False, "Image dimensions too small (minimum 100x100)"
                
                # Check maximum dimensions
                if width > 10000 or height > 10000:
                    return False, "Image dimensions too large (maximum 10000x10000)"
                
                # Check file format
                if img.format.lower() not in ['jpeg', 'jpg', 'png', 'bmp', 'tiff']:
                    return False, f"Unsupported image format: {img.format}"
                
                return True, ""
                
    except Exception as e:
        return False, f"Invalid image file: {str(e)}"

def extract_image_metadata(image_path: str) -> dict:
    """
    Extract metadata from image file.
    
    Args:
        image_path: Path to image file
        
    Returns:
        Dictionary with image metadata
    """
    try:
        with Image.open(image_path) as img:
            metadata = {
                'format': img.format,
                'mode': img.mode,
                'size': img.size,
                'width': img.size[0],
                'height': img.size[1],
            }
            
            # Add EXIF data if available
            if hasattr(img, '_getexif') and img._getexif():
                metadata['exif'] = img._getexif()
                
            return metadata
            
    except Exception as e:
        logger.error(f"Error extracting metadata from {image_path}: {e}")
        return {}