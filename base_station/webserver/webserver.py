# app.py - Flask web server
from flask import Flask, render_template, request, jsonify, redirect, url_for
import psycopg
from psycopg.rows import dict_row
import json
from datetime import datetime

app = Flask(__name__)

# Database configuration
DB_CONFIG = {
    'dbname': 'db',
    'user': 'postgres',
    'password': 'mypass',
    'host': 'db',
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
    return psycopg.connect(**DB_CONFIG)

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
    cur = conn.cursor(row_factory=dict_row)
    
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