from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_cors import CORS
from dotenv import load_dotenv
from pymongo import MongoClient
from a2wsgi import WSGIMiddleware
import socketio
import os
import logging
import bcrypt
import jwt
import secrets
from pathlib import Path
from datetime import datetime, timezone, timedelta
from functools import wraps
import ctypes
import uuid
import time
import random

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

JWT_SECRET = os.environ.get('JWT_SECRET', secrets.token_hex(32))
JWT_ALGORITHM = "HS256"

# Load C++ library
cpp_lib = ctypes.CDLL(str(ROOT_DIR / 'libparking.so'))
cpp_lib.calculateFee.argtypes = [ctypes.c_int, ctypes.c_bool]
cpp_lib.calculateFee.restype = ctypes.c_double
cpp_lib.generateQRCode.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
cpp_lib.generateQRCode.restype = None
cpp_lib.validateQRCode.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
cpp_lib.validateQRCode.restype = ctypes.c_bool
cpp_lib.calculateTimeDifference.argtypes = [ctypes.c_long, ctypes.c_long]
cpp_lib.calculateTimeDifference.restype = ctypes.c_int
cpp_lib.isSlotAvailable.argtypes = [ctypes.c_int, ctypes.c_int]
cpp_lib.isSlotAvailable.restype = ctypes.c_bool
cpp_lib.applyVIPDiscount.argtypes = [ctypes.c_double]
cpp_lib.applyVIPDiscount.restype = ctypes.c_double
cpp_lib.estimateCost.argtypes = [ctypes.c_int, ctypes.c_bool]
cpp_lib.estimateCost.restype = ctypes.c_double
cpp_lib.calculateSlotPriority.argtypes = [ctypes.c_double, ctypes.c_bool, ctypes.c_bool]
cpp_lib.calculateSlotPriority.restype = ctypes.c_double

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
mongo_client = MongoClient(mongo_url)
db = mongo_client[os.environ['DB_NAME']]

# Collections
parking_slots = db.parking_slots
vehicles = db.vehicles
reservations = db.reservations
payment_transactions = db.payment_transactions
sensor_data = db.sensor_data
users = db.users
login_attempts = db.login_attempts

# Create Flask app
flask_app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(flask_app, supports_credentials=True, origins=os.environ.get('CORS_ORIGINS', '*').split(','))

# Create Socket.IO server (async ASGI mode)
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ========== AUTH HELPERS ==========

def hash_password(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain, hashed):
    return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(user_id, email):
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
        "type": "access"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id):
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "type": "refresh"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def get_current_user():
    token = request.cookies.get('access_token')
    if not token:
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
    if not token:
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get('type') != 'access':
            return None
        user = users.find_one({"user_id": payload['sub']}, {"_id": 0, "password_hash": 0})
        return user
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        request.current_user = user
        return f(*args, **kwargs)
    return decorated

def check_brute_force(ip, email):
    identifier = f"{ip}:{email}"
    attempt = login_attempts.find_one({"identifier": identifier})
    if attempt and attempt.get('count', 0) >= 5:
        lockout_until = attempt.get('lockout_until')
        if lockout_until and datetime.now(timezone.utc).isoformat() < lockout_until:
            return False
        else:
            login_attempts.delete_one({"identifier": identifier})
    return True

def record_failed_attempt(ip, email):
    identifier = f"{ip}:{email}"
    attempt = login_attempts.find_one({"identifier": identifier})
    if attempt:
        new_count = attempt.get('count', 0) + 1
        update = {"$set": {"count": new_count}}
        if new_count >= 5:
            update["$set"]["lockout_until"] = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
        login_attempts.update_one({"identifier": identifier}, update)
    else:
        login_attempts.insert_one({"identifier": identifier, "count": 1})

def clear_failed_attempts(ip, email):
    login_attempts.delete_one({"identifier": f"{ip}:{email}"})

# ========== SEED & INIT ==========

def initialize_parking_data():
    if parking_slots.count_documents({}) == 0:
        slots = []
        for i in range(1, 51):
            slot_type = "VIP" if i <= 5 else ("EV" if i <= 15 else "Regular")
            slots.append({
                "slot_id": f"SLOT-{str(i).zfill(3)}",
                "slot_number": i,
                "type": slot_type,
                "status": "available",
                "vehicle_number": None,
                "floor": (i - 1) // 10 + 1,
                "zone": chr(65 + ((i - 1) % 5)),
                "lat": 40.7128 + (random.random() - 0.5) * 0.01,
                "lng": -74.0060 + (random.random() - 0.5) * 0.01
            })
        parking_slots.insert_many(slots)
        logger.info("Initialized 50 parking slots")
    if sensor_data.count_documents({}) == 0:
        sensors = []
        for i in range(1, 11):
            sensors.append({
                "sensor_id": f"SENSOR-{str(i).zfill(3)}",
                "zone": chr(65 + (i % 5)),
                "status": "active",
                "battery": random.randint(70, 100),
                "last_updated": datetime.now(timezone.utc).isoformat()
            })
        sensor_data.insert_many(sensors)
        logger.info("Initialized sensor data")

def seed_admin():
    admin_email = os.environ.get('ADMIN_EMAIL', 'admin@smartpark.com')
    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
    existing = users.find_one({"email": admin_email})
    if not existing:
        users.insert_one({
            "user_id": str(uuid.uuid4()),
            "email": admin_email,
            "name": "Admin",
            "password_hash": hash_password(admin_password),
            "role": "admin",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"Admin user seeded: {admin_email}")
    elif not verify_password(admin_password, existing['password_hash']):
        users.update_one({"email": admin_email}, {"$set": {"password_hash": hash_password(admin_password)}})

    # Create indexes
    users.create_index("email", unique=True)
    users.create_index("user_id", unique=True)
    login_attempts.create_index("identifier")

    # Write test credentials
    creds_path = ROOT_DIR / 'memory' / 'test_credentials.md'
    creds_path.parent.mkdir(parents=True, exist_ok=True)
    creds_path.write_text(f"""# Test Credentials
## Admin Account
- Email: {admin_email}
- Password: {admin_password}
- Role: admin

## Test User (register manually)
- Use /api/auth/register to create

## Auth Endpoints
- POST /api/auth/register
- POST /api/auth/login
- POST /api/auth/logout
- GET /api/auth/me
- POST /api/auth/refresh
""")

initialize_parking_data()
seed_admin()

# ========== SOCKET.IO EVENTS ==========

@sio.event
async def connect(sid, environ):
    logger.info(f"WebSocket client connected: {sid}")
    # Send initial slot data
    slots = list(parking_slots.find({}, {"_id": 0}).sort("slot_number", 1))
    stats = get_stats_data()
    await sio.emit('slots_update', {"slots": slots, "count": len(slots)}, to=sid)
    await sio.emit('stats_update', stats, to=sid)

@sio.event
async def disconnect(sid):
    logger.info(f"WebSocket client disconnected: {sid}")

@sio.event
async def request_slots(sid, data=None):
    slots = list(parking_slots.find({}, {"_id": 0}).sort("slot_number", 1))
    await sio.emit('slots_update', {"slots": slots, "count": len(slots)}, to=sid)

@sio.event
async def request_stats(sid, data=None):
    stats = get_stats_data()
    await sio.emit('stats_update', stats, to=sid)

def get_stats_data():
    total = parking_slots.count_documents({})
    occupied = parking_slots.count_documents({"status": "occupied"})
    reserved = parking_slots.count_documents({"status": "reserved"})
    available = parking_slots.count_documents({"status": "available"})
    total_vehicles_parked = vehicles.count_documents({"status": "parked"})
    total_revenue = 0
    for v in vehicles.find({"status": "exited", "total_fee": {"$exists": True}}):
        total_revenue += v.get('total_fee', 0)
    exited_count = vehicles.count_documents({"status": "exited"})
    vip_slots = parking_slots.count_documents({"type": "VIP"})
    vip_occupied = parking_slots.count_documents({"type": "VIP", "status": "occupied"})
    active_reservations = reservations.count_documents({"status": "active"})
    active_sensors = sensor_data.count_documents({"status": "active"})
    total_sensors = sensor_data.count_documents({})
    total_parked = vehicles.count_documents({})
    co2_saved = total_parked * 8 * 0.5
    return {
        "occupancy": {"total": total, "occupied": occupied, "reserved": reserved, "available": available,
                       "occupancy_rate": round((occupied / total * 100), 2) if total > 0 else 0},
        "vehicles": {"currently_parked": total_vehicles_parked, "total_processed": vehicles.count_documents({})},
        "revenue": {"total": round(total_revenue, 2),
                     "average_per_vehicle": round(total_revenue / max(1, exited_count), 2)},
        "vip": {"total_slots": vip_slots, "occupied": vip_occupied, "available": vip_slots - vip_occupied},
        "reservations": {"active": active_reservations, "total": reservations.count_documents({})},
        "sensors": {"active": active_sensors, "total": total_sensors,
                     "health_percentage": round((active_sensors / max(1, total_sensors)) * 100, 2)},
        "climate_impact": {"co2_saved_kg": round(co2_saved, 2),
                            "search_time_saved_hours": round(total_parked * 8 / 60, 2),
                            "vehicles_served": total_parked}
    }

async def broadcast_updates():
    """Broadcast slot and stats updates to all connected clients"""
    slots = list(parking_slots.find({}, {"_id": 0}).sort("slot_number", 1))
    stats = get_stats_data()
    await sio.emit('slots_update', {"slots": slots, "count": len(slots)})
    await sio.emit('stats_update', stats)

async def send_reservation_notification(user_id, message, reservation_id):
    """Send reservation notification to specific user"""
    await sio.emit('reservation_notification', {
        "message": message,
        "reservation_id": reservation_id,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

# ========== AUTH ROUTES ==========

@flask_app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    name = data.get('name', '')

    if not email or not password or not name:
        return jsonify({"error": "Email, password, and name are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    if users.find_one({"email": email}):
        return jsonify({"error": "Email already registered"}), 409

    user_id = str(uuid.uuid4())
    users.insert_one({
        "user_id": user_id,
        "email": email,
        "name": name,
        "password_hash": hash_password(password),
        "role": "user",
        "created_at": datetime.now(timezone.utc).isoformat()
    })

    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id)

    resp = make_response(jsonify({
        "user_id": user_id, "email": email, "name": name, "role": "user"
    }))
    resp.set_cookie('access_token', access_token, httponly=True, secure=False, samesite='Lax', max_age=86400, path='/')
    resp.set_cookie('refresh_token', refresh_token, httponly=True, secure=False, samesite='Lax', max_age=604800, path='/')
    return resp

@flask_app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    ip = request.remote_addr or '0.0.0.0'
    if not check_brute_force(ip, email):
        return jsonify({"error": "Too many failed attempts. Please try again in 15 minutes."}), 429

    user = users.find_one({"email": email}, {"_id": 0})
    if not user or not verify_password(password, user['password_hash']):
        record_failed_attempt(ip, email)
        return jsonify({"error": "Invalid email or password"}), 401

    clear_failed_attempts(ip, email)
    access_token = create_access_token(user['user_id'], email)
    refresh_token = create_refresh_token(user['user_id'])

    resp = make_response(jsonify({
        "user_id": user['user_id'], "email": user['email'],
        "name": user['name'], "role": user['role']
    }))
    resp.set_cookie('access_token', access_token, httponly=True, secure=False, samesite='Lax', max_age=86400, path='/')
    resp.set_cookie('refresh_token', refresh_token, httponly=True, secure=False, samesite='Lax', max_age=604800, path='/')
    return resp

@flask_app.route('/api/auth/logout', methods=['POST'])
def logout():
    resp = make_response(jsonify({"message": "Logged out"}))
    resp.delete_cookie('access_token', path='/')
    resp.delete_cookie('refresh_token', path='/')
    return resp

@flask_app.route('/api/auth/me', methods=['GET'])
def get_me():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Not authenticated"}), 401
    return jsonify(user)

@flask_app.route('/api/auth/refresh', methods=['POST'])
def refresh_token():
    token = request.cookies.get('refresh_token')
    if not token:
        return jsonify({"error": "No refresh token"}), 401
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get('type') != 'refresh':
            return jsonify({"error": "Invalid token type"}), 401
        user = users.find_one({"user_id": payload['sub']}, {"_id": 0, "password_hash": 0})
        if not user:
            return jsonify({"error": "User not found"}), 401
        new_access = create_access_token(user['user_id'], user['email'])
        resp = make_response(jsonify(user))
        resp.set_cookie('access_token', new_access, httponly=True, secure=False, samesite='Lax', max_age=86400, path='/')
        return resp
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return jsonify({"error": "Invalid refresh token"}), 401

# ========== PARKING API ROUTES ==========

@flask_app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()})

@flask_app.route('/api/slots/available', methods=['GET'])
def get_available_slots():
    slot_type = request.args.get('type', None)
    query = {"status": "available"}
    if slot_type and slot_type != "all":
        query["type"] = slot_type
    slots = list(parking_slots.find(query, {"_id": 0}).sort("slot_number", 1))
    return jsonify({"slots": slots, "count": len(slots)})

@flask_app.route('/api/slots/all', methods=['GET'])
def get_all_slots():
    slots = list(parking_slots.find({}, {"_id": 0}).sort("slot_number", 1))
    return jsonify({"slots": slots, "total": len(slots)})

@flask_app.route('/api/slots/<slot_id>', methods=['GET'])
def get_slot_details(slot_id):
    slot = parking_slots.find_one({"slot_id": slot_id}, {"_id": 0})
    if not slot:
        return jsonify({"error": "Slot not found"}), 404
    return jsonify(slot)

@flask_app.route('/api/vehicles/register', methods=['POST'])
def register_vehicle():
    data = request.json
    vehicle_number = data.get('vehicle_number')
    slot_id = data.get('slot_id')
    is_vip = data.get('is_vip', False)

    if not vehicle_number or not slot_id:
        return jsonify({"error": "Vehicle number and slot ID required"}), 400

    slot = parking_slots.find_one({"slot_id": slot_id})
    if not slot:
        return jsonify({"error": "Slot not found"}), 404
    if slot['status'] != 'available':
        return jsonify({"error": "Slot not available"}), 400

    qr_buffer = ctypes.create_string_buffer(100)
    cpp_lib.generateQRCode(vehicle_number.encode('utf-8'), slot_id.encode('utf-8'), qr_buffer)
    qr_code = qr_buffer.value.decode('utf-8')

    entry_time = int(time.time())
    user = get_current_user()
    vehicle_doc = {
        "vehicle_id": str(uuid.uuid4()),
        "vehicle_number": vehicle_number,
        "slot_id": slot_id,
        "entry_time": entry_time,
        "exit_time": None,
        "is_vip": is_vip,
        "qr_code": qr_code,
        "status": "parked",
        "user_id": user['user_id'] if user else None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    vehicles.insert_one(vehicle_doc)
    parking_slots.update_one({"slot_id": slot_id}, {"$set": {"status": "occupied", "vehicle_number": vehicle_number}})

    vehicle_doc.pop('_id', None)

    # Trigger async broadcast via background (non-blocking for sync Flask)
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(broadcast_updates())
        else:
            loop.run_until_complete(broadcast_updates())
    except RuntimeError:
        pass

    return jsonify({"success": True, "vehicle": vehicle_doc, "qr_code": qr_code})

@flask_app.route('/api/vehicles/<vehicle_number>', methods=['GET'])
def get_vehicle_details(vehicle_number):
    vehicle = vehicles.find_one({"vehicle_number": vehicle_number, "status": "parked"}, {"_id": 0})
    if not vehicle:
        return jsonify({"error": "Vehicle not found"}), 404
    current_time = int(time.time())
    minutes = cpp_lib.calculateTimeDifference(vehicle['entry_time'], current_time)
    fee = cpp_lib.calculateFee(minutes, vehicle['is_vip'])
    vehicle['current_fee'] = round(fee, 2)
    vehicle['parked_minutes'] = minutes
    return jsonify(vehicle)

@flask_app.route('/api/vehicles/<vehicle_number>/exit', methods=['POST'])
def vehicle_exit(vehicle_number):
    vehicle = vehicles.find_one({"vehicle_number": vehicle_number, "status": "parked"})
    if not vehicle:
        return jsonify({"error": "Vehicle not found"}), 404
    exit_time = int(time.time())
    minutes = cpp_lib.calculateTimeDifference(vehicle['entry_time'], exit_time)
    fee = cpp_lib.calculateFee(minutes, vehicle['is_vip'])
    vehicles.update_one(
        {"vehicle_number": vehicle_number, "status": "parked"},
        {"$set": {"exit_time": exit_time, "status": "exited", "total_fee": round(fee, 2), "parked_minutes": minutes}}
    )
    parking_slots.update_one({"slot_id": vehicle['slot_id']}, {"$set": {"status": "available", "vehicle_number": None}})

    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(broadcast_updates())
        else:
            loop.run_until_complete(broadcast_updates())
    except RuntimeError:
        pass

    return jsonify({"success": True, "vehicle_number": vehicle_number, "fee": round(fee, 2), "minutes": minutes})

@flask_app.route('/api/fee/calculate', methods=['POST'])
def calculate_fee():
    data = request.json
    minutes = data.get('minutes', 0)
    is_vip = data.get('is_vip', False)
    fee = cpp_lib.calculateFee(minutes, is_vip)
    return jsonify({"minutes": minutes, "is_vip": is_vip, "fee": round(fee, 2)})

@flask_app.route('/api/fee/estimate', methods=['POST'])
def estimate_parking_cost():
    data = request.json
    estimated_minutes = data.get('estimated_minutes', 60)
    is_vip = data.get('is_vip', False)
    cost = cpp_lib.estimateCost(estimated_minutes, is_vip)
    return jsonify({"estimated_minutes": estimated_minutes, "is_vip": is_vip, "estimated_cost": round(cost, 2)})

# ========== RESERVATION ROUTES ==========

@flask_app.route('/api/reservations/create', methods=['POST'])
def create_reservation():
    data = request.json
    vehicle_number = data.get('vehicle_number')
    slot_type = data.get('slot_type', 'Regular')
    is_vip = data.get('is_vip', False)
    duration_minutes = data.get('duration_minutes', 60)

    if not vehicle_number:
        return jsonify({"error": "Vehicle number required"}), 400

    query = {"status": "available"}
    if is_vip or slot_type == "VIP":
        query["type"] = "VIP"
    elif slot_type != "all":
        query["type"] = slot_type
    slot = parking_slots.find_one(query)
    if not slot:
        return jsonify({"error": "No slots available"}), 404

    reservation_id = str(uuid.uuid4())
    estimated_cost = cpp_lib.estimateCost(duration_minutes, is_vip)
    user = get_current_user()

    reservation_doc = {
        "reservation_id": reservation_id,
        "vehicle_number": vehicle_number,
        "slot_id": slot['slot_id'],
        "slot_type": slot['type'],
        "is_vip": is_vip,
        "duration_minutes": duration_minutes,
        "estimated_cost": round(estimated_cost, 2),
        "status": "active",
        "user_id": user['user_id'] if user else None,
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    reservations.insert_one(reservation_doc)
    parking_slots.update_one({"slot_id": slot['slot_id']}, {"$set": {"status": "reserved", "vehicle_number": vehicle_number}})

    reservation_doc.pop('_id', None)

    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(broadcast_updates())
        else:
            loop.run_until_complete(broadcast_updates())
    except RuntimeError:
        pass

    return jsonify({"success": True, "reservation": reservation_doc})

@flask_app.route('/api/reservations/<reservation_id>', methods=['GET'])
def get_reservation(reservation_id):
    reservation = reservations.find_one({"reservation_id": reservation_id}, {"_id": 0})
    if not reservation:
        return jsonify({"error": "Reservation not found"}), 404
    return jsonify(reservation)

@flask_app.route('/api/reservations/<reservation_id>/cancel', methods=['POST'])
def cancel_reservation(reservation_id):
    reservation = reservations.find_one({"reservation_id": reservation_id})
    if not reservation:
        return jsonify({"error": "Reservation not found"}), 404
    reservations.update_one({"reservation_id": reservation_id}, {"$set": {"status": "cancelled"}})
    parking_slots.update_one({"slot_id": reservation['slot_id']}, {"$set": {"status": "available", "vehicle_number": None}})

    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(broadcast_updates())
        else:
            loop.run_until_complete(broadcast_updates())
    except RuntimeError:
        pass

    return jsonify({"success": True, "message": "Reservation cancelled"})

# ========== RESERVATION HISTORY (AUTH REQUIRED) ==========

@flask_app.route('/api/reservations/history', methods=['GET'])
@auth_required
def get_reservation_history():
    user = request.current_user
    user_reservations = list(reservations.find(
        {"user_id": user['user_id']},
        {"_id": 0}
    ).sort("created_at", -1).limit(50))
    return jsonify({"reservations": user_reservations})

@flask_app.route('/api/vehicles/history', methods=['GET'])
@auth_required
def get_vehicle_history():
    user = request.current_user
    user_vehicles = list(vehicles.find(
        {"user_id": user['user_id']},
        {"_id": 0}
    ).sort("created_at", -1).limit(50))
    return jsonify({"vehicles": user_vehicles})

# ========== QR CODE ROUTES ==========

@flask_app.route('/api/qr/generate', methods=['POST'])
def generate_qr():
    data = request.json
    vehicle_number = data.get('vehicle_number')
    slot_id = data.get('slot_id')
    if not vehicle_number or not slot_id:
        return jsonify({"error": "Vehicle number and slot ID required"}), 400
    qr_buffer = ctypes.create_string_buffer(100)
    cpp_lib.generateQRCode(vehicle_number.encode('utf-8'), slot_id.encode('utf-8'), qr_buffer)
    return jsonify({"qr_code": qr_buffer.value.decode('utf-8')})

@flask_app.route('/api/qr/validate', methods=['POST'])
def validate_qr():
    data = request.json
    qr_code = data.get('qr_code')
    vehicle_number = data.get('vehicle_number')
    if not qr_code or not vehicle_number:
        return jsonify({"error": "QR code and vehicle number required"}), 400
    is_valid = cpp_lib.validateQRCode(qr_code.encode('utf-8'), vehicle_number.encode('utf-8'))
    return jsonify({"valid": bool(is_valid)})

# ========== ADMIN ROUTES ==========

@flask_app.route('/api/admin/statistics', methods=['GET'])
def get_statistics():
    return jsonify(get_stats_data())

@flask_app.route('/api/admin/occupancy-by-zone', methods=['GET'])
def get_occupancy_by_zone():
    zones = {}
    for slot in parking_slots.find({}, {"_id": 0}):
        zone = slot['zone']
        if zone not in zones:
            zones[zone] = {"total": 0, "occupied": 0, "available": 0, "reserved": 0}
        zones[zone]['total'] += 1
        if slot['status'] == 'occupied':
            zones[zone]['occupied'] += 1
        elif slot['status'] == 'available':
            zones[zone]['available'] += 1
        elif slot['status'] == 'reserved':
            zones[zone]['reserved'] += 1
    return jsonify({"zones": zones})

@flask_app.route('/api/admin/recent-activity', methods=['GET'])
def get_recent_activity():
    limit = int(request.args.get('limit', 10))
    recent = list(vehicles.find({}, {"_id": 0}).sort("created_at", -1).limit(limit))
    return jsonify({"activities": recent})

@flask_app.route('/api/admin/sensors', methods=['GET'])
def get_sensors():
    sensors = list(sensor_data.find({}, {"_id": 0}))
    return jsonify({"sensors": sensors})

# ========== PAYMENT ROUTES ==========

@flask_app.route('/api/payment/create-checkout', methods=['POST'])
def create_payment_checkout():
    data = request.json
    amount = data.get('amount')
    vehicle_number = data.get('vehicle_number')
    payment_provider = data.get('payment_provider', 'stripe')
    if not amount or not vehicle_number:
        return jsonify({"error": "Amount and vehicle number required"}), 400
    transaction_id = str(uuid.uuid4())
    user = get_current_user()
    payment_transactions.insert_one({
        "transaction_id": transaction_id,
        "vehicle_number": vehicle_number,
        "amount": float(amount),
        "currency": "inr",
        "payment_provider": payment_provider,
        "status": "pending",
        "user_id": user['user_id'] if user else None,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    return jsonify({"success": True, "transaction_id": transaction_id, "checkout_url": f"/payment.html?transaction_id={transaction_id}&amount={amount}"})

@flask_app.route('/api/payment/confirm', methods=['POST'])
def confirm_payment():
    data = request.json
    transaction_id = data.get('transaction_id')
    if not transaction_id:
        return jsonify({"error": "Transaction ID required"}), 400
    result = payment_transactions.update_one(
        {"transaction_id": transaction_id},
        {"$set": {"status": "completed", "completed_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.modified_count == 0:
        return jsonify({"error": "Transaction not found"}), 404
    return jsonify({"success": True, "message": "Payment confirmed"})

# ========== EXPIRY CHECK ROUTE ==========

@flask_app.route('/api/reservations/check-expiring', methods=['GET'])
def check_expiring_reservations():
    """Check for reservations expiring in the next 5 minutes"""
    now = datetime.now(timezone.utc)
    soon = (now + timedelta(minutes=5)).isoformat()
    now_str = now.isoformat()

    expiring = list(reservations.find(
        {"status": "active", "expires_at": {"$lte": soon, "$gte": now_str}},
        {"_id": 0}
    ))
    return jsonify({"expiring": expiring, "count": len(expiring)})

# ========== ASGI APP ==========

# Wrap Flask WSGI in ASGI middleware, then combine with Socket.IO
flask_asgi = WSGIMiddleware(flask_app)
app = socketio.ASGIApp(sio, other_asgi_app=flask_asgi, socketio_path='/api/socket.io')
