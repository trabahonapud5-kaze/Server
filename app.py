from flask import Flask, request, jsonify
import os
from supabase import create_client, Client

app = Flask(__name__)

# Mga kinakailangan mula sa iyong bagong Supabase project para sa FLUXHAX
SUPABASE_URL = os.environ.get("SUPABASE_URL", "YOUR_SUPABASE_URL_HERE")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "YOUR_SUPABASE_SERVICE_ROLE_KEY_HERE")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/verify', methods=['POST'])
def verify_device():
    data = request.json
    device_id = data.get('device_id')
    
    if not device_id:
        return jsonify({"status": "error", "message": "Missing device_id"}), 400
    
    # Hanapin ang device_id sa Supabase table mo (halimbawa: table name ay 'devices' o 'device_links')
    response = supabase.table('devices').select('*').eq('device_id', device_id).execute()
    
    # Kung may nahanap na record at active/valid
    if response.data and len(response.data) > 0:
        return jsonify({"status": "success", "message": "Access granted!"}), 200
    else:
        return jsonify({"status": "error", "message": "Device not registered or banned!"}), 403

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
