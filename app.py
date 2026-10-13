from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import random
import string
from datetime import datetime, timedelta, timezone
from supabase import create_client, Client

app = Flask(__name__)
CORS(app)

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
    expires_at = row.get('expires_at')
    
    # Check kung nag-expire na ang key (3-hour duration)
    if expires_at:
        exp_time = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        if now > exp_time:
            return jsonify({"status": "error", "message": "Key has already expired!"}), 403

    # Kung wala pang device na nakakabit, i-bind sa device_id at itakda ang expiration
    if not bound_device:
        now = datetime.now(timezone.utc)
        expire_time = (now + timedelta(hours=3)).isoformat()
        
        supabase.table('FLUXHAX').update({
            'device_id': device_id,
            'expires_at': expire_time
        }).eq('key', entered_key).execute()
        
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
    
    try:
        # --- 3-MINUTE COOLDOWN CHECK (Para sa Testing) ---
        response = supabase.table('FLUXHAX') \
            .select('*') \
            .eq('created_by_device', device_id) \
            .order('created_at', desc=True) \
            .limit(1) \
            .execute()
        
        if response.data and len(response.data) > 0:
            last_created = response.data[0].get('created_at')
            if last_created:
                clean_time_str = str(last_created).replace('Z', '+00:00')
                if '+' not in clean_time_str and '-' not in clean_time_str[10:]:
                    clean_time_str += '+00:00'
                    
                last_time = datetime.fromisoformat(clean_time_str)
                now = datetime.now(timezone.utc)
                
                diff_seconds = (now - last_time).total_seconds()
                cooldown_limit = 3 * 60  # 3 minutes in seconds para sa testing
                
                if diff_seconds < cooldown_limit:
                    remaining_seconds = int(cooldown_limit - diff_seconds)
                    rem_mins = remaining_seconds // 60
                    rem_secs = remaining_seconds % 60
                    
                    return jsonify({
                        "status": "cooldown", 
                        "message": f"Test Cooldown! Please wait {rem_mins}m {rem_secs}s before getting another key."
                    }), 200
    except Exception as e:
        print("COOLDOWN CHECK ERROR:", str(e))
        pass

    token = 'tok_' + os.urandom(8).hex()
    active_tokens[token] = device_id
    
    return jsonify({"status": "success", "token": token}), 200

@app.route('/getkey', methods=['GET'])
def get_key():
    token = request.args.get('token')
    if not token or token not in active_tokens:
        return jsonify({"status": "error", "message": "Invalid or expired token"}), 400
    
    device_id = active_tokens[token]
    
    try:
        random_digits = ''.join(random.choices(string.digits, k=5))
        new_key = f"CODM-FREEKEY{random_digits}"
        
        current_time = datetime.now(timezone.utc).isoformat()
        
        supabase.table('FLUXHAX').insert({
            'key': new_key,
            'device_id': None,
            'created_by_device': device_id,
            'created_at': current_time
        }).execute()
        
        del active_tokens[token]
        
        return jsonify({"status": "success", "key": new_key}), 200
        
    except Exception as e:
        print("Error in getkey:", str(e))
        return jsonify({"status": "error", "message": "Server internal error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
