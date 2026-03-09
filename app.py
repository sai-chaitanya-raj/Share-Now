from flask import Flask, render_template, request, jsonify, send_file
import os, random, string
from cryptography.fernet import Fernet
import qrcode
from io import BytesIO
import base64
from werkzeug.utils import secure_filename
from pymongo import MongoClient

app = Flask(__name__)
client = MongoClient("mongodb://localhost:27017/") # Replace with your MongoDB connection string
db = client["nowshare_db"]
contact_collection = db["contacts"]

UPLOAD_FOLDER = 'uploads'
codes = {}
keys = {}
history = []  # To store the history temporarily

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def generate_key():
    return Fernet.generate_key()

def generate_qr_code(code):
    # Create the URL with the code as a query parameter
    url_with_code = f"https://nowshare.onrender.com/?code={code}"

    # Generate QR code with the URL
    img = qrcode.make(url_with_code)

    # Save the QR code image to a BytesIO object
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    # Convert the image to base64 encoding
    img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')

    # Return the base64 string as a data URL
    return f"data:image/png;base64,{img_base64}"

@app.route('/')
def index():
    return render_template('index.html', history=history)

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    sender_ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
  # Get sender's IP address
    code = ''.join(random.choices(string.digits, k=6))
    
    original_filename = secure_filename(file.filename)  # Sanitize filename
    filename = f"{code}_{original_filename}"
    path = os.path.join(UPLOAD_FOLDER, filename)

    key = generate_key()
    fernet = Fernet(key)
    encrypted_data = fernet.encrypt(file.read())

    with open(path, 'wb') as f:
        f.write(encrypted_data)

    codes[code] = path
    keys[code] = key

    # Save upload history
    history.append({
        'sender_ip': sender_ip,
        'receiver_ip': '',
        'filename': filename
    })

    qr_code_url = generate_qr_code(code)

    return jsonify({'code': code, 'qr_code_url': qr_code_url})

@app.route('/download/<code>', methods=['GET'])
def download(code):
    path = codes.get(code)
    key = keys.get(code)
    receiver_ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
  # Get receiver's IP address

    if path and key and os.path.exists(path):
        fernet = Fernet(key)
        with open(path, 'rb') as f:
            encrypted_data = f.read()

        try:
            decrypted_data = fernet.decrypt(encrypted_data)
        except Exception as e:
            return f"Decryption failed. Error: {str(e)}", 400

        # Extract original filename
        try:
            _, original_filename = os.path.basename(path).split('_', 1)
        except ValueError:
            original_filename = "downloaded_file"

        # Update history with receiver IP
        for entry in history:
            if entry['filename'] == os.path.basename(path) and entry['receiver_ip'] == '':
                entry['receiver_ip'] = receiver_ip

        return send_file(
            BytesIO(decrypted_data),
            as_attachment=True,
            download_name=original_filename,
            mimetype='application/octet-stream'
        )

    return "Invalid code or file expired.", 404

@app.route('/get_history', methods=['GET'])
def get_history():
    return jsonify(history)  

#contact info
@app.route('/submit_contact', methods=['POST'])
def submit_contact():
    data = request.get_json()  # Accepts JSON payload

    if not data:
        return jsonify({"message": "Invalid data"}), 400

    # Extract data from the JSON payload
    name = data.get('name')
    phone = data.get('phone')
    email = data.get('email')
    message = data.get('message')

    if not all([name, phone, email, message]):
        return jsonify({"message": "All fields are required"}), 400

    # Insert data into MongoDB
    contact_collection.insert_one({
        "name": name,
        "phone": phone,
        "email": email,
        "message": message
    })

    return jsonify({"message": "Contact submitted successfully"}), 200



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
