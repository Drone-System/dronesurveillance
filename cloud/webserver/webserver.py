from flask import Flask, render_template, redirect, request, url_for, flash, session, make_response, jsonify, Response
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import pandas as pd
import psycopg
import time
import os
import ssl
import grpc
import ServerBaseStation_pb2, ServerBaseStation_pb2_grpc
import uuid
import asyncio
from threading import Thread
import redis
import re
import base64

# -------------------- Database --------------------
# Retry connection logic for Docker startup
max_retries = 5
retry_delay = 2

channel = grpc.aio.insecure_channel('localhost:50051')
stub = ServerBaseStation_pb2_grpc.WebserverDroneCommuncationDetailsStub(channel)

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

#--------------------- Redis setup --------------------

try:
    r = redis.Redis(host='red', port=6379, db=0, socket_connect_timeout=5)
    r.ping()
    print("Connected to Redis successfully!")
except redis.ConnectionError as e:
    print(f"ERROR: Cannot connect to Redis server at localhost:6379")
    print(f"Details: {e}")
    print("\nPlease start Redis first:")
    print("  - Ubuntu/Debian: sudo systemctl start redis-server")
    print("  - Docker: docker run -d -p 6379:6379 redis")
    print("  - macOS: brew services start redis")
    exit(1)


# -------------------- Flask setup --------------------
webserver = Flask(__name__)
webserver.secret_key = "your_secret_key_change_this_in_production"
webserver.config['SESSION_COOKIE_SECURE'] = True
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

def user_has_access(basestation_id: int, admin: bool=False) -> bool:
    user_id = current_user.id
    string = "SELECT COUNT(1) FROM users_to_basestations \
                            WHERE user_id=%s::integer AND basestation_id=%s::integer"
    if admin:
        string += " AND owner=TRUE"

    data = pd.read_sql(string, conn, params=[user_id, basestation_id])
    has_access = count_bs = data.to_dict()["count"][0] == 1

    return has_access

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
    print(f"[LOGOUT] Before logout: authenticated={current_user.is_authenticated}", flush=True)
    
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
        data = pd.read_sql("select id, name from basestations \
                INNER JOIN users_to_basestations ON basestations.id=users_to_basestations.basestation_id \
                where users_to_basestations.user_id=%s;", conn, params=[current_user.id],)
        items = data.to_dict("records")
        print(items, current_user.id, flush=True)
        return render_template("index.html", items=items, username=current_user.username)
    except Exception as e:
        print(f"Error loading home page: {e}")
        logout_user()
        session.clear()
        return redirect(url_for("login"))

@webserver.route("/basestation/add", methods=['GET', 'POST'])
@login_required
def add_basestation():
    # check if user is allowed to request drones from that base station
    # data = pd.read_sql("select id, name from basestations where id =ANY(select basestation_id from basestations_to_groups where group_id =ANY(select group_id from users_to_groups where user_id = %s));", conn, params=[current_user.id],)

    # basestations = pd.read_sql("select id, name from basestations where id = %s::integer", conn, params=[basestation_id],)
    # basestation_info = basestations.to_dict("records")[0]
    if request.method == 'POST':
        id = request.form.get("bsid")
        password = request.form.get("bspass")
        
        data = pd.read_sql("select count(*) from basestations where id=%s::integer", conn, params=[id,])
        count_bs = data.to_dict()["count"][0]
        
        print(count_bs)
        if count_bs == 0:
            return render_template("addbasestationview.html", 
                error="No basestation with specified id. Please first connect a basestation.")
        data = pd.read_sql("select count(*) from users_to_basestations where basestation_id=%s::integer AND owner=TRUE", conn, params=[id,])
        count_bs = data.to_dict()["count"][0]
        if count_bs != 0:
            return render_template("addbasestationview.html", 
                error="Basestation already has a owner. Ask the owner for access.")

        print(id, password, flush=True)
        result = pd.read_sql("select verify_basestation(%s, %s::text)", conn, params=[id, password])

        print("RESULT", result, flush=True)





        # check if basestation id exists
        # check if id has already an owner
        # if not assign owner to current user
        # else Say it cant assign

        return redirect(url_for("home"))

    return render_template("addbasestationview.html")

@webserver.route("/basestation/<int:basestation_id>")
def basestation(basestation_id):
    if not user_has_access(basestation_id):
        return "Unauthorized"

    basestations = pd.read_sql("select id, name from basestations where id = %s::integer", conn, params=[basestation_id],)
    basestation_info = basestations.to_dict("records")[0]

    print("\n\n\n\n", flush=True)
    print(basestation_info, flush=True)
    print("\n\n\n\n", flush=True)

    return render_template("basestationview.html", basestation=basestation_info, admin=user_has_access(basestation_id, True))

@webserver.route("/basestation/<int:basestation_id>/drones")
async def droneview(basestation_id):
    if not user_has_access(basestation_id):
        return "Unauthorized"
    channel = grpc.aio.insecure_channel('proxy_server:50051')
    stub = ServerBaseStation_pb2_grpc.WebserverDroneCommuncationDetailsStub(channel)
    # check if user is allowed to request drones from that base station
    # data = pd.read_sql("select id, name from basestations where id = ")
    
    drones = await stub.RequestAvailableDrones(ServerBaseStation_pb2.AvailableDroneRequest(basestation_id=basestation_id))

    if drones.info:
        return render_template("droneview.html", basestation_id=basestation_id, drones = drones.info)
    else:
        return "NO DRONES AVAILABLE"

@webserver.route("/basestation/<int:basestation_id>/drones/<drone_id>")
async def dronestream(basestation_id, drone_id):  
    # check if user is allowed to request drones from that base station
    # data = pd.read_sql("select id, name from basestations where id = ")
    
    return render_template("dronestream.html", basestation_id=basestation_id, drone_id = str(drone_id))

@webserver.route("/basestation/<int:basestation_id>/adduser", methods=['GET', 'POST'])
def basestation_adduser(basestation_id):
    if not user_has_access(basestation_id, True):
        return "Unauthorized"

    if request.method == 'POST':
        user = request.form.get("user")
        # add user to basestation

        # maybe add success feedback
        return redirect(url_for("basestation", basestation_id=basestation_id))

    return render_template("basestationadduserview.html")

@webserver.route("/basestation/<int:basestation_id>/cameras")
def basestation_cameras(basestation_id):  
    if not user_has_access(basestation_id):
        return "Unauthorized"
    streams = get_active_streams()
    return render_template("cameraview.html", streams=streams)


@webserver.route('/request', methods = ['POST'])
async def request_stream():
    channel = grpc.aio.insecure_channel('host.docker.internal:50051')
    stub = ServerBaseStation_pb2_grpc.WebserverDroneCommuncationDetailsStub(channel)

    print("request received", flush=True)

    data = request.get_json()

    drone_id = data['drone_id']
    basestation_id = data['basestation_id']

    if not user_has_access(basestation_id):
        print("Request Unauthorized", flush=True)
        return jsonify({})

    response = await stub.RequestDroneStream(ServerBaseStation_pb2.DroneStreamRequest(basestation_id= str(basestation_id) ,drone_id = str(drone_id)))
    reply = {"stream_id": response.stream_id, "offer": {"type": response.offer.type, "sdp": response.offer.sdp}}
    return jsonify(reply)


@webserver.route('/answer', methods = ['POST'])
async def answer_stream():
    channel = grpc.aio.insecure_channel('host.docker.internal:50051')
    stub = ServerBaseStation_pb2_grpc.WebserverDroneCommuncationDetailsStub(channel)

    data = request.get_json()
    print("answer received", data, flush=True)
    if not user_has_access(data['basestation_id']):
        print("Answer Unauthorized", flush=True)
        return jsonify({})

    answer = ServerBaseStation_pb2.StreamAnswer(basestation_id=data['basestation_id'],
                                                stream_id=data['stream_id'], 
                                                answer= ServerBaseStation_pb2.StreamDesc(type = data['answer']['type'],
                                                                                          sdp = data['answer']['sdp']))
    print("A", answer)
    await stub.Answer(answer)
    return jsonify({})


def get_active_streams():
    """
    Discover all active video streams by checking for latest_frame keys in Redis
    Only returns streams that have active heartbeats (updated within last 5 seconds)
    Returns a list of stream channel names
    """
    streams = []
    
    # Get all keys that match the pattern 'latest_frame_*'
    keys = r.keys('latest_frame_*')
    print("keys:",keys, flush=True)
    for key in keys:
        # Extract channel name from key (remove 'latest_frame_' prefix)
        key_str = key.decode('utf-8') if isinstance(key, bytes) else key
        channel_name = key_str.replace('latest_frame_', '')
        
        # Check if stream has an active heartbeat
        heartbeat_key = f'heartbeat_{channel_name}'
        heartbeat = r.get(heartbeat_key)
        
        # Only include streams with active heartbeat
        if heartbeat:
            # Extract camera identifier for display (e.g., "camera0" from "video_stream_camera0")
            camera_match = re.search(r'camera(\d+)', channel_name)
            if camera_match:
                camera_id = camera_match.group(1)
                display_name = f"Camera {camera_id}"
            else:
                # Use channel name as display name if no camera pattern found
                display_name = channel_name.replace('video_stream_', '').replace('_', ' ').title()
            
            streams.append({
                'channel': channel_name,
                'display_name': display_name,
                'camera_id': camera_match.group(1) if camera_match else channel_name
            })
    
    # Sort by camera ID or channel name
    streams.sort(key=lambda x: x['camera_id'])
    
    return streams

@webserver.route('/api/streams')
def api_streams():
    """API endpoint to get list of active streams"""
    streams = get_active_streams()
    return jsonify(streams)

def generate_frames(channel_name):
    """
    Generator function that yields video frames from a specific Redis channel
    
    Args:
        channel_name: Redis pub/sub channel name to subscribe to
    """
    pubsub = r.pubsub()
    pubsub.subscribe(channel_name)
    
    print(f"Subscribed to {channel_name}...")
    
    # Try to get the latest frame first for immediate display
    latest = r.get(f'latest_frame_{channel_name}')
    if latest:
        jpg_data = base64.b64decode(latest)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpg_data + b'\r\n')
    
    # Stream frames from pub/sub
    for message in pubsub.listen():
        if message['type'] == 'message':
            try:
                # Decode the base64 frame
                jpg_data = base64.b64decode(message['data'])
                
                # Yield frame in multipart format
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpg_data + b'\r\n')
            except Exception as e:
                print(f"Error processing frame from {channel_name}: {e}")
                continue


@webserver.route('/video_feed/<channel_name>')
def video_feed(channel_name):
    """Dynamic video streaming route for any channel"""
    return Response(generate_frames(channel_name),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

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
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain('cert.pem', 'key.pem')
    webserver.run('0.0.0.0', port=443, ssl_context=context, debug=True, use_reloader = False)