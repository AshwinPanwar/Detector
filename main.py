from flask import Flask, render_template, request
import google.generativeai as genai
import os
import PyPDF2  
from dotenv import load_dotenv 

load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# --- API Configuration ---

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

# Initialize Gemini model
model = genai.GenerativeModel("gemini-2.5-flash")



# --- AI Logic Functions ---

def predict_fake_or_real_email_content(text):
    prompt = f"""
    You are an expert in identifying scam messages in text or email.
    Classify this content as:
    - Real/Legitimate
    - Scam/Fake

    Text:
    {text}

    Respond with one clear sentence stating if it’s real or scam and why.
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip() if response and response.text else "Classification failed."
    except Exception as e:
        return f"Error during AI classification: {str(e)}"


def url_detection(url):
    prompt = f"""
    You are an advanced AI trained to classify URLs for safety.

    Categories:
    - benign (safe/trusted)
    - phishing (fraudulent)
    - malware (spreading harmful software)
    - defacement (hacked websites)

    URL: {url}

    Return only one category name in lowercase.
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip().lower() if response and response.text else "unknown"
    except Exception as e:
        return f"error: {str(e)}"


# --- Routes ---

@app.route('/')
def home():
    return render_template("index.html",
                           message="",
                           predicted_class="",
                           input_url="")


@app.route('/scam/', methods=['POST'])
def detect_scam():
    if 'file' not in request.files:
        return render_template("index.html",
                               message="No file uploaded.",
                               predicted_class="",
                               input_url="")

    file = request.files['file']
    extracted_text = ""

    # Extract text safely
    if file.filename.endswith('.pdf'):
        try:
            pdf_reader = PyPDF2.PdfReader(file)
            extracted_text = " ".join([page.extract_text() or "" for page in pdf_reader.pages])
        except Exception:
            return render_template("index.html",
                                   message="Error reading PDF file.",
                                   predicted_class="",
                                   input_url="")
    elif file.filename.endswith('.txt'):
        try:
            extracted_text = file.read().decode("utf-8")
        except Exception:
            return render_template("index.html",
                                   message="Error reading TXT file.",
                                   predicted_class="",
                                   input_url="")
    else:
        return render_template("index.html",
                               message="Invalid file type. Please upload a PDF or TXT file.",
                               predicted_class="",
                               input_url="")

    if not extracted_text.strip():
        return render_template("index.html",
                               message="File is empty or text could not be extracted.",
                               predicted_class="",
                               input_url="")

    message = predict_fake_or_real_email_content(extracted_text)
    return render_template("index.html",
                           message=message,
                           predicted_class="",
                           input_url="")


@app.route('/predict', methods=['POST'])
def predict_url():
    url = request.form.get('url', '').strip()

    if not url.startswith(("http://", "https://")):
        return render_template("index.html",
                               message="Invalid URL format. Include http:// or https://",
                               predicted_class="",
                               input_url=url)

    classification = url_detection(url)
    return render_template("index.html",
                           message="",
                           input_url=url,
                           predicted_class=classification)


if __name__ == '__main__':
    app.run(debug=True)
