import os
import time
import re
import logging
from pathlib import Path

# PDF processing libraries
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    import pypdfium2
    PYPDFIUM2_AVAILABLE = True
except ImportError:
    PYPDFIUM2_AVAILABLE = False

logger = logging.getLogger(__name__)

class PDFProcessor:
    """
    Advanced PDF processor that extracts and cleans text from German business documents
    Integrated with your Kaggle Mistral 7B preprocessing code
    """
    
    def __init__(self):
        self.available_methods = []
        
        if PYMUPDF_AVAILABLE:
            self.available_methods.append('pymupdf')
        if PDFPLUMBER_AVAILABLE:
            self.available_methods.append('pdfplumber')
        if PYPDFIUM2_AVAILABLE:
            self.available_methods.append('pypdfium2')
        
        logger.info(f"PDF processor initialized with methods: {self.available_methods}")
        
        if not self.available_methods:
            raise RuntimeError("No PDF processing libraries available. Install PyMuPDF, pdfplumber, or pypdfium2")
    
    def process_pdf(self, file_path):
        """
        Main processing method - tries all available methods and returns best result
        Integrates your Kaggle preprocessing logic
        
        Args:
            file_path (str): Path to the PDF file
            
        Returns:
            dict: Processing result with success status and cleaned text
        """
        try:
            logger.info(f"Processing PDF: {os.path.basename(file_path)}")
            
            # Validate PDF file
            validation_result = self._validate_pdf(file_path)
            if not validation_result["valid"]:
                return {"success": False, "error": validation_result["error"]}
            
            # Try all available extraction methods
            extraction_results = []
            
            for method in self.available_methods:
                try:
                    if method == 'pymupdf':
                        result = self._extract_text_pymupdf(file_path)
                    elif method == 'pdfplumber':
                        result = self._extract_text_pdfplumber(file_path)
                    elif method == 'pypdfium2':
                        result = self._extract_text_pypdfium2(file_path)
                    
                    if result["success"]:
                        extraction_results.append(result)
                        
                except Exception as e:
                    logger.warning(f"Method {method} failed: {e}")
                    continue
            
            if not extraction_results:
                return {"success": False, "error": "All text extraction methods failed"}
            
            # Choose best result (prioritize text length, then speed)
            best_result = self._choose_best_result(extraction_results)
            
            # Preprocess with your Kaggle logic
            cleaned_text = self._preprocess_german_text_kaggle(best_result["text"])
            
            final_result = {
                "success": True,
                "method": best_result["method"],
                "raw_text": best_result["text"],
                "cleaned_text": cleaned_text,
                "stats": {
                    "raw_length": len(best_result["text"]),
                    "cleaned_length": len(cleaned_text),
                    "word_count": len(cleaned_text.split()),
                    "processing_time": best_result["processing_time"],
                    "pages_processed": best_result.get("pages_processed", 0)
                }
            }
            
            logger.info(f"PDF processed successfully: {final_result['stats']['word_count']} words extracted")
            return final_result
            
        except Exception as e:
            logger.error(f"PDF processing failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _validate_pdf(self, file_path):
        """Validate PDF file"""
        try:
            if not os.path.exists(file_path):
                return {"valid": False, "error": "File not found"}
            
            if not file_path.lower().endswith('.pdf'):
                return {"valid": False, "error": "Not a PDF file"}
            
            file_size_mb = os.path.getsize(file_path) / (1024*1024)
            
            if file_size_mb > 50:
                return {"valid": False, "error": "PDF file too large (>50MB)"}
            
            # Try basic PDF validation
            if PYMUPDF_AVAILABLE:
                try:
                    doc = fitz.open(file_path)
                    page_count = len(doc)
                    doc.close()
                    
                    if page_count == 0:
                        return {"valid": False, "error": "PDF has no pages"}
                    
                except Exception:
                    return {"valid": False, "error": "Invalid or corrupted PDF file"}
            
            return {"valid": True}
            
        except Exception as e:
            return {"valid": False, "error": f"Validation failed: {str(e)}"}
    
    def _extract_text_pymupdf(self, file_path):
        """Extract text using PyMuPDF"""
        logger.info("Extracting text using PyMuPDF...")
        start_time = time.time()
        
        try:
            doc = fitz.open(file_path)
            extracted_text = ""
            total_pages = len(doc)
            
            for page_num in range(total_pages):
                page = doc[page_num]
                page_text = page.get_text()
                extracted_text += f"\n\n--- PAGE {page_num + 1} ---\n\n"
                extracted_text += page_text
            
            doc.close()
            
            processing_time = time.time() - start_time
            text_length = len(extracted_text.strip())
            word_count = len(extracted_text.split())
            
            return {
                "method": "PyMuPDF",
                "success": True,
                "text": extracted_text.strip(),
                "text_length": text_length,
                "word_count": word_count,
                "processing_time": round(processing_time, 3),
                "pages_processed": total_pages
            }
            
        except Exception as e:
            return {
                "method": "PyMuPDF",
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time
            }
    
    def _extract_text_pdfplumber(self, file_path):
        """Extract text using pdfplumber with table extraction"""
        logger.info("Extracting text using pdfplumber...")
        start_time = time.time()
        
        try:
            extracted_text = ""
            
            with pdfplumber.open(file_path) as pdf:
                total_pages = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        extracted_text += f"\n\n--- PAGE {page_num + 1} ---\n\n"
                        extracted_text += page_text
                    
                    # Extract table data if present
                    tables = page.extract_tables()
                    if tables:
                        extracted_text += f"\n\n[TABLES ON PAGE {page_num + 1}]\n"
                        for table_num, table in enumerate(tables):
                            extracted_text += f"\nTable {table_num + 1}:\n"
                            for row in table:
                                if row:
                                    row_text = " | ".join([cell if cell else "" for cell in row])
                                    extracted_text += row_text + "\n"
            
            processing_time = time.time() - start_time
            text_length = len(extracted_text.strip())
            word_count = len(extracted_text.split())
            
            return {
                "method": "pdfplumber",
                "success": True,
                "text": extracted_text.strip(),
                "text_length": text_length,
                "word_count": word_count,
                "processing_time": round(processing_time, 3),
                "pages_processed": total_pages,
                "includes_tables": "[TABLES ON PAGE" in extracted_text
            }
            
        except Exception as e:
            return {
                "method": "pdfplumber",
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time
            }
    
    def _extract_text_pypdfium2(self, file_path):
        """Extract text using pypdfium2"""
        logger.info("Extracting text using pypdfium2...")
        start_time = time.time()
        
        try:
            pdf = pypdfium2.PdfDocument(file_path)
            extracted_text = ""
            total_pages = len(pdf)
            
            for page_num in range(total_pages):
                page = pdf.get_page(page_num)
                textpage = page.get_textpage()
                page_text = textpage.get_text_range()
                
                extracted_text += f"\n\n--- PAGE {page_num + 1} ---\n\n"
                extracted_text += page_text
                
                textpage.close()
                page.close()
            
            pdf.close()
            
            processing_time = time.time() - start_time
            text_length = len(extracted_text.strip())
            word_count = len(extracted_text.split())
            
            return {
                "method": "pypdfium2",
                "success": True,
                "text": extracted_text.strip(),
                "text_length": text_length,
                "word_count": word_count,
                "processing_time": round(processing_time, 3),
                "pages_processed": total_pages
            }
            
        except Exception as e:
            return {
                "method": "pypdfium2",
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time
            }
    
    def _choose_best_result(self, results):
        """Choose the best extraction result"""
        successful = [r for r in results if r.get("success", False)]
        
        if not successful:
            return None
        
        # Find method with most text
        most_text = max(successful, key=lambda x: x["text_length"])
        
        # If we got substantial text (>100 chars), use that
        if most_text["text_length"] > 100:
            return most_text
        
        # Otherwise, use fastest method with decent text
        fastest = min(successful, key=lambda x: x["processing_time"])
        if fastest["text_length"] > 50:
            return fastest
        
        # Last resort: first successful method
        return successful[0]
    
    def _preprocess_german_text_kaggle(self, raw_text):
        """
        Advanced preprocessing for German text
        EXACT FROM YOUR KAGGLE CODE
        """
        if not raw_text or not raw_text.strip():
            return ""
        
        logger.info("Preprocessing German text (Kaggle method)...")
        text = raw_text
        
        # 0. Convert literal \\n to actual newlines
        text = text.replace('\\n', '\n')
        
        # 1. Remove table markers
        text = text.replace('[TABLES ON PAGE 1]', '')
        text = text.replace('Table 1:', '')
        text = text.replace('\nTable 1:\n', '\n')
        
        # 2. Remove pipe characters (table separators)
        text = text.replace('|', ' ')
        
        # 3. Remove column headers (1 2 3 4 5)
        text = re.sub(r'\n1 2 3 4 5\n', '\n', text)
        text = re.sub(r'^1 2 3 4 5\n', '', text, flags=re.MULTILINE)
        
        # 4. Remove row numbers at start of lines
        text = re.sub(r'^[123] \| ', '', text, flags=re.MULTILINE)
        text = re.sub(r'^[123] ', '', text, flags=re.MULTILINE)
        
        # 5. Fix unicode characters (German umlauts)
        text = text.replace("√°", "ä")
        text = text.replace("√∂", "ö")
        text = text.replace("√ü", "ü")
        text = text.replace("√ì", "ß")
        
        # 6. Remove page separators
        text = re.sub(r'\n+--- PAGE \d+ ---\n+', '\n', text)
        text = re.sub(r'--- PAGE \d+ ---', '', text)
        
        # 7. Remove page numbers
        text = re.sub(r'Seite \d+ von \d+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Page \d+ of \d+', '', text, flags=re.IGNORECASE)
        
        # 8. Remove abruf date
        text = re.sub(r'Abruf vom [\d.]+ \d{2}:\d{2}', '', text, flags=re.IGNORECASE)
        
        # 9. Fix lines with NO SPACES between words
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        text = re.sub(r'([0-9])([a-z])', r'\1 \2', text)
        
        # 10. Fix hyphenation
        text = re.sub(r'-\s*\n\s*', '', text)
        text = re.sub(r'(\w)\n(\w)', r'\1 \2', text)
        
        # 11. Normalize spaces
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r'\t+', ' ', text)
        
        # 12. Normalize newlines
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = '\n'.join(line.rstrip() for line in text.split('\n'))
        
        # 13. Remove noise
        text = re.sub(r'\.{3,}', '...', text)
        text = re.sub(r'-{3,}', '---', text)
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F]', '', text)
        
        # 14. Remove header lines
        text = re.sub(r'Nummer [a\)] Name [a\)] Allgemeine.*?Bemerkungen', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Nummer der Eintragung.*?Bemerkungen', '', text, flags=re.IGNORECASE)
        
        # 15. Remove excessive blank lines at start
        text = re.sub(r'^\n\n\n+', '', text)
        text = re.sub(r'\n\n\n+', '\n\n', text)
        
        # 16. Final trim
        text = text.strip()
        
        logger.info(f"✓ Text cleaned! ({len(text)} chars)")
        return text
