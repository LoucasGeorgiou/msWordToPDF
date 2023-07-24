from flask import Flask, render_template, request, redirect
import os
from werkzeug.utils import secure_filename
from docx import Document
import pdfkit
import mammoth
from google.cloud import storage
from google.oauth2 import service_account
import io
import datetime
from flask import jsonify

BUCKET_NAME = "simpleconverter"

app = Flask(__name__)
app.config['SECRET_KEY'] = 'loukas10'

# Specify the path to your service account key file
key_path = "/Users/vanishz/Desktop/Documents/10.Programming/01.Python/02.Simpleconverter/keyfile.json"

# Load the credentials from the service account key file
credentials = service_account.Credentials.from_service_account_file(key_path)

# Pass the credentials to the client
storage_client = storage.Client(credentials=credentials)

bucket = storage_client.get_bucket(BUCKET_NAME)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            blob = bucket.blob(filename)
            blob.upload_from_file(file)
            processed_file, status = process_file(filename)
            if status == 200:
                blob_pdf = bucket.blob(processed_file)
                blob_pdf.content_disposition = "attachment"  # Set the content disposition property
                blob_pdf.upload_from_filename(processed_file)
                os.remove(processed_file)  # remove the local PDF file after it has been uploaded to GCS
                # generate a signed url for the pdf and redirect the user to this url
                url = blob_pdf.generate_signed_url(expiration=datetime.timedelta(minutes=10))
                return url, 200
            else:
                return processed_file, status
    return render_template('index.html')

def process_file(filename):
    print(f"Processing file: {filename}")  # Debug print

    blob = bucket.blob(filename)
    blob.download_to_filename(filename)  # It is important to ensure that 'filename' is not None

    filename_without_ext = os.path.splitext(filename)[0]
    output_path = filename_without_ext + ".pdf"

    try:
        Document(filename)  # This should be the path where you downloaded the file
    except:
        return "Invalid .docx file", 400

    try:
        with open(filename, "rb") as docx_file:  # This should be the path where you downloaded the file
            result = mammoth.convert_to_html(docx_file)
            html = result.value

        # convert html to pdf
        pdfkit.from_file(io.StringIO(html), output_path)

        os.remove(filename)  # This should be the path where you downloaded the file

        return output_path, 200
    except Exception as e:
        return str(e), 500

if __name__ == "__main__":
    app.run(debug=True)
