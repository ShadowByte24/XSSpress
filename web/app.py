from flask import Flask, render_template, request, send_from_directory
from urllib.parse import urljoin, urlencode
import threading
import os
import requests
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
submitted_content = {}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Set upload folder to web/upload
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'upload')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Ensure the folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

BASE_URL = os.getenv('BASE_URL', 'http://0.0.0.0')
BOT_URL = os.getenv('BOT_URL', 'http://0.0.0.0:8000')


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/preview', methods=["GET","POST"])
def preview():
    """Preview the content"""
    content_preview =""
    if request.method == "POST":
       content_preview = request.form.get("content_preview")

    return render_template("preview.html", contentTodisplay=content_preview)


@app.route("/write-to-editor", methods=["GET"])
def create():
    return render_template("write-to-editor.html")


# @app.route('/debug')
# def debug():
#     return {
#         'current_working_dir': os.getcwd(),
#         'app_location': os.path.dirname(os.path.abspath(__file__)),
#         'upload_folder': app.config['UPLOAD_FOLDER'],
#         'upload_folder_exists': os.path.exists(app.config['UPLOAD_FOLDER'])
#     }


@app.route('/send-to-editor', methods=['POST'])
def submit():
    """Handle input submission"""
    content_submit = request.form.get('content_submit')
    if not content_submit:
        return "No content submitted", 400

    # Create unique ID and store payload
    unique_id = str(uuid.uuid4())
    submitted_content[unique_id] = content_submit

    # Trigger bot to visit /preview/<id>
    uploaded_url = urljoin(BASE_URL, f"/send-to-editor/{unique_id}")
    print(f"Triggering bot for: {uploaded_url}")
    threading.Thread(target=bot, args=(uploaded_url, submitted_content[unique_id])).start()
    return f"""Content has been sent to the admin with unique_id: <a href="/send-to-editor/{unique_id}">{unique_id}</a>!"""

@app.route('/send-to-editor/<unique_id>', methods=['GET'])
def submit_content(unique_id):
    return "",200


@app.route('/upload', methods=['GET','POST'])
def upload():
    
        if request.method == 'POST':
             
            # Check if the file part is in the request
            if 'file' not in request.files:
                return "No file uploaded", 400
            
            file = request.files['file']
            if file.filename == '':
                return "Empty filename.", 400
            
            if file:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                uploaded_url = urljoin(BASE_URL, f"/uploads/{filename}")
                print(f"Triggering bot for: {uploaded_url}")
                # Run bot in a separate thread
                threading.Thread(target=bot, args=(uploaded_url,)).start()
               
                return render_template('dropzone.html', filename=filename)

        return render_template('dropzone.html')




@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.after_request
def apply_csp(response):
    response.headers['Content-Security-Policy'] = (
         "base-uri 'self'; "
        "default-src 'self'; "
        "script-src 'self' 'nonce-rAnd0mn0Nc3' 'strict-dynamic'; "
        "object-src 'none';" 
        " connect-src *; " )
    response.headers['Access-Control-Allow-Origin'] = '*'
   
    return response


def bot(uploaded_url, submitted_content=None):
    try:
        if submitted_content:
            requests.post(BOT_URL, data={"url": uploaded_url, "contentToAdmin": submitted_content})
        else:
            requests.post(BOT_URL, data={"url": uploaded_url})
    except Exception as e:
        print(f"Error notifying bot: {e}")

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=80)
