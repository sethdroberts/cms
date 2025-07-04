from flask import Flask, render_template, send_from_directory, flash, redirect, url_for, request, session
import os
from functools import wraps
from markdown import markdown
import yaml
import bcrypt

app = Flask(__name__)
app.secret_key = 'secret'

def get_data_path():
    if app.config['TESTING']:
        return os.path.join(os.path.dirname(__file__), 'tests', 'data')
    else:
        return os.path.join(os.path.dirname(__file__), 'cms', 'data')

def load_user_credentials():
    filename = 'users.yml'
    root_dir = os.path.dirname(__file__)
    if app.config['TESTING']:
        credentials_path = os.path.join(root_dir, 'tests', filename)
    else:
        credentials_path = os.path.join(root_dir, "cms", filename)

    with open(credentials_path, 'r') as file:
        return yaml.safe_load(file)
        
def valid_credentials(username, password):
    credentials = load_user_credentials()

    #When creating hashed passwords, remove the 'b' from beginning to decode them before saving them (avoids invalid salt error)

    if username in credentials:
        stored_password = credentials[username].encode('utf-8')
        return bcrypt.checkpw(password.encode('utf-8'), stored_password)
    else:
        return False

def logged_in():
    return session.get('username', "")
    
def require_logged_in(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not logged_in():
            flash('You must be signed in to do that')
            return redirect(url_for('show_signin_form'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@require_logged_in
def index():
    data_dir = get_data_path()
    files = [os.path.basename(path) for path in os.listdir(data_dir)]
    return render_template('index.html', files=files)
    
@app.route('/<file_name>')
@require_logged_in
def get_file(file_name):
    data_dir = get_data_path()
    file_path = os.path.join(data_dir, file_name)
    
    if os.path.isfile(file_path):
        if file_path.endswith(".md"):
            with open(file_path, 'r') as f:
                content = f.read()
                return render_template('markdown.html', content=markdown(content))
        return send_from_directory(data_dir, file_name)
    else:
        flash(f"{file_name} does not exist")
        return redirect(url_for('index'))

@app.route('/<file_name>/edit')
@require_logged_in
def edit_file(file_name):
    data_dir = get_data_path()
    file_path = os.path.join(data_dir, file_name)
    if os.path.isfile(file_path):
        with open(file_path, 'r') as f:
            content = f.read()
        return render_template('edit.html', file_name=file_name, file_content=content)
    else:
        flash(f"{file_name} does not exist")
        return redirect(url_for('index'))

@app.route('/<file_name>/edit', methods=['POST'])
@require_logged_in
def update_file(file_name):
    data_dir = get_data_path()
    file_path = os.path.join(data_dir, file_name)
    
    content = request.form['content']
    with open(file_path, 'w') as f:
        f.write(content)
    
    flash(f'{file_name} has been updated')
    return redirect(url_for('index'))
    
@app.route('/create')
@require_logged_in
def create_document():
    return render_template('create.html')
    
@app.route('/create', methods=['POST'])
@require_logged_in
def save_new_document():
    file_name = request.form['file_name'].strip()
    data_dir = get_data_path()
    file_path = os.path.join(data_dir, file_name)
    if not file_name:
        flash('A name is required')
        return render_template('create.html')
    elif os.path.exists(file_path):
        flash(f"{file_name} already exists.")
        return render_template('create.html')
    else:
        with open(file_path, 'w') as file:
                file.write("")
        flash(f'{file_name} was created')
        return redirect(url_for('index'))

@app.route('/<file_name>/delete')
@require_logged_in
def delete_file(file_name):
    data_dir = get_data_path()
    file_path = os.path.join(data_dir, file_name)
    if os.path.exists(file_path):
        os.remove(file_path)
        flash(f"{file_name} has been deleted!")
        return redirect(url_for('index'))
    else:
        flash('File does not exist')
        return redirect(url_for('index'))
        
@app.route("/users/signin")
def show_signin_form():
    return render_template('signin.html')

@app.route("/users/signin", methods=['POST'])
def signin():
    username = request.form.get('username')
    password = request.form.get('password')

    if valid_credentials(username, password):
        session['username'] = username
        flash("Welcome!")
        return redirect(url_for('index'))
    else:
        flash("Invalid credentials")
        return render_template('signin.html'), 422

@app.route("/users/signout", methods=['POST'])
def signout():
    session.pop('username', None)
    flash("You have been signed out.")
    return redirect(url_for('show_signin_form'))

if __name__ == "__main__":
    app.run(debug=True, port=8080)