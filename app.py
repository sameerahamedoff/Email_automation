from flask import Flask, request, jsonify, send_from_directory, url_for
from flask_cors import CORS
import sys
import os
import base64
import mimetypes
from functools import wraps
import time
import uuid
import json
from werkzeug.utils import secure_filename

# Import Cold_email_v2 directly since we're in the same directory
from Cold_email_v2 import (
    generate_base_email_content, 
    send_email,
    get_sn10_product_info,
    send_sn10_product_email,
    send_followup_email,
    process_excel_file,
    send_bulk_emails
)

app = Flask(__name__)
# Configure CORS to allow specific origins
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:5173",  # Development
            "https://automation.sensiq.ae"  # Production frontend domain
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Configure static folder for assets
ASSETS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')

# Configure upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Store job progress
email_jobs = {}

def handle_timeout(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            start_time = time.time()
            result = func(*args, **kwargs)
            if time.time() - start_time > 25:  # If operation takes more than 25 seconds
                return jsonify({
                    'success': False,
                    'error': 'Operation timed out. Please try again.'
                }), 504
            return result
        except Exception as e:
            print(f"Error in {func.__name__}: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    return wrapper

def get_image_as_data_url(filename):
    try:
        file_path = os.path.join(ASSETS_FOLDER, filename)
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                image_data = f.read()
                mime_type = mimetypes.guess_type(filename)[0]
                b64_data = base64.b64encode(image_data).decode('utf-8')
                return f'data:{mime_type};base64,{b64_data}'
    except Exception as e:
        print(f"Error loading image {filename}: {e}")
        return ''

@app.route('/assets/<path:filename>')
def serve_asset(filename):
    return send_from_directory(ASSETS_FOLDER, filename)

@app.route('/api/preview-email', methods=['POST'])
@handle_timeout
def preview_email():
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Invalid request format. JSON required.'
            }), 400

        data = request.json
        recipient_type = data.get('recipientType', 'municipality')
        country = data.get('country', 'UAE')
        language = data.get('language', 'English')
        test_email = data.get('email', '')
        email_type = data.get('emailType', 'regular')
        followup_stage = data.get('followupStage')

        print(f"Received request - Type: {email_type}, Recipient: {recipient_type}, Country: {country}, Language: {language}")

        if email_type == 'product':
            try:
                # Get product info
                product_info = get_sn10_product_info()
                
                # Read product template
                template_path = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    'templates',
                    'product_template.html'
                )
                with open(template_path, 'r', encoding='utf-8') as f:
                    body = f.read()
                
                # Replace placeholders
                body = body.replace('{{product_name}}', product_info['name'])
                body = body.replace('{{product_subtitle}}', product_info['subtitle'])
                body = body.replace('{{product_image}}', 'cid:product')
                
                # Format technical specifications
                specs_html = ''
                for category, details in product_info['technical_specs'].items():
                    specs_html += f'<div class="content-text"><h3 style="color: #0ef0a1;">{category.title()}</h3><ul style="list-style: none; padding-left: 0;">'
                    for key, value in details.items():
                        specs_html += f'<li style="margin-bottom: 8px;"><strong style="color: #9ba6b7;">{key.replace("_", " ").title()}:</strong> {value}</li>'
                    specs_html += '</ul></div>'
                body = body.replace('{{technical_specs}}', specs_html)
                
                # Format key features
                features_html = '<ul style="list-style: none; padding-left: 0;">'
                for feature in product_info['key_features']:
                    features_html += f'<li style="margin-bottom: 8px; color: #9ba6b7;">• {feature}</li>'
                features_html += '</ul>'
                body = body.replace('{{key_features}}', features_html)
                
                subject = f"Introducing {product_info['name']}: Advanced Waste Management Solution"
            except Exception as e:
                print(f"Error generating product email: {e}")
                return jsonify({
                    'success': False,
                    'error': f'Error generating product email: {str(e)}'
                }), 500
        elif email_type == 'followup':
            try:
                # Validate parameters
                if not followup_stage:
                    return jsonify({
                        'success': False,
                        'error': 'Follow-up stage is required for follow-up emails'
                    }), 400

                # Read follow-up template
                template_path = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    'templates',
                    'followup_template.html'
                )
                with open(template_path, 'r', encoding='utf-8') as f:
                    body = f.read()

                # Get follow-up content with validated parameters
                from templates.followup_content import get_followup_content
                content = get_followup_content(
                    country=country,
                    recipient_type=recipient_type,
                    followup_stage=followup_stage
                )

                # Replace placeholders
                recipient_name = test_email.split('@')[0].title() if test_email else '[recipient_name]'
                body = body.replace('{{recipient_name}}', recipient_name)
                body = body.replace('{{followup_intro}}', content['followup_intro'])
                body = body.replace('{{country_specific_content}}', content['country_specific_content'])
                body = body.replace('{{main_content}}', content['main_content'])
                body = body.replace('{{cta_message}}', content['cta_message'])

                # Generate subject line based on follow-up stage and country
                subject_prefixes = {
                    'first': "Following up: ",
                    'second': "Re: ",
                    'third': "Final follow-up: "
                }
                subject = f"{subject_prefixes[followup_stage]}Smart Waste Management Solution for {country}"

            except Exception as e:
                print(f"Error generating follow-up email: {e}")
                return jsonify({
                    'success': False,
                    'error': f'Error generating follow-up email: {str(e)}'
                }), 500
        else:
            try:
                # Generate regular email content
                subject, body = generate_base_email_content(
                    recipient_type=recipient_type,
                    country=country,
                    language=language
                )
            except Exception as e:
                print(f"Error generating regular email: {e}")
                return jsonify({
                    'success': False,
                    'error': f'Error generating regular email: {str(e)}'
                }), 500

        # Replace image CIDs with data URLs
        logo_data_url = get_image_as_data_url('logo.png')
        cover_data_url = get_image_as_data_url('Cover.png')
        product_data_url = get_image_as_data_url('SN10.jpg')

        body = body.replace('cid:logo', logo_data_url)
        body = body.replace('cid:cover', cover_data_url)
        body = body.replace('cid:product', product_data_url)

        # Replace [recipient_name] with name from email if provided
        if test_email:
            name = test_email.split('@')[0].title()
            body = body.replace('[recipient_name]', name)

        return jsonify({
            'success': True,
            'subject': subject,
            'body': body
        })

    except Exception as e:
        print(f"Error in preview_email: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/send-email', methods=['POST', 'OPTIONS'])
@handle_timeout
def send_email_endpoint():
    if request.method == 'OPTIONS':
        # Respond to preflight request
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response

    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Invalid request format. JSON required.'
            }), 400

        data = request.json
        recipient_type = data.get('recipientType', 'municipality')
        country = data.get('country', 'UAE')
        language = data.get('language', 'English')
        recipient_email = data.get('email')
        email_type = data.get('emailType', 'regular')
        followup_stage = data.get('followupStage')  # New parameter

        if not recipient_email:
            return jsonify({
                'success': False,
                'error': 'Email address is required'
            }), 400

        # Get paths for images relative to the Cold_email_v2.py location
        parent_dir = os.path.dirname(os.path.abspath(__file__))
        images = {
            'logo': os.path.join(parent_dir, 'assets', 'logo.png'),
            'cover': os.path.join(parent_dir, 'assets', 'Cover.png'),
            'product': os.path.join(parent_dir, 'assets', 'SN10.jpg')
        }

        try:
            if email_type == 'product':
                # Send product email
                subject = f"Introducing {get_sn10_product_info()['name']}: Advanced Waste Management Solution"
                success = send_sn10_product_email(recipient_email, subject, images=images)
                if not success:
                    return jsonify({'status': 'error', 'message': 'Failed to send product email. Check server logs for details.'}), 500
            elif email_type == 'followup':
                # Send follow-up email with validated parameters
                success = send_followup_email(
                    recipient_email=recipient_email,
                    country=country,
                    recipient_type=recipient_type,
                    followup_stage=followup_stage
                )
                if not success:
                    return jsonify({
                        'success': False,
                        'error': 'Failed to send follow-up email. Check server logs for details.'
                    }), 500
            else:
                # Generate regular email content
                subject, body = generate_base_email_content(
                    recipient_type=recipient_type,
                    country=country,
                    language=language
                )

                # Replace [recipient_name] with name from email
                if recipient_email:
                    name = recipient_email.split('@')[0].title()
                    body = body.replace('[recipient_name]', name)
                    body = body.replace('{{recipient_name}}', name)

                # Send the email with images
                success = send_email(
                    recipient_email, 
                    subject, 
                    body,
                    images=images
                )
                if not success:
                    return jsonify({'status': 'error', 'message': 'Failed to send email. Check server logs for details.'}), 500

            return jsonify({
                'success': True,
                'message': f'Email sent successfully to {recipient_email}'
            })

        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Error sending email: {str(e)}'
            }), 500

    except Exception as e:
        print(f"Error in send_email_endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/upload-excel', methods=['POST'])
@handle_timeout
def upload_excel():
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'error': 'No file part in the request'
        }), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({
            'success': False,
            'error': 'No file selected'
        }), 400
    
    if not (file.filename.endswith('.xlsx') or file.filename.endswith('.xls') or file.filename.endswith('.csv')):
        return jsonify({
            'success': False,
            'error': 'Invalid file format. Please upload an Excel (.xlsx, .xls) or CSV file'
        }), 400
    
    try:
        # Save the file with a secure filename
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Process the file to get column names
        import pandas as pd
        if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)
        
        columns = df.columns.tolist()
        
        # Generate a unique job ID
        job_id = str(uuid.uuid4())
        
        # Store file path with job ID
        email_jobs[job_id] = {
            'file_path': file_path,
            'status': 'uploaded',
            'columns': columns,
            'progress': 0,
            'results': None
        }
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'columns': columns,
            'message': 'File uploaded successfully'
        })
    
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error processing file: {str(e)}'
        }), 500

@app.route('/api/process-excel', methods=['POST'])
@handle_timeout
def process_excel():
    data = request.json
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'No data provided'
        }), 400
    
    job_id = data.get('job_id')
    email_column = data.get('email_column')
    additional_columns = data.get('additional_columns', [])
    email_type = data.get('emailType')
    recipient_type = data.get('recipientType')
    country = data.get('country')
    language = data.get('language')
    followup_stage = data.get('followupStage')
    
    if not job_id or not email_column or not email_type or not recipient_type or not country or not language:
        return jsonify({
            'success': False,
            'error': 'Missing required parameters'
        }), 400
    
    if job_id not in email_jobs:
        return jsonify({
            'success': False,
            'error': 'Invalid job ID'
        }), 400
    
    try:
        # Update job status
        email_jobs[job_id]['status'] = 'processing'
        
        # Get file path from job
        file_path = email_jobs[job_id]['file_path']
        
        # Process the Excel file
        email_data = process_excel_file(file_path, email_column, additional_columns)
        
        # Start a background thread to send emails
        import threading
        
        def send_emails_background():
            with app.app_context():
                try:
                    # Update job status
                    email_jobs[job_id]['status'] = 'sending'
                    email_jobs[job_id]['total'] = len(email_data)
                    email_jobs[job_id]['sent'] = 0
                    email_jobs[job_id]['failed'] = 0
                    email_jobs[job_id]['start_time'] = time.time()
                    
                    # Get absolute paths for images relative to the Cold_email_v2.py location
                    parent_dir = os.path.dirname(os.path.abspath(__file__))
                    images = {
                        'logo': os.path.join(parent_dir, 'assets', 'logo.png'),
                        'cover': os.path.join(parent_dir, 'assets', 'Cover.png'),
                        'product': os.path.join(parent_dir, 'assets', 'SN10.jpg')
                    }

                    # Verify all image paths exist
                    for img_type, img_path in images.items():
                        if not os.path.exists(img_path):
                            raise FileNotFoundError(f"Image file not found: {img_path}")

                    # Send emails to all recipients
                    for i, data in enumerate(email_data):
                        try:
                            email_address = data['email']
                            name = email_address.split('@')[0].title()
                            
                            # Send email based on type
                            if email_type == 'product':
                                # Get product info for subject line
                                product_info = get_sn10_product_info()
                                subject = f"Introducing {product_info['name']}: Advanced Waste Management Solution"
                                
                                # Read product template
                                template_path = os.path.join(parent_dir, 'templates', 'product_template.html')
                                with open(template_path, 'r', encoding='utf-8') as f:
                                    body = f.read()
                                
                                # Replace placeholders
                                body = body.replace('{{product_name}}', product_info['name'])
                                body = body.replace('{{product_subtitle}}', product_info['subtitle'])
                                body = body.replace('[recipient_name]', name)
                                body = body.replace('{{recipient_name}}', name)
                                body = body.replace('{{product_image}}', 'cid:product')
                                
                                # Format technical specifications
                                specs_html = format_product_specs(product_info)
                                features_html = format_product_features(product_info)
                                body = body.replace('{{technical_specs}}', specs_html)
                                body = body.replace('{{key_features}}', features_html)
                                
                                # Send the email with images
                                success = send_email(email_address, subject, body, images=images)
                            elif email_type == 'followup':
                                # Send follow-up email
                                success = send_followup_email(
                                    recipient_email=email_address,
                                    country=country,
                                    recipient_type=recipient_type,
                                    followup_stage=followup_stage
                                )
                            else:
                                # Generate regular email content
                                subject, body = generate_base_email_content(
                                    recipient_type=recipient_type,
                                    country=country,
                                    language=language
                                )
                                # Replace recipient name
                                body = body.replace('[recipient_name]', name)
                                # Send regular email
                                success = send_email(email_address, subject, body, images=images)
                            
                            if success:
                                email_jobs[job_id]['sent'] += 1
                            else:
                                email_jobs[job_id]['failed'] += 1
                            
                            # Update progress
                            email_jobs[job_id]['progress'] = int((i + 1) / len(email_data) * 100)
                            
                            # Add a small delay between emails to avoid rate limiting
                            time.sleep(1)
                            
                        except Exception as e:
                            email_jobs[job_id]['failed'] += 1
                            print(f"Error sending email to {data['email']}: {str(e)}")
                    
                    # Update job status and add completion time
                    email_jobs[job_id]['status'] = 'completed'
                    email_jobs[job_id]['completion_time'] = time.time()
                    
                except Exception as e:
                    email_jobs[job_id]['status'] = 'failed'
                    email_jobs[job_id]['error'] = str(e)
                    email_jobs[job_id]['completion_time'] = time.time()
                    print(f"Error in background thread: {str(e)}")
        
        # Start the background thread
        thread = threading.Thread(target=send_emails_background)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'Email sending process started',
            'total_emails': len(email_data)
        })
    
    except Exception as e:
        email_jobs[job_id]['status'] = 'failed'
        email_jobs[job_id]['error'] = str(e)
        
        print(f"Error processing Excel file: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error processing Excel file: {str(e)}'
        }), 500

def format_product_specs(product_info):
    """Format product technical specifications into HTML."""
    specs_html = ''
    for category, details in product_info['technical_specs'].items():
        specs_html += f'<div class="content-text"><h3 style="color: #0ef0a1;">{category.title()}</h3><ul style="list-style: none; padding-left: 0;">'
        for key, value in details.items():
            specs_html += f'<li style="margin-bottom: 8px;"><strong style="color: #9ba6b7;">{key.replace("_", " ").title()}:</strong> {value}</li>'
        specs_html += '</ul></div>'
    return specs_html

def format_product_features(product_info):
    """Format product features into HTML."""
    features_html = '<ul style="list-style: none; padding-left: 0;">'
    for feature in product_info['key_features']:
        features_html += f'<li style="margin-bottom: 8px; color: #9ba6b7;">• {feature}</li>'
    features_html += '</ul>'
    return features_html

@app.route('/api/job-status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    try:
        if not job_id:
            return jsonify({
                'success': False,
                'error': 'Job ID is required'
            }), 400
            
        if job_id not in email_jobs:
            return jsonify({
                'success': True,
                'status': 'not_found',
                'progress': 0,
                'total': 0,
                'sent': 0,
                'failed': 0,
                'error': 'Job not found or expired'
            })
        
        job = email_jobs[job_id]
        
        # Clean up completed or failed jobs after 5 minutes
        if job['status'] in ['completed', 'failed']:
            job_age = time.time() - job.get('completion_time', time.time())
            if job_age > 300:  # 5 minutes
                del email_jobs[job_id]
                return jsonify({
                    'success': True,
                    'status': 'expired',
                    'progress': 100,
                    'total': job.get('total', 0),
                    'sent': job.get('sent', 0),
                    'failed': job.get('failed', 0),
                    'error': 'Job data expired'
                })
        
        return jsonify({
            'success': True,
            'status': job['status'],
            'progress': job.get('progress', 0),
            'total': job.get('total', 0),
            'sent': job.get('sent', 0),
            'failed': job.get('failed', 0),
            'error': job.get('error')
        })
        
    except Exception as e:
        print(f"Error in get_job_status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/test-email-structure', methods=['GET'])
def test_email_structure():
    """Test endpoint to verify the email structure"""
    try:
        # Get product info
        product_info = get_sn10_product_info()
        
        # Get template
        parent_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(parent_dir, 'templates', 'product_template.html')
        
        with open(template_path, 'r', encoding='utf-8') as f:
            body = f.read()
        
        # Replace placeholders
        body = body.replace('{{product_name}}', product_info['name'])
        body = body.replace('{{product_subtitle}}', product_info['subtitle'])
        body = body.replace('{{product_image}}', 'cid:product')
        
        # Format technical specifications
        specs_html = format_product_specs(product_info)
        features_html = format_product_features(product_info)
        body = body.replace('{{technical_specs}}', specs_html)
        body = body.replace('{{key_features}}', features_html)
        
        # Get image paths
        images = {
            'logo': os.path.join(parent_dir, 'assets', 'logo.png'),
            'cover': os.path.join(parent_dir, 'assets', 'Cover.png'),
            'product': os.path.join(parent_dir, 'assets', 'SN10.jpg')
        }
        
        # Create email message
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.image import MIMEImage
        
        # Create a multipart message with the correct structure for inline images
        message = MIMEMultipart('alternative')
        message["From"] = "test@example.com"
        message["To"] = "test@example.com"
        message["Subject"] = "Test Email Structure"
        
        # Create HTML part
        html_part = MIMEText(body, "html")
        
        # Create related part to hold the HTML and inline images
        related = MIMEMultipart('related')
        related.attach(html_part)
        
        # Attach images
        for cid, path in images.items():
            if os.path.exists(path):
                with open(path, 'rb') as f:
                    img = MIMEImage(f.read())
                    img.add_header('Content-ID', f'<{cid}>')
                    img.add_header('Content-Disposition', 'inline', filename=os.path.basename(path))
                    related.attach(img)
        
        # Attach the related part to the message
        message.attach(related)
        
        # Return the email structure
        return jsonify({
            'success': True,
            'message': 'Email structure verified',
            'structure': str(message).split('\n')[:20]  # First 20 lines for brevity
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/test-regular-email', methods=['GET'])
def test_regular_email():
    """Test endpoint to verify the regular email structure"""
    try:
        # Generate regular email content
        subject, body = generate_base_email_content(
            recipient_type='municipality',
            country='UAE',
            language='English'
        )
        
        # Replace [recipient_name] with a test name
        body = body.replace('[recipient_name]', 'Test User')
        
        # Check if product image is referenced in the body
        product_image_referenced = 'cid:product' in body
        
        # Get image paths
        parent_dir = os.path.dirname(os.path.abspath(__file__))
        images = {
            'logo': os.path.join(parent_dir, 'assets', 'logo.png'),
            'cover': os.path.join(parent_dir, 'assets', 'Cover.png'),
            'product': os.path.join(parent_dir, 'assets', 'SN10.jpg')
        }
        
        # Create email message
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.image import MIMEImage
        
        # Create a multipart message with the correct structure for inline images
        message = MIMEMultipart('alternative')
        message["From"] = "test@example.com"
        message["To"] = "test@example.com"
        message["Subject"] = subject
        
        # Create HTML part
        html_part = MIMEText(body, "html")
        
        # Create related part to hold the HTML and inline images
        related = MIMEMultipart('related')
        related.attach(html_part)
        
        # Attach images
        for cid, path in images.items():
            if os.path.exists(path):
                with open(path, 'rb') as f:
                    img = MIMEImage(f.read())
                    img.add_header('Content-ID', f'<{cid}>')
                    img.add_header('Content-Disposition', 'inline', filename=os.path.basename(path))
                    related.attach(img)
        
        # Attach the related part to the message
        message.attach(related)
        
        # Return the email structure
        return jsonify({
            'success': True,
            'message': 'Regular email structure verified',
            'product_image_referenced': product_image_referenced,
            'body_excerpt': body[:1000] + '...',  # First 1000 chars for brevity
            'structure': str(message).split('\n')[:20]  # First 20 lines for brevity
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True) 