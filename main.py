import mysql.connector
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
import bcrypt

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# MySQL Database configuration
db_config = {
    'user': 'root',
    'password': 'J<RfM+se)9fR',
    'host': 'localhost',
    'database': 'todo_app'
}

# User data for login (for simplicity, still using a static dictionary here)
users = {
    'admin': {
        'username': 'admin',
        'password': bcrypt.hashpw(b'password', bcrypt.gensalt()).decode('utf-8'),
    }
}

# MySQL connection helper
def get_db_connection():
    return mysql.connector.connect(**db_config)

# Mock user class for Flask-Login
class User(UserMixin):
    def __init__(self, username):
        self.id = username

# Load user function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        return User(user_id)
    return None

# Helper function to read tasks from the database
def read_tasks():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM tasks ORDER BY display_order')  # Order by display_order
    tasks = cursor.fetchall()
    conn.close()
    return tasks


# Helper function to write tasks to the database
def write_task(task_text):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get the current max display_order
    cursor.execute('SELECT MAX(display_order) FROM tasks')
    max_order = cursor.fetchone()[0]
    if max_order is None:
        max_order = -1

    # Insert task with the next display order value
    cursor.execute('INSERT INTO tasks (text, display_order) VALUES (%s, %s)', (task_text, max_order + 1))
    conn.commit()
    conn.close()

def delete_task_from_db(task_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tasks WHERE id = %s', (task_id,))
    conn.commit()
    conn.close()

def toggle_task_completion(task_id, completed_status):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE tasks SET completed = %s WHERE id = %s', (completed_status, task_id))
    conn.commit()
    conn.close()

@app.route('/')
@login_required
def index():
    tasks = read_tasks()  # Read tasks from MySQL
    return render_template('index.html', tasks=tasks)

@app.route('/tasks', methods=['GET'])
@login_required
def get_tasks():
    tasks = read_tasks()  # Load tasks from MySQL
    return jsonify(tasks)

@app.route('/add', methods=['POST'])
@login_required
def add_task():
    task_text = request.form['task']
    write_task(task_text)  # Write task to MySQL
    tasks = read_tasks()  # Get updated tasks
    return jsonify(tasks)

@app.route('/delete/<int:index>', methods=['DELETE'])
@login_required
def delete_task(index):
    delete_task_from_db(index)  # Remove task from MySQL
    tasks = read_tasks()  # Get updated tasks
    return jsonify(tasks)

@app.route('/toggle/<int:task_id>', methods=['POST'])
@login_required
def toggle_task(task_id):
    tasks = read_tasks()
    task = next((t for t in tasks if t['id'] == task_id), None)  # Find task by ID
    if task:
        new_status = not task['completed']
        toggle_task_completion(task_id, new_status)  # Toggle completion in MySQL
        tasks = read_tasks()  # Get updated tasks
        return jsonify(tasks)
    else:
        return jsonify({'error': 'Invalid task ID'}), 400

@app.route('/reorder', methods=['POST'])
@login_required
def reorder_tasks():
    data = request.json
    from_task_id = data['fromIndex']  # Task IDs
    to_task_id = data['toIndex']

    # Fetch tasks from the database
    tasks = read_tasks()

    # Find the tasks to reorder based on the IDs
    from_task = next((task for task in tasks if task['id'] == from_task_id), None)
    to_task = next((task for task in tasks if task['id'] == to_task_id), None)

    if from_task and to_task:
        from_index = tasks.index(from_task)
        to_index = tasks.index(to_task)

        # Reorder tasks in Python
        task_to_move = tasks.pop(from_index)
        tasks.insert(to_index, task_to_move)

        # Update the tasks' order in the database by reassigning display_order values
        conn = get_db_connection()
        cursor = conn.cursor()
        for index, task in enumerate(tasks):
            cursor.execute('UPDATE tasks SET display_order = %s WHERE id = %s', (index, task['id']))
        conn.commit()
        conn.close()

        # Return updated tasks
        return jsonify(tasks)
    else:
        return jsonify({'error': 'Invalid task IDs'}), 400

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if user exists and password is correct
        user = users.get(username)
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            login_user(User(username))
            flash('Login successful', 'success')
            return redirect(url_for('index'))  # Redirect to tasks dashboard
        else:
            flash('Invalid credentials', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()  # This logs out the current user
    session.pop('_flashes', None)  # Clear previous flashed messages
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))  # Redirect to the login page

if __name__ == '__main__':
    app.run(debug=True)
