"""
PDF Parsing and Workflow Application with Mistral 7B Integration
Main Flask application with proper structure and error handling
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import os
import time
import logging
from pathlib import Path
import traceback
import math

# Import configuration
from config import Config

# Import backend modules
from backend.web_scraper import HandelsregisterScraper
from backend.pdf_processor import PDFProcessor
from backend.ai_summarizer import GermanDocumentSummarizer
from backend.utils import setup_logging, create_safe_filename, validate_company_name

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize CORS
    CORS(app)

    # Initialize configuration
    Config.init_app(app)

    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)

    # Initialize components
    logger.info("🚀 Initializing PDF Parsing System with Mistral 7B...")

    try:
        pdf_processor = PDFProcessor()
        logger.info("✅ PDF Processor initialized")
        
        ai_summarizer = GermanDocumentSummarizer()
        logger.info("✅ Mistral 7B Summarizer initialized")
        
        logger.info("✅ All components initialized successfully!")
    except Exception as e:
        logger.error(f"❌ Component initialization failed: {e}")
        raise

    # ========================================================
    # ROUTES
    # ========================================================

    @app.route('/')
    def index():
        """Serve the main web interface"""
        try:
            return render_template('index.html')
        except Exception as e:
            logger.error(f"Template rendering error: {e}")
            return jsonify({
                'success': False,
                'error': 'Template not found. Please check the templates folder.'
            }), 500

    def save_summary_to_file(company_name, summary_text):
        """Save summary to file"""
        summaries_dir = os.path.abspath("summaries")
        os.makedirs(summaries_dir, exist_ok=True)
    
        safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in company_name.strip())
        filename = f"{safe_name}_{int(time.time())}.txt"
        filepath = os.path.join(summaries_dir, filename)
    
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(summary_text)
        
        return filepath

    @app.route('/api/process-company', methods=['POST'])
    def process_company():
        """
        Main API endpoint: Complete company processing pipeline with Mistral 7B
        Stage 1: Search & Download from handelsregister.de
        Stage 2: Extract & Preprocess PDF
        Stage 3: Generate AI Summary with Mistral 7B
        """
        start_time = time.time()

        try:
            # Get and validate input
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'No JSON data provided',
                    'stage': 'validation'
                }), 400

            company_name = data.get('company', '').strip()

            # Validate company name
            is_valid, error_msg = validate_company_name(company_name)
            if not is_valid:
                return jsonify({
                    'success': False,
                    'error': error_msg,
                    'stage': 'validation'
                }), 400

            logger.info(f"Processing company: {company_name}")

            # ===== STAGE 1: Search and download from handelsregister.de =====
            logger.info("Stage 1: Searching handelsregister.de...")
            scraper = HandelsregisterScraper(
                headless=app.config['CHROME_HEADLESS'],
                timeout=app.config['SELENIUM_TIMEOUT'],
                retries=app.config['SELENIUM_RETRIES']
            )

            download_result = scraper.search_and_download(company_name)

            if not download_result['success']:
                return jsonify({
                    'success': False,
                    'error': download_result['error'],
                    'stage': 'download'
                }), 422

            logger.info(f"✓ Stage 1 complete: PDF downloaded ({download_result['size']} bytes)")

            # ===== STAGE 2: Process PDF with Kaggle preprocessing =====
            logger.info("Stage 2: Processing PDF...")
            pdf_path = download_result['pdf_path']

            if not os.path.exists(pdf_path):
                return jsonify({
                    'success': False,
                    'error': 'Downloaded PDF file not found',
                    'stage': 'pdf_processing'
                }), 500

            processing_result = pdf_processor.process_pdf(pdf_path)

            if not processing_result['success']:
                return jsonify({
                    'success': False,
                    'error': processing_result['error'],
                    'stage': 'pdf_processing'
                }), 422

            logger.info(f"✓ Stage 2 complete: Text extracted and cleaned ({processing_result['stats']['cleaned_length']} chars)")

            # ===== STAGE 3: Generate AI summary with Mistral 7B =====
            logger.info("Stage 3: Generating AI summary with Mistral 7B...")
            cleaned_text = processing_result['cleaned_text']

            if len(cleaned_text.strip()) < 50:
                return jsonify({
                    'success': False,
                    'error': 'Extracted text too short for meaningful summarization',
                    'stage': 'ai_summary'
                }), 422

            summary_result = ai_summarizer.generate_summary(cleaned_text)

            if not summary_result['success']:
                return jsonify({
                    'success': False,
                    'error': summary_result['error'],
                    'stage': 'ai_summary'
                }), 422

            logger.info(f"✓ Stage 3 complete: Summary generated ({summary_result.get('word_count', 0)} words)")

            # ===== STAGE 4: Return complete result =====
            total_time = round(time.time() - start_time, 2)

            final_result = {
                'success': True,
                'company_name': download_result.get('company_found', company_name),
                'filename': download_result['filename'],
                'file_size': format_file_size(download_result['size']),
                'pdf_path': download_result['pdf_path'],
                'summary': summary_result['formatted_summary'],
                'processing_stats': {
                    'total_time': total_time,
                    'quality_score': summary_result.get('quality_score', 85),
                    'word_count': summary_result.get('word_count', 0),
                    'extraction_method': processing_result.get('method', 'Unknown'),
                    'pages_processed': processing_result.get('stats', {}).get('pages_processed', 0),
                    'stage_1_time': 'Download',
                    'stage_2_time': 'PDF Processing',
                    'stage_3_time': 'Mistral 7B Summarization'
                },
                'extracted_info': summary_result.get('extracted_info', {}),
                'stage': 'complete'
            }

            logger.info(f"✅ Successfully processed {company_name} in {total_time}s")
            return jsonify(final_result)

        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"Processing error: {str(e)}\n{error_trace}")

            return jsonify({
                'success': False,
                'error': f"Internal processing error: {str(e)}",
                'stage': 'internal_error'
            }), 500

    @app.route('/api/upload-pdf', methods=['POST'])
    def upload_pdf():
        """
        Alternative endpoint for direct PDF upload (for testing)
        Skips Stage 1 (download) and goes directly to PDF processing + Mistral summary
        """
        try:
            if 'file' not in request.files:
                return jsonify({'success': False, 'error': 'No file provided'}), 400

            file = request.files['file']

            if file.filename == '':
                return jsonify({'success': False, 'error': 'No file selected'}), 400

            if not file.filename.lower().endswith('.pdf'):
                return jsonify({'success': False, 'error': 'Only PDF files allowed'}), 400

            # Save uploaded file
            filename = create_safe_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            logger.info(f"PDF uploaded: {filename}")

            # ===== STAGE 2: Process the uploaded PDF =====
            logger.info("Processing uploaded PDF...")
            processing_result = pdf_processor.process_pdf(filepath)

            if not processing_result['success']:
                return jsonify({'success': False, 'error': processing_result['error']}), 422

            # ===== STAGE 3: Generate summary with Mistral 7B =====
            logger.info("Generating Mistral 7B summary...")
            summary_result = ai_summarizer.generate_summary(processing_result['cleaned_text'])

            if not summary_result['success']:
                return jsonify({'success': False, 'error': summary_result['error']}), 422

            return jsonify({
                'success': True,
                'filename': filename,
                'summary': summary_result['formatted_summary'],
                'processing_stats': {
                    'extraction_method': processing_result.get('method', 'Unknown'),
                    'pages_processed': processing_result.get('stats', {}).get('pages_processed', 0),
                    'word_count': summary_result.get('word_count', 0),
                    'quality_score': summary_result.get('quality_score', 85)
                },
                'extracted_info': summary_result.get('extracted_info', {})
            })

        except Exception as e:
            logger.error(f"Upload processing error: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/download/<filename>')
    def download_file(filename):
        """Allow users to download processed PDF files"""
        try:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            if not os.path.exists(filepath):
                return jsonify({'error': 'File not found'}), 404

            return send_file(
                filepath,
                as_attachment=True,
                download_name=filename
            )

        except Exception as e:
            logger.error(f"Download error: {str(e)}")
            return jsonify({'error': 'Download failed'}), 500

    @app.route('/api/health')
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'timestamp': time.time(),
            'components': {
                'pdf_processor': True,
                'ai_summarizer': ai_summarizer.is_model_loaded(),
                'web_scraper': True
            },
            'ai_model': 'Mistral-7B-Instruct-v0.2'
        })

    @app.route('/api/status')
    def api_status():
        """Get API status"""
        return jsonify({
            'service': 'German Registry Document Summarizer API',
            'version': '2.0.0',
            'status': 'running',
            'ai_model': 'Mistral-7B-Instruct-v0.2',
            'model_loaded': ai_summarizer.is_model_loaded()
        })

    # ========================================================
    # ERROR HANDLERS
    # ========================================================

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({'error': 'Internal server error'}), 500

    return app

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0B"

    size_names = ["B", "KB", "MB", "GB"]
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)

    return f"{s} {size_names[i]}"

# Create app instance
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False
    )
