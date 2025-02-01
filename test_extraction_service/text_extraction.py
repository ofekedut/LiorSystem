import io
import json
import logging
import os
import pathlib
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import statistics
import gc
import re

import cv2
import numpy as np
import pytesseract
from pytesseract import Output
from pdf2image import convert_from_bytes
from PIL import Image, ImageOps, ImageEnhance


# Configure logging
def setup_logging(level=logging.ERROR):
    """Configure logging with a consistent format"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)


logger = setup_logging()


class OCRConfig:
    """Central configuration for OCR processing"""
    DEFAULT_PSM_MODES = [1, 3, 6, 12]
    DEFAULT_LANGUAGE = "heb"
    MIN_CONFIDENCE_THRESHOLD = 30.0
    MAX_IMAGE_DIMENSION = 4000
    BATCH_SIZE = 5

    # Preprocessing configurations
    CONTRAST_ENHANCEMENT_CAP = 3.0
    BASE_WIDTH = 1000
    DESKEW_ANGLE_THRESHOLD = 0.5

    # Quality assessment weights
    CONFIDENCE_WEIGHT = 0.6
    ERROR_WEIGHT = 0.2
    LENGTH_WEIGHT = 0.2

    @staticmethod
    def validate_psm_modes(modes: List[int]) -> List[int]:
        """Validate and filter PSM modes"""
        valid_modes = set(range(0, 14))
        return [m for m in modes if m in valid_modes]


@dataclass
class OCRResult:
    """Data class for OCR results"""
    text: str
    confidence: float
    psm: int
    preprocessing_info: Dict
    processing_time: float
    page_number: Optional[int] = None


class ImagePreprocessor:
    """Handles all image preprocessing operations"""

    @staticmethod
    def preprocess_image(
            image: Image.Image,
            config: OCRConfig = OCRConfig()
    ) -> Tuple[Image.Image, Dict]:
        """Enhanced preprocessing pipeline with detailed tracking"""
        start_time = time.time()
        preprocessing_info = {}

        logger.debug("Starting image preprocessing pipeline")

        try:
            # Convert to grayscale
            image = ImageOps.grayscale(image)
            logger.debug("Converted image to grayscale")

            # Dynamic contrast enhancement
            image, contrast_info = ImagePreprocessor._enhance_contrast_dynamic(image)
            preprocessing_info.update(contrast_info)

            # Resize image
            image, resize_info = ImagePreprocessor._resize_image(image)
            preprocessing_info.update(resize_info)

            # Apply adaptive thresholding
            image = ImagePreprocessor._adaptive_threshold(image)
            logger.debug("Applied adaptive thresholding")

            # Remove noise
            image, noise_info = ImagePreprocessor._remove_noise_adaptive(image)
            preprocessing_info.update(noise_info)

            # Deskew if needed
            image, deskew_info = ImagePreprocessor._deskew_optimized(
                image,
                angle_threshold=config.DESKEW_ANGLE_THRESHOLD
            )
            preprocessing_info.update(deskew_info)

            # Equalize histogram
            image = ImagePreprocessor._equalize_histogram(image)
            logger.debug("Applied histogram equalization")

            preprocessing_info['total_time'] = time.time() - start_time
            logger.info(f"Preprocessing completed in {preprocessing_info['total_time']:.2f} seconds")

            return image, preprocessing_info

        except Exception as e:
            logger.error(f"Preprocessing failed: {str(e)}")
            raise

    @staticmethod
    def _enhance_contrast_dynamic(image: Image.Image) -> Tuple[Image.Image, Dict]:
        """Dynamically enhance contrast based on image statistics"""
        img_array = np.array(image)
        p2, p98 = np.percentile(img_array, (2, 98))

        if p98 - p2 > 0:
            factor = min(255.0 / (p98 - p2), OCRConfig.CONTRAST_ENHANCEMENT_CAP)
            enhanced = ImageEnhance.Contrast(image).enhance(factor)
            return enhanced, {'contrast_factor': factor}
        return image, {'contrast_factor': 1.0}

    @staticmethod
    def _resize_image(
            image: Image.Image,
            base_width: int = OCRConfig.BASE_WIDTH
    ) -> Tuple[Image.Image, Dict]:
        """Resize image while maintaining aspect ratio"""
        original_size = image.size
        w_percent = base_width / float(original_size[0])
        h_size = int(float(original_size[1]) * w_percent)

        resized = image.resize((base_width, h_size), Image.Resampling.LANCZOS)
        return resized, {
            'original_size': original_size,
            'new_size': (base_width, h_size),
            'scale_factor': w_percent
        }

    @staticmethod
    def _adaptive_threshold(image: Image.Image) -> Image.Image:
        """Apply adaptive thresholding with optimal parameters"""
        cv_image = np.array(image)

        # Calculate optimal block size based on image size
        block_size = min(11, max(3, int(min(image.size) / 100) * 2 + 1))

        thresh = cv2.adaptiveThreshold(
            cv_image, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            block_size, 2
        )
        return Image.fromarray(thresh)

    @staticmethod
    def _remove_noise_adaptive(image: Image.Image) -> Tuple[Image.Image, Dict]:
        """Remove noise with adaptive kernel size"""
        img_array = np.array(image)
        noise_estimate = np.std(img_array)
        kernel_size = max(3, min(7, int(noise_estimate / 10)))

        denoised = cv2.fastNlMeansDenoising(
            img_array,
            None,
            h=10,
            templateWindowSize=kernel_size,
            searchWindowSize=kernel_size * 3
        )

        return Image.fromarray(denoised), {
            'noise_level': noise_estimate,
            'kernel_size': kernel_size
        }

    @staticmethod
    def _deskew_optimized(
            image: Image.Image,
            angle_threshold: float
    ) -> Tuple[Image.Image, Dict]:
        """Optimized deskew operation with angle threshold"""
        cv_image = np.array(image)
        coords = np.column_stack(np.where(cv_image > 0))

        if coords.size == 0:
            return image, {'deskewed': False, 'angle': 0.0}

        angle = cv2.minAreaRect(coords)[-1]

        if abs(angle) < angle_threshold:
            return image, {'deskewed': False, 'angle': angle}

        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle

        (h, w) = cv_image.shape[:2]
        center = (w // 2, h // 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        deskewed = cv2.warpAffine(
            cv_image,
            matrix,
            (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )

        return Image.fromarray(deskewed), {
            'deskewed': True,
            'angle': angle
        }

    @staticmethod
    def _equalize_histogram(image: Image.Image) -> Image.Image:
        """Apply histogram equalization with edge preservation"""
        cv_image = np.array(image)
        equalized = cv2.equalizeHist(cv_image)
        return Image.fromarray(equalized)


class OCRProcessor:
    """Handles OCR operations with quality assessment"""

    def __init__(self, config: OCRConfig = OCRConfig()):
        self.config = config
        self._verify_tesseract()

    def _verify_tesseract(self):
        """Verify Tesseract installation and language data"""
        try:
            pytesseract.get_tesseract_version()
            logger.info(f"Tesseract version: {pytesseract.get_tesseract_version()}")
        except Exception as e:
            logger.error(f"Tesseract verification failed: {str(e)}")
            raise RuntimeError("Tesseract is not properly installed")

    def process_image(
            self,
            image: Image.Image,
            preprocess_passes: int = 2,
            psm: int = 3,
            language: str = OCRConfig.DEFAULT_LANGUAGE
    ) -> OCRResult:
        """Process single image with OCR"""
        start_time = time.time()
        logger.info(f"Starting OCR processing with PSM {psm}")

        try:
            processed_img = image.copy()
            preprocessing_info = {}

            # Apply preprocessing
            for i in range(preprocess_passes):
                processed_img, prep_info = ImagePreprocessor.preprocess_image(
                    processed_img,
                    self.config
                )
                preprocessing_info[f'pass_{i + 1}'] = prep_info

            # Perform OCR
            config = f"--oem 3 --psm {psm} -l {language}"
            ocr_data = pytesseract.image_to_data(
                processed_img,
                config=config,
                output_type=Output.DICT
            )

            # Process results
            text_segments = []
            confidences = []

            for i, (word, conf) in enumerate(zip(ocr_data["text"], ocr_data["conf"])):
                if word.strip() and conf != "-1":
                    text_segments.append(word)
                    confidences.append(float(conf))

            # Calculate confidence and create result
            avg_conf = statistics.mean(confidences) if confidences else 0.0
            text = " ".join(text_segments)

            processing_time = time.time() - start_time
            logger.info(f"OCR completed in {processing_time:.2f} seconds with confidence {avg_conf:.2f}")

            return OCRResult(
                text=text.strip(),
                confidence=avg_conf,
                psm=psm,
                preprocessing_info=preprocessing_info,
                processing_time=processing_time
            )

        except Exception as e:
            logger.error(f"OCR processing failed: {str(e)}")
            raise


class DocumentProcessor:
    """Main class for document processing"""

    def __init__(self, config: OCRConfig = OCRConfig()):
        self.config = config
        self.ocr_processor = OCRProcessor(config)

    def process_document(
            self,
            image_bytes: bytes,
            filename: str,
            preprocess_passes: int = 2,
            psm_modes: Optional[List[int]] = None,
            language: str = OCRConfig.DEFAULT_LANGUAGE
    ) -> Dict:
        """Process document with multiple strategies"""
        logger.info(f"Starting document processing for {filename}")
        start_time = time.time()

        try:
            # Validate PSM modes
            psm_modes = self.config.validate_psm_modes(
                psm_modes or self.config.DEFAULT_PSM_MODES
            )

            # Load image
            img = self._load_image(image_bytes, filename)

            # Process with different PSM modes
            results = []
            for psm in psm_modes:
                result = self.ocr_processor.process_image(
                    img,
                    preprocess_passes=preprocess_passes,
                    psm=psm,
                    language=language
                )
                results.append(result)

            # Select best result
            best_result = self._select_best_result(results)

            processing_time = time.time() - start_time
            logger.info(f"Document processing completed in {processing_time:.2f} seconds")

            return {
                "text": best_result.text,
                "confidence": best_result.confidence,
                "psm": best_result.psm,
                "preprocessing_info": best_result.preprocessing_info,
                "processing_time": processing_time,
                "all_attempts": [
                    {
                        "text": r.text,
                        "confidence": r.confidence,
                        "psm": r.psm,
                        "processing_time": r.processing_time
                    } for r in results
                ]
            }

        except Exception as e:
            logger.error(f"Document processing failed: {str(e)}")
            raise

    def _load_image(self, image_bytes: bytes, filename: str) -> Image.Image:
        """Load image with format handling"""
        try:
            if filename.lower().endswith(".tiff"):
                return self._convert_tiff_to_rgb(image_bytes)
            return Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            logger.error(f"Image loading failed: {str(e)}")
            raise

    @staticmethod
    def _convert_tiff_to_rgb(tiff_bytes: bytes) -> Image.Image:
        """Convert TIFF to RGB format"""
        tiff_image = Image.open(io.BytesIO(tiff_bytes))
        if tiff_image.mode != "RGB":
            return tiff_image.convert("RGB")
        return tiff_image

    def _select_best_result(self, results: List[OCRResult]) -> OCRResult:
        """Select best result using multiple criteria"""
        if not results:
            return OCRResult("", 0.0, 0, {}, 0.0)

        scored_results = []
        for result in results:
            quality_score = self._assess_text_quality(result)
            scored_results.append((quality_score, result))

        # Get top results
        scored_results.sort(key=lambda x: x[0], reverse=True)

        if len(scored_results) > 1:
            # If top scores are close, use additional criteria
            if abs(scored_results[0][0] - scored_results[1][0]) < 0.1:
                return max(
                    [r[1] for r in scored_results[:2]],
                    key=lambda x: len(x.text.split())
                )

        return scored_results[0][1]

    def _assess_text_quality(self, result: OCRResult) -> float:
        """Assess OCR result quality using multiple metrics"""
        if not result.text or result.confidence < self.config.MIN_CONFIDENCE_THRESHOLD:
            return 0.0

        # Check for common OCR errors
        error_patterns = {
            'confused_chars': r'\d{1,2}[l|I]',  # Confused 1/l/I
            'garbage_seq': r'[^a-zA-Z0-9\s\.,!?-]{3,}',  # Garbage character sequences
            'repeated_chars': r'(.)\1{3,}',  # Excessive character repetition
            'isolated_chars': r'\b[a-zA-Z]\b'  # Single character words (except a/I)
        }

        # Calculate error score
        text_length = len(result.text)
        error_counts = {
            name: len(re.findall(pattern, result.text))
            for name, pattern in error_patterns.items()
        }

        total_errors = sum(error_counts.values())
        error_score = 1.0 - (total_errors / max(text_length, 1))

        # Word analysis
        words = result.text.split()
        if words:
            word_lengths = [len(w) for w in words]
            avg_word_length = statistics.mean(word_lengths)
            word_length_variance = statistics.variance(word_lengths) if len(words) > 1 else 0

            # Score word length distribution (prefer 3-15 character words)
            length_score = sum(1 for l in word_lengths if 3 <= l <= 15) / len(words)

            # Penalize high variance in word lengths
            variance_penalty = min(1.0, word_length_variance / 100)
            length_score *= (1 - variance_penalty)
        else:
            length_score = 0.0

        # Combine scores with weights from config
        final_score = (
                result.confidence / 100.0 * self.config.CONFIDENCE_WEIGHT +
                error_score * self.config.ERROR_WEIGHT +
                length_score * self.config.LENGTH_WEIGHT
        )

        logger.debug(f"Quality assessment - Confidence: {result.confidence:.2f}, "
                     f"Error Score: {error_score:.2f}, Length Score: {length_score:.2f}, "
                     f"Final Score: {final_score:.2f}")

        return max(0.0, min(1.0, final_score))


class PDFProcessor:
    """Handles PDF-specific processing with memory management"""

    def __init__(self, config: OCRConfig = OCRConfig()):
        self.config = config
        self.document_processor = DocumentProcessor(config)

    def process_pdf(
            self,
            file_bytes: bytes,
            preprocess_passes: int = 2,
            psm_modes: Optional[List[int]] = None,
            language: str = OCRConfig.DEFAULT_LANGUAGE,
            max_pages: Optional[int] = None
    ) -> Dict:
        """
        Process PDF with memory-efficient batch processing
        """
        logger.info("Starting PDF processing")
        start_time = time.time()

        try:
            results = []
            total_pages = 0

            with tempfile.NamedTemporaryFile(suffix='.pdf') as tmp:
                tmp.write(file_bytes)
                tmp.flush()

                # Process pages in batches
                batch_size = self.config.BATCH_SIZE
                current_page = 1

                while True:
                    try:
                        # Convert batch of pages to images
                        images = convert_from_bytes(
                            file_bytes,
                            first_page=current_page,
                            last_page=min(
                                current_page + batch_size - 1,
                                max_pages if max_pages else float('inf')
                            )
                        )

                        if not images:
                            break

                        # Process each image in the batch
                        for idx, image in enumerate(images):
                            page_num = current_page + idx
                            logger.info(f"Processing page {page_num}")

                            result = self.document_processor.process_document(
                                self._image_to_bytes(image),
                                filename="page.png",
                                preprocess_passes=preprocess_passes,
                                psm_modes=psm_modes,
                                language=language
                            )

                            results.append({
                                'page_number': page_num,
                                'text': result['text'],
                                'confidence': result['confidence'],
                                'psm': result['psm']
                            })

                            total_pages += 1

                        current_page += batch_size

                        if max_pages and current_page > max_pages:
                            break

                        # Force garbage collection after each batch
                        gc.collect()

                    except Exception as e:
                        logger.error(f"Error processing PDF batch: {str(e)}")
                        break

            processing_time = time.time() - start_time
            logger.info(f"PDF processing completed. {total_pages} pages processed "
                        f"in {processing_time:.2f} seconds")

            return {
                'pages': results,
                'total_pages': total_pages,
                'processing_time': processing_time
            }

        except Exception as e:
            logger.error(f"PDF processing failed: {str(e)}")
            raise

    @staticmethod
    def _image_to_bytes(image: Image.Image) -> bytes:
        """Convert PIL Image to bytes"""
        with io.BytesIO() as bio:
            image.save(bio, format='PNG')
            return bio.getvalue()


def main():
    """Example usage of the enhanced OCR system"""
    # Configure logging
    setup_logging(level=logging.ERROR)

    # Initialize processors
    config = OCRConfig()
    doc_processor = DocumentProcessor(config)
    pdf_processor = PDFProcessor(config)
    return doc_processor, pdf_processor
    # Example image processing


def process_image_example(image_path: str):
    with open(image_path, 'rb') as f:
        image_bytes = f.read()

    result = doc_processor.process_document(
        image_bytes,
        filename=image_path,
        preprocess_passes=2,
        language="heb"
    )

    logger.info(f"OCR Result: {result['text'][:100]}...")
    logger.info(f"Confidence: {result['confidence']:.2f}")
    return result


# Example PDF processing
def process_pdf_example(pdf_path: str):
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()

    result = pdf_processor.process_pdf(
        pdf_bytes,
        preprocess_passes=2,
        language="heb",
        max_pages=10
    )

    logger.info(f"Processed {result['total_pages']} pages")
    return result


if __name__ == "__main__":
    doc_processor, pdf_processor = main()
    for f in os.listdir('/Users/ofekedut/development/otech/projects/API/lior_arbivv/test_extraction_service/monday_assets'):
        start_at = datetime.now()
        if f.lower().endswith('.pdf'):
            text = process_pdf_example(f'/Users/ofekedut/development/otech/projects/API/lior_arbivv/test_extraction_service/monday_assets/{f}')
            pages = text['pages']
            text = ''
            confidence = pages[0]['confidence']
            for page in pages:
                confidence = (confidence + page['confidence']) / 2
                text = text + page['text']
            text = {
                'filename': f,
                'text': text,
                'confidence': confidence,
            }
        else:
            text = process_image_example(f'/Users/ofekedut/development/otech/projects/API/lior_arbivv/test_extraction_service/monday_assets/{f}')
            text = {
                'filename': f,
                'text': text['text'],
                'confidence': text['confidence'],
            }
        print(json.dumps(text, indent=2, ensure_ascii=False))
        end_at = datetime.now() - start_at
        print(f"total time {end_at.seconds}secs")
        gc.collect()
