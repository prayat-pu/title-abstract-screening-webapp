from flask import Flask, render_template, redirect, url_for, request, jsonify, send_file, session
import pandas as pd
import os
from datetime import datetime
import json
import re

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a random secret key

# Sample data - replace this with your actual DataFrame loading
def load_data():
    """
    Load your pandas DataFrame here.
    This example creates sample data, but you should replace it with:
    df = pd.read_csv('your_file.csv')  # or any other data source
    """
    return pd.read_csv('./data/monitor_papers.csv')

# Load the DataFrame globally
df = load_data()

# Initialize checkbox data storage
checkbox_data = {}

# Initialize or load existing checkbox data
def init_checkbox_data():
    global checkbox_data
    for i in range(len(df)):
        if i not in checkbox_data:
            checkbox_data[i] = {
                'related': None,  # 'yes' or 'no'
                'detect': False,
                'monitor': False,
                'analyze': False
            }

init_checkbox_data()

@app.route('/')
def index():
    """Redirect to the first entry"""
    return redirect(url_for('show_entry', entry_id=0))

@app.route('/entry/<int:entry_id>')
def show_entry(entry_id):
    """Display a single entry with navigation"""
    # Ensure entry_id is within bounds
    if entry_id < 0 or entry_id >= len(df):
        return redirect(url_for('show_entry', entry_id=0))
    
    # Get the current entry
    entry = df.iloc[entry_id]
    
    # Get checkbox state for this entry
    entry_checkbox_data = checkbox_data.get(entry_id, {
        'related': None,
        'detect': False,
        'monitor': False,
        'analyze': False
    })
    
    # Get search terms from session
    search_terms = session.get('search_terms', [])
    
    # Determine navigation availability
    has_prev = entry_id > 0
    has_next = entry_id < len(df) - 1
    
    return render_template('index.html',
                         title=entry['Title'],
                         abstract=entry['Abstract'],
                         entry_id=entry_id,
                         total_entries=len(df),
                         has_prev=has_prev,
                         has_next=has_next,
                         checkbox_state=entry_checkbox_data,
                         search_terms=json.dumps(search_terms))

@app.route('/save_checkbox', methods=['POST'])
def save_checkbox():
    """Save checkbox state for an entry"""
    data = request.json
    entry_id = data.get('entry_id')
    
    if entry_id is not None and 0 <= entry_id < len(df):
        checkbox_data[entry_id] = {
            'related': data.get('related'),
            'detect': data.get('detect', False),
            'monitor': data.get('monitor', False),
            'analyze': data.get('analyze', False)
        }
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
    export_data = []
    
    for i in range(len(df)):
        entry = df.iloc[i]
        checkbox_state = checkbox_data.get(i, {
            'related': None,
            'detect': False,
            'monitor': False,
            'analyze': False
        })
        
        export_data.append({
            'Title': entry['Title'],
            'Abstract': entry['Abstract'],
            'Related': checkbox_state['related'] or '',
            'Detect': 'Yes' if checkbox_state['detect'] else 'No',
            'Monitor': 'Yes' if checkbox_state['monitor'] else 'No',
            'Analyze': 'Yes' if checkbox_state['analyze'] else 'No'
        })
    
    # Create DataFrame and save to CSV
    export_df = pd.DataFrame(export_data)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'checkbox_data_{timestamp}.csv'
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
    new_id = min(len(df) - 1, entry_id + 1)
    return redirect(url_for('show_entry', entry_id=new_id))


if __name__ == '__main__':
    # Run the Flask app
    print("Starting Flask application...")
    print(f"Loaded {len(df)} entries")
    app.run(debug=True, port=5000)