from flask import Flask, render_template, request, jsonify, redirect
from flask_cors import CORS
import json
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from .inventory_routes import inventory_bp
from .auth_routes import auth_bp, require_auth

app = Flask(__name__, template_folder='../frontend/templates')
CORS(app)  # Enable CORS for all routes

# Register blueprints
app.register_blueprint(inventory_bp)
app.register_blueprint(auth_bp)

# Configure upload folder
UPLOAD_FOLDER = '../data/uploads'
TEXT_LOGS_FOLDER = '../data/text_logs'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TEXT_LOGS_FOLDER'] = TEXT_LOGS_FOLDER

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TEXT_LOGS_FOLDER, exist_ok=True)

def save_text_to_log(text, source='microphone'):
    """Save recognized text to a log file."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] {source}: {text}\n"
    
    log_file = os.path.join(TEXT_LOGS_FOLDER, 'speech_log.txt')
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        return True
    except Exception as e:
        print(f"Error saving text to log: {e}")
        return False

def speech_to_text_from_file(audio_file_path):
    """Convert speech to text from audio file."""
    try:
        # Import speech recognition only when needed to avoid import errors
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        
        with sr.AudioFile(audio_file_path) as source:
            audio_data = recognizer.record(source)
        
        # Recognize speech
        text = recognizer.recognize_google(audio_data)
        return {
            'success': True,
            'text': text,
            'message': 'Speech recognized successfully from file!'
        }
        
    except ImportError:
        return {
            'success': False,
            'text': '',
            'message': 'Speech recognition library not available. Please install SpeechRecognition.'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Error processing audio file: {e}'
        }

@app.route('/')
def index():
    """Serve the main single page application."""
    return render_template('index.html')

@app.route('/login')
def login():
    """Redirect to main page (SPA handles login)."""
    return redirect('/')

@app.route('/signup')
def signup():
    """Redirect to main page (SPA handles signup)."""
    return redirect('/')

@app.route('/dashboard')
def dashboard():
    """Redirect to main page (SPA handles dashboard)."""
    return redirect('/')

@app.route('/speech-to-text')
def speech_to_text_page():
    """Redirect to main page (SPA handles speech-to-text)."""
    return redirect('/')

@app.route('/inventory')
def inventory_page():
    """Redirect to main page (SPA handles inventory)."""
    return redirect('/')

@app.route('/api/speech-to-text', methods=['POST'])
@require_auth
def speech_to_text_api():
    """API endpoint for speech-to-text conversion from audio files only."""
    audio_file = request.files['audio_file']
    if audio_file:
        filename = secure_filename(audio_file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        audio_file.save(filepath)
        result = speech_to_text_from_file(filepath)
        # Clean up the file after processing
        try:
            os.remove(filepath)
        except:
            pass
        
        # Save recognized text to log if successful
        if result['success']:
            save_text_to_log(result['text'], 'file_upload')
            
            # Try to process as inventory command
            inventory_result = None
            try:
                from .utils import parse_inventory_command
                from .db.models import get_db
                
                # Get user_id from authenticated session
                user_id = getattr(request, 'user', {}).get('user_id')
                
                if user_id:
                    # Parse the command
                    parsed_command = parse_inventory_command(result['text'])
                    
                    if 'error' not in parsed_command:
                        # Execute the command
                        db = get_db()
                        command_type = parsed_command['command']
                        
                        if command_type == 'add':
                            inventory_result = db.add_product(
                                parsed_command['product_name'],
                                parsed_command['quantity'],
                                user_id
                            )
                        elif command_type == 'sell':
                            inventory_result = db.sell_product(
                                parsed_command['product_name'],
                                parsed_command['quantity'],
                                user_id
                            )
                        elif command_type == 'delete':
                            inventory_result = db.delete_product(
                                parsed_command['product_name'],
                                user_id
                            )
            except Exception as e:
                print(f"Error processing inventory command from speech-to-text: {e}")
            
            # Add inventory processing result to response
            if inventory_result:
                result['inventory_processed'] = True
                result['inventory_result'] = inventory_result
                if inventory_result.get('success'):
                    result['message'] += ' Inventory updated successfully!'
                else:
                    result['message'] += ' However, inventory processing failed: ' + inventory_result.get('error', 'Unknown error')
        
        return jsonify(result)
    else:
        result = {
            'success': False,
            'text': '',
            'message': 'No audio file provided.'
        }
    
    return jsonify(result)

@app.route('/api/save-text', methods=['POST'])
@require_auth
def save_text_api():
    """API endpoint to save text from browser speech recognition and process inventory commands."""
    data = request.get_json()
    
    if data and 'text' in data:
        text = data['text'].strip()
        source = data.get('source', 'microphone')
        
        if text:
            # Save text to log file
            log_success = save_text_to_log(text, source)
            
            # Try to process as inventory command
            inventory_result = None
            try:
                from .utils import parse_inventory_command
                from .db.models import get_db
                from .auth_routes import require_auth
                
                # Parse the command
                parsed_command = parse_inventory_command(text)
                
                if 'error' not in parsed_command:
                    user_id = getattr(request, 'user', {}).get('user_id')
                    
                    if user_id:
                        # Execute the command
                        db = get_db()
                        command_type = parsed_command['command']
                        
                        if command_type == 'add':
                            inventory_result = db.add_product(
                                parsed_command['product_name'],
                                parsed_command['quantity'],
                                user_id
                            )
                        elif command_type == 'sell':
                            inventory_result = db.sell_product(
                                parsed_command['product_name'],
                                parsed_command['quantity'],
                                user_id
                            )
                        elif command_type == 'delete':
                            inventory_result = db.delete_product(
                                parsed_command['product_name'],
                                user_id
                            )
            except Exception as e:
                print(f"Error processing inventory command: {e}")
            
            if log_success:
                response_data = {
                    'success': True,
                    'message': 'Text saved successfully!',
                    'text': text
                }
                
                # Add inventory processing result if applicable
                if inventory_result:
                    response_data['inventory_processed'] = True
                    response_data['inventory_result'] = inventory_result
                    if inventory_result.get('success'):
                        response_data['message'] += ' Inventory updated successfully!'
                    else:
                        response_data['message'] += ' However, inventory processing failed: ' + inventory_result.get('error', 'Unknown error')
                
                return jsonify(response_data)
            else:
                return jsonify({
                    'success': False,
                    'message': 'Error saving text to log.',
                    'text': text
                })
        else:
            return jsonify({
                'success': False,
                'message': 'No text provided.',
                'text': ''
            })
    else:
        return jsonify({
            'success': False,
            'message': 'Invalid request data.',
            'text': ''
        })

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'message': 'Speech-to-text API is running'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
