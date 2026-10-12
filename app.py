from flask import Flask, request, jsonify
from flask_cors import CORS  # <--- I-import ang CORS
import os
from supabase import create_client, Client

app = Flask(__name__)
CORS(app)  # <--- Paganahin ang CORS para sa lahat ng routes

SUPABASE_URL = os.environ.get("SUPABASE_URL", "YOUR_SUPABASE_URL_HERE")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "YOUR_SUPABASE_SERVICE_ROLE_KEY_HERE")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

active_tokens = {}

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "online", "message": "FLUXHAX API Server is running!"}), 200

@app.route('/verify', methods=['POST'])
def verify_key():
    data = request.get_json(force=True)
    entered_key = data.get('key')
    device_id = data.get('device_id')
    
    if not entered_key or not device_id:
        return jsonify({"status": "error", "message": "Missing key or device_id"}), 400
    
    response = supabase.table('FLUXHAX').select('*').eq('key', entered_key).execute()
    
    if not response.data or len(response.data) == 0:
        return jsonify({"status": "error", "message": "Invalid key!"}), 403
        
    row = response.data[0]
    bound_device = row.get('device_id')
    
    if not bound_device:
        supabase.table('FLUXHAX').update({'device_id': device_id}).eq('key', entered_key).execute()
        return jsonify({"status": "success", "message": "Login successfully"}), 200
    elif bound_device == device_id:
        return jsonify({"status": "success", "message": "Login successfully"}), 200
    else:
        return jsonify({"status": "error", "message": "Key already bound to another device!"}), 403

@app.route('/token', methods=['GET'])
def get_token():
    device_id = request.args.get('device_id')
    if not device_id:
        return jsonify({"status": "error", "message": "Missing device_id"}), 400
    
    token = 'tok_' + os.urandom(8).hex()
    active_tokens[token] = device_id
    
    return jsonify({"token": token}), 200

import random
import string

@app.route('/getkey', methods=['GET'])
def get_key():
    token = request.args.get('token')
    if not token or token not in active_tokens:
        return jsonify({"status": "error", "message": "Invalid or expired token"}), 400
    
    device_id = active_tokens[token]
    
    try:
        # Gumawa ng sariling key: CODM-FREEKEY + 5 random digits
        random_digits = ''.join(random.choices(string.digits, k=5))
        new_key = f"CODM-FREEKEY{random_digits}"
        
        # I-save sa Supabase pero IWANANG NULL ANG device_id 
        # (Para ang Android App ang magba-bind nito sa phone ng user kapag nag-login na!)
        supabase.table('FLUXHAX').insert({
            'key': new_key,
            'device_id': None
        }).execute()
        
        # Tanggalin na ang token para hindi maulit ang request
        del active_tokens[token]
        
        return jsonify({"status": "success", "key": new_key}), 200
        
    except Exception as e:
        print("Error in getkey:", str(e))
        return jsonify({"status": "error", "message": "Server internal error"}), 500
        
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
