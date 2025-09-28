from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from .inventory_routes import inventory_bp

app = Flask(__name__, template_folder='../frontend/templates')
CORS(app)  # Enable CORS for all routes

# Register inventory blueprint
app.register_blueprint(inventory_bp)

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
            'text': '',
            'message': f'Error processing audio file: {e}'
        }

@app.route('/')
def index():
    """Serve the main page."""
    return render_template('index.html')

@app.route('/api/speech-to-text', methods=['POST'])
def speech_to_text_api():
    """API endpoint for speech-to-text conversion from audio files only."""
    if 'audio_file' in request.files:
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
            
            return jsonify(result)
        else:
            result = {
                'success': False,
                'text': '',
                'message': 'No audio file provided.'
            }
    else:
        result = {
            'success': False,
            'text': '',
            'message': 'Please upload an audio file. Microphone recording is handled by the browser.'
        }
    
    return jsonify(result)

@app.route('/api/save-text', methods=['POST'])
def save_text_api():
    """API endpoint to save text from browser speech recognition."""
    data = request.get_json()
    
    if data and 'text' in data:
        text = data['text'].strip()
        source = data.get('source', 'microphone')
        
        if text:
            # Save text to log file
            success = save_text_to_log(text, source)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Text saved successfully!',
                    'text': text
                })
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
