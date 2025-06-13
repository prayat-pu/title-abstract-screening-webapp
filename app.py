from flask import Flask, render_template, redirect, url_for, request, jsonify, send_file, session
import pandas as pd
import os
from datetime import datetime
import json
import re
from werkzeug.utils import secure_filename
import time

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a random secret key
app.static_folder = 'static' 

# Configuration for file upload
UPLOAD_FOLDER = 'upload'
ALLOWED_EXTENSIONS = {'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('export', exist_ok=True)

# Initialize checkbox data storage
checkbox_data = {}
# Global variables for data storage
df = None
checkbox_data = {}
dynamic_fields = []

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_dynamic_fields(df):
    """Extract dynamic fields from the CSV columns"""
    # Get all columns except Title, Abstract, and Related
    excluded_cols = ['Title', 'Abstract', 'Related']
    dynamic_cols = [col for col in df.columns if col not in excluded_cols]
    
    # Check if these are boolean/checkbox fields
    valid_dynamic_fields = []
    for col in dynamic_cols:
        # Check if the column contains Yes/No or boolean values
        unique_values = df[col].dropna().unique()
        if len(unique_values) <= 2:
            # Convert to lowercase for comparison
            lower_values = [str(v).lower() for v in unique_values]
            if all(v in ['yes', 'no', 'true', 'false', '1', '0', ''] for v in lower_values):
                valid_dynamic_fields.append(col)
    
    return valid_dynamic_fields

# Initialize or load existing checkbox data
def init_checkbox_data():
    """Initialize checkbox data based on loaded CSV"""
    global checkbox_data, dynamic_fields, df
    
    if df is None:
        return
    
    checkbox_data = {}
    for i in range(len(df)):
        row_data = {
            'related': None,  # Will be set from CSV if available
        }
        
        # Check if Related column exists and has value
        if 'Related' in df.columns:
            related_value = df.iloc[i]['Related']
            if pd.notna(related_value) and str(related_value).lower() in ['yes', 'no']:
                row_data['related'] = str(related_value).lower()
        
        # Add dynamic fields
        for field in dynamic_fields:
            if field in df.columns:
                value = df.iloc[i][field]
                if pd.notna(value):
                    # Convert Yes/No to boolean
                    row_data[field.lower()] = str(value).lower() == 'yes'
                else:
                    row_data[field.lower()] = False
            else:
                row_data[field.lower()] = False
        
        checkbox_data[i] = row_data


@app.route('/')
def index():
    """Redirect to the first entry"""
    return render_template('upload.html')



@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    global df, dynamic_fields
    
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Save file in chunks to prevent timeout
            file.save(filepath)

            
            try:
                # Load the CSV file with low_memory=False to prevent dtype warnings
                df = pd.read_csv(filepath, low_memory=False)
    
                
                # Validate required columns
                required_cols = ['Title', 'Abstract']
                if not all(col in df.columns for col in required_cols):
                    os.remove(filepath)  # Clean up uploaded file
                    return jsonify({'error': 'CSV must contain Title and Abstract columns'}), 400
                
                # Extract dynamic fields
                dynamic_fields = extract_dynamic_fields(df)
                
                # Initialize checkbox data
                init_checkbox_data()
                
                # Store filename in session
                session['current_file'] = filename
                
                # Clean up old uploaded files (optional)
                for old_file in os.listdir(app.config['UPLOAD_FOLDER']):
                    if old_file != filename:
                        try:
                            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], old_file))
                        except:
                            pass
                
                return jsonify({
                    'success': True,
                    'total_entries': len(df),
                    'dynamic_fields': dynamic_fields
                })
                
            except Exception as e:
                if os.path.exists(filepath):
                    os.remove(filepath)
                return jsonify({'error': f'Error reading CSV: {str(e)}'}), 400
        
        return jsonify({'error': 'Invalid file type'}), 400
        
    except Exception as e:
        app.logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': 'Server error during upload'}), 500

@app.route('/viewer')
def viewer():
    """Redirect to the first entry"""
    global df, dynamic_fields

    if df is None:
        filename = session['current_file']
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        df = pd.read_csv(filepath, low_memory=False)
        # Extract dynamic fields
        dynamic_fields = extract_dynamic_fields(df)
        
        # Initialize checkbox data
        init_checkbox_data()
        return redirect(url_for('index'))

    current_index = df.loc[(df['Related']=='yes') | (df['Related']=='no')].index[-1]
    return redirect(url_for('show_entry', entry_id=current_index))

@app.route('/entry/<int:entry_id>')
def show_entry(entry_id):
    """Display a single entry with navigation"""
    global df, dynamic_fields
    if df is None:
        filename = session['current_file']
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        df = pd.read_csv(filepath, low_memory=False)
        # Extract dynamic fields
        dynamic_fields = extract_dynamic_fields(df)
        
        # Initialize checkbox data
        init_checkbox_data()

    # Ensure entry_id is within bounds
    if entry_id < 0 or entry_id >= len(df):
        return redirect(url_for('show_entry', entry_id=0))
    
    # Get the current entry
    entry = df.iloc[entry_id]
    
    # Get checkbox state for this entry
    entry_checkbox_data = checkbox_data.get(entry_id, {
        'related': None,
    })

     # Add dynamic fields to checkbox data if not present
    for field in dynamic_fields:
        if field.lower() not in entry_checkbox_data:
            entry_checkbox_data[field.lower()] = False
    
    # Get search terms from session
    search_terms = session.get('search_terms', [])
    
    # Determine navigation availability
    has_prev = entry_id > 0
    has_next = entry_id < len(df) - 1
    
    return render_template('viewer.html',
                         title=entry['Title'],
                         abstract=entry['Abstract'],
                         entry_id=entry_id,
                         total_entries=len(df),
                         has_prev=has_prev,
                         has_next=has_next,
                         checkbox_state=entry_checkbox_data,
                         search_terms=json.dumps(search_terms),
                         dynamic_fields=dynamic_fields)

@app.route('/save_checkbox', methods=['POST'])
def save_checkbox():
    """Save checkbox state for an entry"""
    data = request.json
    entry_id = data.get('entry_id')
    
    if entry_id is not None and 0 <= entry_id < len(df):
        # Build checkbox data
        new_data = {
            'related': data.get('related'),
        }
        
        # Add dynamic fields
        for field in dynamic_fields:
            field_key = field.lower()
            new_data[field_key] = data.get(field_key, False)
        
        checkbox_data[entry_id] = new_data
        return jsonify({'status': 'success'})
    
    return jsonify({'status': 'error'}), 400

@app.route('/save_search_terms', methods=['POST'])
def save_search_terms():
    """Save search terms to session"""
    data = request.json
    search_terms = data.get('search_terms', [])
    session['search_terms'] = search_terms
    return jsonify({'status': 'success'})

@app.route('/export_csv')
def export_csv():
    """Export checkbox data to CSV"""
    # Create a list to store the export data
    global df
    export_data = []
    
    for i in range(len(df)):
        entry = df.iloc[i]
        checkbox_state = checkbox_data.get(i, {})

        row_data = {
            'Title': entry['Title'],
            'Abstract': entry['Abstract'],
            'Related': checkbox_state.get('related', '') or '',
        }

        # Add dynamic fields
        for field in dynamic_fields:
            field_key = field.lower()
            value = checkbox_state.get(field_key, False)
            row_data[field] = 'Yes' if value else 'No'
        
        export_data.append(row_data)
    
    # Create DataFrame and save to CSV
    export_df = pd.DataFrame(export_data)
    # Count existing files in export folder
    export_dir = 'export'
    existing_files = [f for f in os.listdir(export_dir) if f.endswith('.csv')]
    # Determine next count number
    next_count = len(existing_files) + 1
    filename = f'checkbox_data_{next_count}.csv'
    filepath = os.path.join(os.getcwd()+'/export/', filename)
    export_df.to_csv(filepath, index=False)
    
    return send_file(filepath, as_attachment=True, download_name=filename)

@app.route('/prev/<int:entry_id>')
def prev_entry(entry_id):
    """Navigate to previous entry"""
    new_id = max(0, entry_id - 1)
    return redirect(url_for('show_entry', entry_id=new_id))

@app.route('/next/<int:entry_id>')
def next_entry(entry_id):
    """Navigate to next entry"""
    global df
    new_id = min(len(df) - 1, entry_id + 1)
    return redirect(url_for('show_entry', entry_id=new_id))

if __name__ == '__main__':
    # Run the Flask app
    print("Starting Flask application...")
    # print(f"Loaded {len(df)} entries")
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
