from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import os
import json

app = Flask(__name__)
CORS(app)

# -----------------------------
# CONFIG
# -----------------------------
GOOGLE_CLIENT_SECRETS = "client_secret.json"
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
REDIRECT_URI = os.getenv("REDIRECT_URI", "https://YOUR-RAILWAY-URL.up.railway.app/oauth2callback")

TOKEN_FILE = "token.json"


# -----------------------------
# STEP 1: USER VISITS THIS TO AUTHORIZE YOUR APP
# -----------------------------
@app.route("/authorize")
def authorize():
    flow = Flow.from_client_secrets_file(
        GOOGLE_CLIENT_SECRETS,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    auth_url, _ = flow.authorization_url(prompt="consent")
    return redirect(auth_url)


# -----------------------------
# STEP 2: GOOGLE SENDS TOKEN HERE
# -----------------------------
@app.route("/oauth2callback")
def oauth_callback():
    flow = Flow.from_client_secrets_file(
        GOOGLE_CLIENT_SECRETS,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    flow.fetch_token(authorization_response=request.url)

    credentials = flow.credentials
    with open(TOKEN_FILE, "w") as token:
        token.write(credentials.to_json())

    return "Google Calendar connected successfully! 🎉"


# -----------------------------
# API — CREATE EVENT
# -----------------------------
@app.route("/create-event", methods=["POST"])
def create_event():
    data = request.json

    if not os.path.exists(TOKEN_FILE):
        return jsonify({"error": "Google Calendar is not connected. Go to /authorize"}), 400

    credentials = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    service = build("calendar", "v3", credentials=credentials)

    event = {
        "summary": f"Cita con {data.get('name')}",
        "description": f"Email: {data.get('email')}\nMensaje: {data.get('message')}",
        "start": {"dateTime": data.get("start"), "timeZone": "America/Mexico_City"},
        "end": {"dateTime": data.get("end"), "timeZone": "America/Mexico_City"},
    }

    created_event = service.events().insert(calendarId="primary", body=event).execute()

    return jsonify({"success": True, "eventLink": created_event.get("htmlLink")})


@app.route("/")
def home():
    return "Backend OK — Google Calendar API is running 😊"


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
