from flask import Flask, request, jsonify
import os
from supabase import create_client, Client

app = Flask(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "YOUR_SUPABASE_URL_HERE")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "YOUR_SUPABASE_SERVICE_ROLE_KEY_HERE")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/verify', methods=['POST'])
def verify_key():
    # Gamitin ang force=True para maiwasan ang 415 Unsupported Media Type error
    data = request.get_json(force=True)
    entered_key = data.get('key')
    device_id = data.get('device_id')
    
    if not entered_key or not device_id:
        return jsonify({"status": "error", "message": "Missing key or device_id"}), 400
    
    # Hanapin ang key sa 'FLUXHAX' table
    response = supabase.table('FLUXHAX').select('*').eq('key', entered_key).execute()
    
    if not response.data or len(response.data) == 0:
        return jsonify({"status": "error", "message": "Invalid key!"}), 403
        
    row = response.data[0]
    bound_device = row.get('device_id')
    
    # Kung wala pang device na nakakabit (NULL/blank), i-bind ito sa kasalukuyang device_id
    if not bound_device:
        update_res = supabase.table('FLUXHAX').update({'device_id': device_id}).eq('key', entered_key).execute()
        return jsonify({"status": "success", "message": "Login successfully"}), 200
        
    # Kung may nakakabit na, i-check kung tugma sa kasalukuyang device_id
    elif bound_device == device_id:
        return jsonify({"status": "success", "message": "Login successfully"}), 200
    else:
        return jsonify({"status": "error", "message": "Key already bound to another device!"}), 403

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
