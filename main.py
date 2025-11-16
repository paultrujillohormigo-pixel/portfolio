from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import os
import json

app = Flask(__name__)
CORS(app)

if os.environ.get("FLASK_ENV") == "development":
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '0'

# -----------------------------
# CONFIG
# -----------------------------
GOOGLE_CLIENT_SECRETS = "client_secret.json"
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

# REDIRECT_URI debe ser tu dominio de Railway + /oauth2callback
REDIRECT_URI = os.getenv("REDIRECT_URI","https://portfolio-production-1cfa.up.railway.app/oauth2callback")

# En Railway usamos /tmp para almacenar archivos temporales
TOKEN_FILE = "/tmp/token.json"


# -----------------------------
# STEP 1: USUARIO AUTORIZA
# -----------------------------
@app.route("/authorize")
def authorize():
    try:
        flow = Flow.from_client_secrets_file(
            GOOGLE_CLIENT_SECRETS,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        auth_url, _ = flow.authorization_url(prompt="consent")
        return redirect(auth_url)
    except Exception as e:
        return f"Error al generar la autorización: {str(e)}", 500


# -----------------------------
# STEP 2: CALLBACK DE GOOGLE
# -----------------------------
@app.route("/oauth2callback")
def oauth_callback():
    try:
        flow = Flow.from_client_secrets_file(
            GOOGLE_CLIENT_SECRETS,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        flow.fetch_token(authorization_response=request.url)
        credentials = flow.credentials

        with open(TOKEN_FILE, "w") as token:
            token.write(credentials.to_json())

        return "Google Calendar conectado correctamente! 🎉"
    except Exception as e:
        return f"Error al conectar con Google Calendar: {str(e)}", 500


# -----------------------------
# API — CREAR EVENTO
# -----------------------------
@app.route("/create-event", methods=["POST"])
def create_event():
    try:
        data = request.json

        if not os.path.exists(TOKEN_FILE):
            return jsonify({"error": "Google Calendar no está conectado. Ve a /authorize"}), 400

        credentials = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        service = build("calendar", "v3", credentials=credentials)

        # Creamos el evento
        event = {
            "summary": f"Cita con {data.get('name')}",
            "description": f"Email: {data.get('email')}\nMensaje: {data.get('message')}",
            "start": {"dateTime": data.get("start"), "timeZone": "America/Mexico_City"},
            "end": {"dateTime": data.get("end"), "timeZone": "America/Mexico_City"},
        }

        created_event = service.events().insert(calendarId="primary", body=event).execute()
        return jsonify({"success": True, "eventLink": created_event.get("htmlLink")})
    except Exception as e:
        return jsonify({"error": f"Error al crear evento: {str(e)}"}), 500


# -----------------------------
# HOME
# -----------------------------
@app.route("/")
def home():
    return "Backend OK — Google Calendar API funcionando 😊"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
