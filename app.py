from flask import Flask, render_template, request, redirect, session, jsonify
import scratchattach as scratch3
import os
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Directory storage for demo
directories = {
    'profile': {},
    'project': {},
    'studio': {}  # Added studio support
}

# Current directory (initially set to a default profile "h1h2")
current_directory = {
    'type': 'profile',
    'value': 'h1h2'
}

# Function to authenticate user with Scratch API
def authenticate_user(username, password):
    try:
        print(f"Attempting to authenticate with Username: {username}")
        auth_session = scratch3.login(username, password)
        print("Authentication successful")
        return auth_session
    except Exception as e:
        print(f"Authentication failed: {e}")
        return None

# Fetch comments from the Scratch API
def fetch_scratch_comments(directory_type, directory_value):
    if directory_type == 'profile':
        url = f"https://scratch.mit.edu/site-api/comments/user/{directory_value}/"
    elif directory_type == 'project':
        url = f"https://scratch.mit.edu/site-api/comments/project/{directory_value}/"
    elif directory_type == 'studio':  # Added studio support
        url = f"https://scratch.mit.edu/site-api/comments/studio/{directory_value}/"
    else:
        return []

    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        comments = [comment.text.strip() for comment in soup.find_all('div', class_='content')]
        return comments
    except Exception as e:
        print(f"Error fetching comments from Scratch API: {e}")
        return []

@app.route('/')
def index():
    if 'username' in session:
        return redirect('/chat')
    return render_template('signin.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    print(f"Received login request with Username: {username}")
    
    auth_session = authenticate_user(username, password)
    if auth_session:
        session['username'] = username
        session['password'] = password
        print("Login successful, redirecting to chat...")
        return redirect('/chat')
    else:
        print("Login failed, rendering sign-in page again.")
        return render_template('signin.html', error="Invalid credentials or error occurred.")

@app.route('/chat')
def chat():
    if 'username' in session:
        return render_template('chat.html')
    return redirect('/')

@app.route('/fetch_comments', methods=['GET'])
def fetch_comments():
    if 'username' not in session or 'password' not in session:
        return jsonify({'message': 'User not authenticated'}), 403
    
    directory_type = current_directory['type']
    directory_value = current_directory['value']
    comments = fetch_scratch_comments(directory_type, directory_value)
    return jsonify({'comments': comments})

@app.route('/post_comment', methods=['POST'])
def post_comment():
    if 'username' not in session or 'password' not in session:
        return jsonify({'message': 'User not authenticated'}), 403
    
    data = request.get_json()
    comment_message = data.get('comment_message')
    
    # Get the username from the session
    username = session['username']
    
    # Prefix the comment with the username
    comment_message = f"{username}: {comment_message}"
    
    directory_type = current_directory['type']
    directory_value = current_directory['value']
    
    auth_session = authenticate_user(session['username'], session['password'])
    
    if not auth_session:
        return jsonify({'message': 'Session error'}), 500
    
    try:
        if directory_type == 'profile':
            user = auth_session.connect_user(directory_value)
            user.post_comment(comment_message)
        elif directory_type == 'project':
            project = auth_session.connect_project(directory_value)
            project.post_comment(comment_message)
        elif directory_type == 'studio':  # Added studio support
            studio = auth_session.connect_studio(directory_value)
            studio.post_comment(comment_message)
        else:
            raise ValueError('Invalid directory type')

        if directory_value not in directories[directory_type]:
            directories[directory_type][directory_value] = []
        directories[directory_type][directory_value].append(comment_message)
        return jsonify({'message': 'Comment posted successfully'})
    except Exception as e:
        return jsonify({'message': f'Failed to post comment: {e}'}), 500

@app.route('/change_directory', methods=['POST'])
def change_directory():
    data = request.get_json()
    directory_type = data.get('type')
    directory_value = data.get('value')

    if directory_type in ['profile', 'project', 'studio']:  # Added studio support
        current_directory['type'] = directory_type
        current_directory['value'] = directory_value
        return jsonify({'message': 'Directory changed successfully'})
    else:
        return jsonify({'message': 'Invalid directory type'}), 400

if __name__ == '__main__':
    app.run(debug=True)
