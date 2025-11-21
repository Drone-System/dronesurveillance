from flask import Flask, render_template, redirect, request, url_for, flash, session, make_response
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import pandas as pd
import psycopg
import time
import os

# -------------------- Database --------------------
# Retry connection logic for Docker startup
max_retries = 5
retry_delay = 2

for attempt in range(max_retries):
    try:
        conn = psycopg.connect(
            host="db",
            dbname="db",
            user="postgres",
            password="mysecretpassword",
            port="5432",
            autocommit=True
        )
        print("Database connection successful!")
        break
    except psycopg.OperationalError as e:
        if attempt < max_retries - 1:
            print(f"Database connection attempt {attempt + 1} failed. Retrying in {retry_delay}s...")
            time.sleep(retry_delay)
        else:
            print(f"Failed to connect to database after {max_retries} attempts")
            raise

# -------------------- Flask setup --------------------
webserver = Flask(__name__)
webserver.secret_key = "your_secret_key_change_this_in_production"
webserver.config['SESSION_COOKIE_SECURE'] = False
webserver.config['SESSION_COOKIE_HTTPONLY'] = True
webserver.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

login_manager = LoginManager()
login_manager.init_app(webserver)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access this page."

# -------------------- User class --------------------
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    # Handle None or invalid user_id
    if user_id is None or user_id == "None" or user_id == "":
        return None
    
    try:
        # Convert to integer
        user_id = int(user_id)
        
        with conn.cursor() as cur:
            cur.execute("SELECT id, username FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
            if row:
                return User(id=row[0], username=row[1])
    except (ValueError, TypeError) as e:
        print(f"Invalid user_id format: {user_id} - {e}")
        return None
    except Exception as e:
        print(f"Error loading user: {e}")
        return None
    
    return None


@webserver.before_request
def debug_request():
    print(f">>> {request.method} {request.path} | Authenticated={current_user.is_authenticated}")

# -------------------- Routes --------------------
@webserver.route("/")
def index():
    """Root route - redirect based on auth status"""
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    return redirect(url_for("login"))

@webserver.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("home"))
    
    """Login and registration page"""
    # Clear any corrupted session data
    if not current_user.is_authenticated:
        session.clear()
    
    if request.method == "POST":
        action = request.form.get("action", "")
        
        # REGISTRATION
        if action == "register":

            with conn.cursor() as cur:
                cur.execute("select username from users;")
                rows = cur.fetchall()
                usernames = [r[0] for r in rows]

            username = request.form.get("create_username", "")
            password = request.form.get("create_password", "")
            
            if username in usernames:
                return render_template("login.html", error="Username already in use"), 400

            if not username or not password:
                return render_template("login.html", error="Username and password are required"), 400
            
            try:
                with conn.cursor() as cur:
                    # Call the stored procedure to create user
                    cur.execute("CALL create_user(%s, %s)", (username, password))
                    print(f"User '{username}' registered successfully")
                    
                return render_template("login.html", success="Registration successful! Please login."), 200
                
            except Exception as e:
                print(f"Registration error: {e}")
                import traceback
                traceback.print_exc()
                return render_template("login.html", error=f"Registration failed: {str(e)}"), 500
        
        # LOGIN
        elif action == "login":
            username = request.form.get("username", "")
            password = request.form.get("password", "")

            if not username or not password:
                return render_template("login.html", error="Username and password are required"), 400

            try:
                with conn.cursor() as cur:
                    # Check if verify_user function returns true
                    cur.execute("SELECT verify_user(%s::text, %s::text)", (username, password))
                    result = cur.fetchone()
                    
                    print(f"Login attempt for user '{username}': verify_user returned {result}")
                    
                    # Check if result exists and is True
                    if result and result[0] is True:
                        cur.execute("SELECT id, username FROM users WHERE username = %s", (username,))
                        user_row = cur.fetchone()
                        
                        if user_row:
                            user_id = user_row[0]
                            user = User(id=user_id, username=username)
                            
                            # Clear session before login to avoid conflicts
                            session.clear()
                            login_user(user, remember=True)
                            print(f"User '{username}' (ID: {user_id}) logged in successfully")
                            
                            next_page = request.args.get('next')
                            if next_page:
                                return redirect(next_page)
                            return redirect(url_for("home"))
                        else:
                            print(f"User '{username}' verified but not found in users table")
                    else:
                        print(f"verify_user returned False or NULL for user '{username}'")
                    
            except Exception as e:
                print(f"Login error: {e}")
                import traceback
                traceback.print_exc()
                return render_template("login.html", error="An error occurred during login"), 500

            return render_template("login.html", error="Invalid username or password"), 401

    return render_template("login.html")

@webserver.route("/logout")
def logout():
    print(f"[LOGOUT] Before logout: authenticated={current_user.is_authenticated}")
    
    logout_user()           # clear Flask-Login’s session
    session.clear()         # clear Flask session
    
    # Explicitly remove the remember-me cookie
    resp = make_response(redirect(url_for("login")))
    resp.delete_cookie("remember_token")
    
    print(f"[LOGOUT] After logout: authenticated={current_user.is_authenticated}")
    return resp


@webserver.route("/home")
@login_required
def home():
    """Protected home page"""
    try:
        data = pd.read_sql("select name from basestations where id =ANY(select basestation_id from basestations_to_groups where group_id =ANY(select group_id from users_to_groups where user_id = %s));", conn, params=[current_user.id],)
        items = data.to_dict("records")
        return render_template("index.html", items=items, username=current_user.username)
    except Exception as e:
        print(f"Error loading home page: {e}")
        logout_user()
        session.clear()
        return redirect(url_for("login"))

# -------------------- Error handlers --------------------
@webserver.errorhandler(404)
def not_found(e):
    # Only redirect authenticated users away from invalid pages
    if current_user.is_authenticated and request.endpoint not in ["logout", "login"]:
        return redirect(url_for("home"))
    return redirect(url_for("login"))



@webserver.errorhandler(401)
def unauthorized(e):
    """Handle unauthorized access"""
    return redirect(url_for("login"))

# -------------------- Run --------------------
if __name__ == "__main__":
    webserver.run(host="0.0.0.0", port=5000, debug=True)