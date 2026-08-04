import os
import time
import re
import logging
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

logger = logging.getLogger(__name__)

class GermanDocumentSummarizer:
    """
    German Document Summarizer using Mistral 7B
    Fixed: Proper initialization, error handling, always returns dict
    """
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = None
        self.model_loaded = False
        logger.info("Initializing GermanDocumentSummarizer...")
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize Mistral 7B model with proper error handling"""
        try:
            logger.info("🔄 Loading Mistral 7B model...")
            
            model_id = "mistralai/Mistral-7B-Instruct-v0.2"
            
            # Check if model files are already cached
            logger.info(f"Loading tokenizer from: {model_id}")
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_id,
                trust_remote_code=False,
                local_files_only=False
            )
            logger.info("✓ Tokenizer loaded")
            
            # Determine dtype based on available hardware
            if torch.cuda.is_available():
                logger.info("CUDA available - using bfloat16")
                dtype = torch.bfloat16
            else:
                logger.info("CUDA not available - using float32")
                dtype = torch.float32
            
            # Load model
            logger.info(f"Loading model from: {model_id}")
            self.model = AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype=dtype,
                device_map="auto",
                trust_remote_code=False,
                low_cpu_mem_usage=True,
                attn_implementation="eager"  # Use eager attention for compatibility
            )
            logger.info("✓ Model loaded")
            
            # Set pad token
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Get device
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            
            # Set model to eval mode
            self.model.eval()
            
            self.model_loaded = True
            logger.info(f"✅ Mistral 7B initialized successfully on {self.device}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize model: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            self.model_loaded = False
            self.model = None
            self.tokenizer = None
    
    def is_model_loaded(self):
        """Check if model is properly loaded"""
        is_loaded = self.model_loaded and self.model is not None and self.tokenizer is not None
        logger.debug(f"Model loaded status: {is_loaded}")
        return is_loaded
    
    def extract_clean_response(self, full_output: str) -> str:
        """Extract clean response from Mistral output"""
        if not full_output:
            return ""
        
        text = full_output.strip()
        
        # Keep only the LAST "Company Details:" block if repeated
        if text.count("Company Details:") > 1:
            text = text.split("Company Details:")[-1].strip()
            text = "Company Details: " + text
        
        # Remove anything after model accidentally repeats
        cutoff_markers = [
            "### DOCUMENT", "### REQUIRED", "### STRUCTURED", 
            "### END", "Now analyze", "### DOCUMENT TO ANALYZE",
            "You are a legal expert"
        ]
        for m in cutoff_markers:
            if m in text:
                text = text[:text.index(m)]
        
        # Collapse extra blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = text.strip()
        
        return text if text else "No summary generated"
    
    def generate_summary(self, cleaned_text):
        """
        Generate structured summary using Mistral 7B
        ALWAYS returns a dictionary (never None)
        """
        try:
            logger.info("🔄 Generating summary with Mistral 7B...")
            start_time = time.time()
            
            # Validate input
            if not cleaned_text or len(cleaned_text.strip()) < 50:
                logger.warning("⚠️ Text too short for summarization")
                return {
                    'success': False,
                    'error': 'Text too short for summarization (min 50 chars)',
                    'formatted_summary': '',
                    'word_count': 0,
                    'quality_score': 0,
                    'extracted_info': {}
                }
            
            # Check model loaded
            if not self.is_model_loaded():
                logger.error("❌ Model not loaded or initialization failed")
                return {
                    'success': False,
                    'error': 'AI model not available - failed to load Mistral 7B',
                    'formatted_summary': '',
                    'word_count': 0,
                    'quality_score': 0,
                    'extracted_info': {}
                }
            
            # Truncate text if too long to avoid memory issues
            if len(cleaned_text) > 3000:
                logger.info(f"Truncating text from {len(cleaned_text)} to 3000 chars")
                cleaned_text = cleaned_text[:3000]
            
            # Build prompt
            complete_prompt = f"""You are a legal expert summarizer specialized in German commercial and association registries.

Extract all relevant information from the following registry document and present it
in the exact structured format below.

Always include *all* fields, even if some values are not available.

### REQUIRED OUTPUT FORMAT:

Company Details:
Organization Name: ...
Register Number: ...
Registered Office: ...
Registration Court: ...
Registration Date: ...

Persons Involved:
• Person Name – Role/Occupation/Responsibility

Summary:
(Write a concise 5–8 line summary highlighting registration, company type, key persons, authority rules,
and any notable details such as changes, mergers, or statute updates.)

If a field is missing, write "Not specified".
Keep the style factual, clear, and professional.
Retain important German legal terms (e.g., Amtsgericht, e.V., GmbH, Kommanditgesellschaft).

### DOCUMENT TO ANALYZE:
{cleaned_text}

### STRUCTURED SUMMARY:"""
            
            # Tokenize
            logger.info("📝 Tokenizing input...")
            inputs = self.tokenizer(
                complete_prompt,
                return_tensors="pt",
                truncation=True,
                max_length=2048,
                padding=True
            )
            
            # Move to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            logger.info(f"✓ Input tokenized and moved to {self.device}")
            
            # Generate
            logger.info("🤖 Generating response with Mistral 7B...")
            with torch.no_grad():
                outputs = self.model.generate(
                    input_ids=inputs["input_ids"],
                    attention_mask=inputs["attention_mask"],
                    pad_token_id=self.tokenizer.eos_token_id,
                    max_new_tokens=512,
                    do_sample=False,
                    num_beams=2,
                    length_penalty=1.1,
                    temperature=0.7,
                    top_p=0.9
                )
            
            # Decode
            logger.info("📄 Decoding output...")
            full_output = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract clean response
            clean_response = self.extract_clean_response(full_output)
            
            processing_time = time.time() - start_time
            word_count = len(clean_response.split())
            
            logger.info(f"✅ Summary generated: {word_count} words in {processing_time:.2f}s")
            
            # ALWAYS return a properly formed dictionary
            return {
                'success': True,
                'formatted_summary': clean_response,
                'word_count': word_count,
                'processing_time': round(processing_time, 2),
                'quality_score': 85,
                'extracted_info': self._parse_structured_output(clean_response)
            }
            
        except Exception as e:
            logger.error(f"❌ Summary generation failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            # ALWAYS return a properly formed dictionary, even on error
            return {
                'success': False,
                'error': str(e),
                'formatted_summary': '',
                'word_count': 0,
                'quality_score': 0,
                'extracted_info': {}
            }
    
    def _parse_structured_output(self, text):
        """Parse structured output from Mistral"""
        info = {}
        
        try:
            # Extract organization name
            org_match = re.search(r'Organization Name:\s*(.+?)(?:\n|$)', text)
            if org_match:
                value = org_match.group(1).strip()
                if value and value.lower() != 'not specified' and len(value) > 2:
                    info['organization'] = value
            
            # Extract register number
            reg_match = re.search(r'Register Number:\s*(.+?)(?:\n|$)', text)
            if reg_match:
                value = reg_match.group(1).strip()
                if value and value.lower() != 'not specified':
                    info['register_number'] = value
            
            # Extract location
            loc_match = re.search(r'Registered Office:\s*(.+?)(?:\n|$)', text)
            if loc_match:
                value = loc_match.group(1).strip()
                if value and value.lower() != 'not specified' and len(value) > 2:
                    info['location'] = value
            
            # Extract court
            court_match = re.search(r'Registration Court:\s*(.+?)(?:\n|$)', text)
            if court_match:
                value = court_match.group(1).strip()
                if value and value.lower() != 'not specified' and len(value) > 2:
                    info['court'] = value
            
            # Extract date
            date_match = re.search(r'Registration Date:\s*(.+?)(?:\n|$)', text)
            if date_match:
                value = date_match.group(1).strip()
                if value and value.lower() != 'not specified':
                    info['date'] = value
        
        except Exception as e:
            logger.warning(f"Error parsing structured output: {e}")
        
        return info
