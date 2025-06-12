# title-abstract-screening-webapp

A Flask-based web application for viewing and annotating CSV data with dynamic checkbox fields, search functionality, and export capabilities.

## Features

- 📁 **CSV File Upload**: Upload CSV files through a drag-and-drop interface
- 🔍 **Search & Highlight**: Search multiple keywords with color-coded highlighting
- ✅ **Dynamic Checkboxes**: Automatically generates checkboxes based on CSV columns
- 📊 **Data Navigation**: Navigate through entries with Previous/Next buttons
- 💾 **Export Functionality**: Export annotated data with incremental file naming
- 🎨 **Clean UI**: Modern, responsive interface with three-panel layout

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

## Installation

1. **Clone the repository**
   ```bash
   git clone <your-repository-url>
   cd <your-project-directory>
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create required directories**
   ```bash
   mkdir uploads export templates
   ```

## Project Structure

```
your-project/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── gunicorn_config.py    # Gunicorn configuration (for deployment)
├── run.py               # Alternative server runner (Waitress)
├── README.md            # This file
├── templates/           # HTML templates
│   ├── upload.html     # File upload page
│   └── viewer.html     # Data viewer page
├── uploads/            # Temporary storage for uploaded CSVs
└── export/             # Storage for exported CSVs
```

## CSV File Requirements

Your CSV file must include:
- **Required columns**: `Title`, `Abstract`, `Related` 
- **Dynamic columns**: Any additional columns with Yes/No values will become checkboxes

Example CSV structure:
```csv
Title,Abstract,Related,Detect,Monitor,Analyze
"Paper Title 1","Abstract content here...","Yes","No","Yes","No"
"Paper Title 2","Another abstract...","No","","",""
```

## Running the Application

### Local Development

```bash
python app.py
```

The application will start on `http://localhost:10000`

### Production with Gunicorn

```bash
gunicorn app:app --timeout 120
```

Or with configuration file:
```bash
gunicorn app:app -c gunicorn_config.py
```

### Alternative with Waitress

```bash
python run.py
```

## Usage

1. **Upload CSV File**
   - Navigate to the home page
   - Drag and drop your CSV file or click "Browse Files"
   - Click "Upload and Process"

2. **View and Annotate Data**
   - Use Previous/Next buttons to navigate entries
   - Select "Related" Yes/No for each entry
   - If "Yes" is selected, additional checkboxes appear
   - Add search terms to highlight keywords in different colors

3. **Export Data**
   - Click "Export to CSV" to download annotated data
   - Files are saved as `checkbox_data_1.csv`, `checkbox_data_2.csv`, etc.

## Deployment on Render

1. **Create a new Web Service on Render**

2. **Connect your GitHub repository**

3. **Configure build settings**:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --timeout 120`

4. **Add environment variables**:
   ```
   PYTHON_VERSION = 3.9.0
   WEB_CONCURRENCY = 1
   ```

5. **Deploy**

## Troubleshooting

### Gunicorn Worker Timeout

If you encounter worker timeout errors, try:

1. Increase timeout in start command:
   ```bash
   gunicorn app:app --timeout 120 --workers 1 --threads 4
   ```

2. Use the provided `gunicorn_config.py`:
   ```bash
   gunicorn app:app -c gunicorn_config.py
   ```

3. Switch to Waitress server:
   ```bash
   python run.py
   ```

### Large File Uploads

For files larger than 16MB, modify `app.py`:
```python
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB
```

### Memory Issues

If processing large CSV files causes memory issues:
- Use `pd.read_csv(filepath, low_memory=False, chunksize=1000)`
- Implement pagination for very large datasets

## Configuration

### File Upload Settings

In `app.py`:
```python
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
```

### Session Configuration

Change the secret key in `app.py`:
```python
app.secret_key = 'your-secret-key-here'  # Change this!
```

## Features in Detail

### Dynamic Field Detection

The application automatically detects columns that can be used as checkboxes by:
1. Excluding Title, Abstract, and Related columns
2. Checking if column values are Yes/No or boolean
3. Creating checkboxes for valid columns

### Search and Highlight

- Add multiple search terms with custom colors
- Case-insensitive search
- Highlights persist across navigation
- Clear all highlights with one button

### Export Functionality

- Exports maintain all annotations
- Incremental file naming (checkbox_data_1.csv, checkbox_data_2.csv, etc.)
- Includes all dynamic fields in export

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with Flask web framework
- Uses Pandas for CSV processing
- Gunicorn/Waitress for production deployment
- Deployed on Render platform
