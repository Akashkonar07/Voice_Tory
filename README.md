# Voice-Driven Inventory Management System

A modern web-based application that converts speech to text and includes a comprehensive voice-driven inventory management system for small and medium shopkeepers.

## Features

### Speech Recognition
- **Real-time Speech Recognition**: Convert live speech to text using Web Speech API
- **Audio File Processing**: Upload and process audio files for speech recognition
- **Text-to-Speech**: Convert text back to speech
- **Cross-browser Compatibility**: Works on Chrome, Edge, and Safari 14.1+
- **Python 3.13 Support**: Full compatibility with the latest Python version
- **Responsive Design**: Works on desktop and mobile devices

### Inventory Management
- **Voice Command Processing**: Process natural language commands like "Add 10 packets of milk", "Sold 5 soaps", "Delete 2 bottles of oil"
- **Real-time Inventory Updates**: Automatically update inventory levels based on voice commands
- **MongoDB Integration**: Store all inventory data, sales history, and command logs in MongoDB Atlas
- **Interactive Dashboard**: Visual representation of inventory with Chart.js
- **Sales Tracking**: Track all sales transactions with timestamps
- **Command Logging**: Maintain detailed logs of all inventory commands
- **Statistics & Analytics**: View total products, quantities, and sales statistics
- **Error Handling**: Comprehensive error handling for invalid commands

## Project Structure

```
├── src/
│   ├── backend/           # Flask application and API endpoints
│   │   ├── app.py        # Main Flask application
│   │   ├── inventory_routes.py  # Inventory API endpoints
│   │   └── textToSpeech.py  # Desktop GUI application
│   │   └── db/           # Database models and operations
│   │       ├── __init__.py
│   │       └── models.py # MongoDB models for inventory
│   ├── frontend/         # Frontend templates and static files
│   │   └── templates/    # HTML templates
│   │       └── index.html # Main application interface
│   ├── utils/           # Utility functions and helpers
│   │   └── parser.py    # Voice command parser
│   └── compatibility/   # Python 3.13 compatibility modules
│       ├── aifc.py      # Mock aifc module
│       └── audioop.py   # Mock audioop module
├── config/              # Configuration files
│   ├── config.py       # Application configuration
│   ├── requirements.txt # Python dependencies
│   └── .env.example    # Environment variables template
├── data/               # Data storage
│   ├── uploads/        # Uploaded audio files
│   └── text_logs/      # Speech recognition logs
├── docs/               # Documentation
├── tests/              # Test files
├── .venv/             # Virtual environment
└── main.py            # Main entry point
```

## Installation

### Prerequisites
- Python 3.13 or higher
- MongoDB Atlas account (for inventory management)
- Modern web browser (Chrome, Edge, or Safari 14.1+)

### Setup Steps

1. **Clone the repository** (if applicable)
2. **Create and activate virtual environment**:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r config/requirements.txt
   ```

4. **Install compatibility modules** (for Python 3.13):
   ```bash
   copy src\compatibility\aifc.py .venv\Lib\site-packages\
   copy src\compatibility\audioop.py .venv\Lib\site-packages\
   ```

5. **Set up MongoDB Atlas**:
   - Create a MongoDB Atlas account at [https://www.mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
   - Create a new cluster and database named `inventory_management`
   - Get your connection string from the Atlas dashboard
   - Set up environment variables:
   ```bash
   copy config\.env.example .env
   # Edit .env with your MongoDB connection string:
   MONGODB_URI=mongodb+srv://your_username:your_password@your_cluster.mongodb.net/inventory_management?retryWrites=true&w=majority
   ```

6. **Set up additional environment variables**:
   ```bash
   FLASK_ENV=development
   FLASK_DEBUG=True
   SECRET_KEY=your_secret_key_here
   ```

## Usage

### Web Application

1. **Start the Flask server**:
   ```bash
   python main.py
   ```

2. **Open your browser** and navigate to `http://localhost:5000`

3. **Use the application**:
   - Click "Start Listening" to begin real-time speech recognition
   - Upload audio files for batch processing
   - View recognition history and logs

### Inventory Management

The system now includes a comprehensive voice-driven inventory management system:

#### Voice Commands
Use natural language commands to manage your inventory:

- **Add products**: "Add 10 packets of milk", "Add 25 apples"
- **Record sales**: "Sold 5 soaps", "Sold 3 bottles of water"
- **Delete items**: "Delete 2 bottles of oil", "Delete 1 chocolate bar"

#### Dashboard Features
- **Real-time Inventory Display**: View current product quantities
- **Interactive Charts**: Visual representation of inventory levels
- **Sales Statistics**: Track total sales and product performance
- **Command History**: View all processed inventory commands
- **Error Handling**: Clear feedback for invalid commands

#### API Endpoints
The system provides several API endpoints for inventory management:

- `POST /api/inventory/command` - Process inventory commands
- `GET /api/inventory/inventory` - Get current inventory
- `GET /api/inventory/sales` - Get sales history
- `GET /api/inventory/logs` - Get command logs
- `GET /api/inventory/stats` - Get inventory statistics
- `GET /api/inventory/examples` - Get command examples
- `GET /api/inventory/health` - Health check

### Desktop GUI Application

Run the Tkinter-based desktop application:
```bash
python src/backend/textToSpeech.py
```

## API Endpoints

- `GET /` - Main web interface
- `POST /api/speech-to-text` - Convert audio file to text
- `POST /api/save-text` - Save recognized text from browser
- `GET /api/health` - Health check endpoint

## Browser Compatibility

- **Chrome**: Full support
- **Edge**: Full support
- **Safari**: Version 14.1 and above
- **Firefox**: Limited support (Web Speech API not fully implemented)

## Troubleshooting

### Common Issues

1. **Microphone Access Denied**:
   - Ensure you grant microphone permissions when prompted
   - Check browser settings for microphone access

2. **Import Errors**:
   - Verify compatibility modules are installed in virtual environment
   - Check all dependencies are installed correctly

3. **CORS Issues**:
   - The application includes CORS support by default
   - Ensure the server is running on the correct port

4. **Audio File Processing**:
   - Supported formats: WAV, MP3, OGG, FLAC, M4A, WMA
   - Maximum file size: 16MB

## Development

### Adding New Features

1. Backend changes go in `src/backend/`
2. Frontend changes go in `src/frontend/templates/`
3. Utility functions go in `src/utils/`
4. Configuration changes go in `config/`

### Testing

Run tests from the project root:
```bash
python -m pytest tests/
```

## License

This project is open source and available under the MIT License.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Support

For issues and questions, please check the documentation or create an issue in the repository.
