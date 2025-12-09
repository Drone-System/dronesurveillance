# app.py - Flask web server
from flask import Flask, render_template, request, jsonify, redirect, url_for
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime

app = Flask(__name__)

# Database configuration
DB_CONFIG = {
    'dbname': 'db',
    'user': 'postgres',
    'password': 'mypass',
    'host': 'localhost',
    'port': 5432
}

# Camera type definitions with required fields
CAMERA_TYPES = {
    'ip_camera': {
        'name': 'IP Camera',
        'fields': [
            {'name': 'ip_address', 'label': 'IP Address', 'type': 'text', 'required': True},
            {'name': 'port', 'label': 'Port', 'type': 'number', 'required': True},
            {'name': 'username', 'label': 'Username', 'type': 'text', 'required': False},
            {'name': 'password', 'label': 'Password', 'type': 'password', 'required': False}
        ]
    },
    'usb_camera': {
        'name': 'USB Camera',
        'fields': [
            {'name': 'device_id', 'label': 'Device ID', 'type': 'number', 'required': True},
        ]
    },
}

# Drone type definitions with required fields
DRONE_TYPES = {
    'dji_tello_drone': {
        'name': 'DJI Tello Drone',
        'fields': [
            # {'name': 'serial_number', 'label': 'Serial Number', 'type': 'text', 'required': True},
            # {'name': 'model', 'label': 'Model', 'type': 'text', 'required': True},
            # {'name': 'controller_id', 'label': 'Controller ID', 'type': 'text', 'required': False}
        ]
    },
    'custom_drone': { #TBD With simulated drone
        'name': 'Custom Drone',
        'fields': [
            {'name': 'protocol', 'label': 'Communication Protocol', 'type': 'text', 'required': True},
            {'name': 'connection_params', 'label': 'Connection Parameters', 'type': 'text', 'required': True},
            {'name': 'firmware', 'label': 'Firmware Version', 'type': 'text', 'required': False}
        ]
    }
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def init_db():
    """Initialize database with cameras and drones tables"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Create cameras table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS cameras (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            camera_type VARCHAR(50) NOT NULL,
            config JSONB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create drones table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS drones (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            drone_type VARCHAR(50) NOT NULL,
            config JSONB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    cur.close()
    conn.close()

@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get cameras
    cur.execute('SELECT * FROM cameras ORDER BY created_at DESC')
    cameras = cur.fetchall()
    
    # Get drones
    cur.execute('SELECT * FROM drones ORDER BY created_at DESC')
    drones = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('index.html', 
                         cameras=cameras, 
                         drones=drones,
                         camera_types=CAMERA_TYPES,
                         drone_types=DRONE_TYPES)

@app.route('/add_camera')
def add_camera():
    return render_template('add_device.html', 
                         device_type='camera',
                         types=CAMERA_TYPES,
                         title='Add New Camera')

@app.route('/add_drone')
def add_drone():
    return render_template('add_device.html', 
                         device_type='drone',
                         types=DRONE_TYPES,
                         title='Add New Drone')

@app.route('/api/camera_fields/<camera_type>')
def get_camera_fields(camera_type):
    if camera_type in CAMERA_TYPES:
        return jsonify(CAMERA_TYPES[camera_type])
    return jsonify({'error': 'Invalid camera type'}), 400

@app.route('/api/drone_fields/<drone_type>')
def get_drone_fields(drone_type):
    if drone_type in DRONE_TYPES:
        return jsonify(DRONE_TYPES[drone_type])
    return jsonify({'error': 'Invalid drone type'}), 400

@app.route('/api/cameras', methods=['POST'])
def create_camera():
    data = request.json
    name = data.get('name')
    camera_type = data.get('camera_type')
    config = data.get('config', {})
    
    if not name or not camera_type:
        return jsonify({'error': 'Name and camera type are required'}), 400
    
    if camera_type not in CAMERA_TYPES:
        return jsonify({'error': 'Invalid camera type'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        'INSERT INTO cameras (name, camera_type, config) VALUES (%s, %s, %s) RETURNING id',
        (name, camera_type, json.dumps(config))
    )
    
    camera_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({'id': camera_id, 'message': 'Camera added successfully'}), 201

@app.route('/api/drones', methods=['POST'])
def create_drone():
    data = request.json
    name = data.get('name')
    drone_type = data.get('drone_type')
    config = data.get('config', {})
    
    if not name or not drone_type:
        return jsonify({'error': 'Name and drone type are required'}), 400
    
    if drone_type not in DRONE_TYPES:
        return jsonify({'error': 'Invalid drone type'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        'INSERT INTO drones (name, drone_type, config) VALUES (%s, %s, %s) RETURNING id',
        (name, drone_type, json.dumps(config))
    )
    
    drone_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({'id': drone_id, 'message': 'Drone added successfully'}), 201

@app.route('/api/cameras/<int:camera_id>', methods=['DELETE'])
def delete_camera(camera_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('DELETE FROM cameras WHERE id = %s', (camera_id,))
    
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({'message': 'Camera deleted successfully'}), 200

@app.route('/api/drones/<int:drone_id>', methods=['DELETE'])
def delete_drone(drone_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('DELETE FROM drones WHERE id = %s', (drone_id,))
    
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({'message': 'Drone deleted successfully'}), 200

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)


# ============================================================================
# templates/index.html
# ============================================================================
"""
<!DOCTYPE html>
<html>
<head>
    <title>Camera & Drone Management</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px; }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 30px; }
        h1 { color: #333; margin-bottom: 20px; }
        .button-group { display: flex; gap: 10px; }
        .btn { padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; border: none; cursor: pointer; display: inline-block; }
        .btn:hover { background: #0056b3; }
        .btn-success { background: #28a745; }
        .btn-success:hover { background: #218838; }
        .btn-danger { background: #dc3545; }
        .btn-danger:hover { background: #c82333; }
        
        .section { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 30px; }
        .section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 2px solid #e9ecef; }
        h2 { color: #333; }
        .count-badge { background: #007bff; color: white; padding: 4px 12px; border-radius: 12px; font-size: 0.9em; margin-left: 10px; }
        
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f8f9fa; font-weight: bold; }
        .type-badge { display: inline-block; padding: 4px 8px; background: #e9ecef; border-radius: 4px; font-size: 0.9em; }
        .camera-badge { background: #d1ecf1; color: #0c5460; }
        .drone-badge { background: #d4edda; color: #155724; }
        .no-items { text-align: center; padding: 40px; color: #666; }
        pre { font-size: 0.9em; background: #f8f9fa; padding: 8px; border-radius: 4px; max-width: 400px; overflow-x: auto; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Camera & Drone Management System</h1>
            <div class="button-group">
                <a href="/add_camera" class="btn">📷 Add New Camera</a>
                <a href="/add_drone" class="btn btn-success">🚁 Add New Drone</a>
            </div>
        </div>
        
        <!-- Cameras Section -->
        <div class="section">
            <div class="section-header">
                <h2>
                    Cameras
                    <span class="count-badge">{{ cameras|length }}</span>
                </h2>
            </div>
            
            {% if cameras %}
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Type</th>
                        <th>Configuration</th>
                        <th>Created</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for camera in cameras %}
                    <tr>
                        <td>{{ camera.id }}</td>
                        <td><strong>{{ camera.name }}</strong></td>
                        <td><span class="type-badge camera-badge">{{ camera_types[camera.camera_type].name }}</span></td>
                        <td><pre>{{ camera.config | tojson }}</pre></td>
                        <td>{{ camera.created_at.strftime('%Y-%m-%d %H:%M') }}</td>
                        <td>
                            <button class="btn btn-danger" onclick="deleteDevice('camera', {{ camera.id }})">Delete</button>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <div class="no-items">
                <p>No cameras registered yet. Click "Add New Camera" to get started.</p>
            </div>
            {% endif %}
        </div>
        
        <!-- Drones Section -->
        <div class="section">
            <div class="section-header">
                <h2>
                    Drones
                    <span class="count-badge">{{ drones|length }}</span>
                </h2>
            </div>
            
            {% if drones %}
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Type</th>
                        <th>Configuration</th>
                        <th>Created</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for drone in drones %}
                    <tr>
                        <td>{{ drone.id }}</td>
                        <td><strong>{{ drone.name }}</strong></td>
                        <td><span class="type-badge drone-badge">{{ drone_types[drone.drone_type].name }}</span></td>
                        <td><pre>{{ drone.config | tojson }}</pre></td>
                        <td>{{ drone.created_at.strftime('%Y-%m-%d %H:%M') }}</td>
                        <td>
                            <button class="btn btn-danger" onclick="deleteDevice('drone', {{ drone.id }})">Delete</button>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <div class="no-items">
                <p>No drones registered yet. Click "Add New Drone" to get started.</p>
            </div>
            {% endif %}
        </div>
    </div>
    
    <script>
        function deleteDevice(type, id) {
            const deviceName = type === 'camera' ? 'camera' : 'drone';
            if (confirm(`Are you sure you want to delete this ${deviceName}?`)) {
                fetch(`/api/${type}s/${id}`, { method: 'DELETE' })
                    .then(response => response.json())
                    .then(data => {
                        alert(data.message);
                        location.reload();
                    })
                    .catch(err => alert(`Error deleting ${deviceName}`));
            }
        }
    </script>
</body>
</html>
"""


# ============================================================================
# templates/add_device.html
# ============================================================================
"""
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #333; margin-bottom: 10px; }
        .subtitle { color: #666; margin-bottom: 30px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; color: #555; }
        input[type="text"], input[type="number"], input[type="password"], select {
            width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;
        }
        input[type="checkbox"] { margin-right: 5px; }
        .btn { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
        .btn:hover { background: #0056b3; }
        .btn-secondary { background: #6c757d; margin-right: 10px; text-decoration: none; display: inline-block; }
        .btn-secondary:hover { background: #545b62; }
        .btn-success { background: #28a745; }
        .btn-success:hover { background: #218838; }
        #dynamic-fields { margin-top: 20px; padding-top: 20px; border-top: 2px solid #e9ecef; }
        .required::after { content: " *"; color: red; }
        .actions { margin-top: 30px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>{{ title }}</h1>
        <p class="subtitle">Configure your new {{ device_type }}</p>
        
        <form id="device-form">
            <div class="form-group">
                <label for="name" class="required">{{ device_type|title }} Name</label>
                <input type="text" id="name" name="name" required placeholder="Enter a descriptive name">
            </div>
            
            <div class="form-group">
                <label for="type" class="required">{{ device_type|title }} Type</label>
                <select id="type" name="type" required>
                    <option value="">-- Select {{ device_type|title }} Type --</option>
                    {% for key, value in types.items() %}
                    <option value="{{ key }}">{{ value.name }}</option>
                    {% endfor %}
                </select>
            </div>
            
            <div id="dynamic-fields"></div>
            
            <div class="actions">
                <a href="/" class="btn btn-secondary">Cancel</a>
                <button type="submit" class="btn {% if device_type == 'drone' %}btn-success{% endif %}">
                    Add {{ device_type|title }}
                </button>
            </div>
        </form>
    </div>
    
    <script>
        const deviceType = "{{ device_type }}";
        const typeSelect = document.getElementById('type');
        const dynamicFields = document.getElementById('dynamic-fields');
        const form = document.getElementById('device-form');
        
        typeSelect.addEventListener('change', function() {
            const type = this.value;
            if (!type) {
                dynamicFields.innerHTML = '';
                return;
            }
            
            fetch(`/api/${deviceType}_fields/${type}`)
                .then(response => response.json())
                .then(data => {
                    let html = `<h3 style="margin-bottom: 15px;">${deviceType === 'camera' ? 'Camera' : 'Drone'} Configuration</h3>`;
                    
                    data.fields.forEach(field => {
                        html += `<div class="form-group">`;
                        html += `<label for="${field.name}" ${field.required ? 'class="required"' : ''}>${field.label}</label>`;
                        
                        if (field.type === 'checkbox') {
                            html += `<input type="checkbox" id="${field.name}" name="${field.name}">`;
                        } else {
                            html += `<input type="${field.type}" id="${field.name}" name="${field.name}" ${field.required ? 'required' : ''}>`;
                        }
                        
                        html += `</div>`;
                    });
                    
                    dynamicFields.innerHTML = html;
                })
                .catch(err => {
                    alert(`Error loading ${deviceType} fields`);
                    console.error(err);
                });
        });
        
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(form);
            const config = {};
            
            // Get dynamic fields
            const typeFields = dynamicFields.querySelectorAll('input');
            typeFields.forEach(field => {
                if (field.type === 'checkbox') {
                    config[field.name] = field.checked;
                } else {
                    config[field.name] = field.value;
                }
            });
            
            const data = {
                name: formData.get('name'),
                [`${deviceType}_type`]: formData.get('type'),
                config: config
            };
            
            fetch(`/api/${deviceType}s`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
                window.location.href = '/';
            })
            .catch(err => {
                alert(`Error adding ${deviceType}`);
                console.error(err);
            });
        });
    </script>
</body>
</html>
"""