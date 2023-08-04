from flask import Flask, render_template
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
import psycopg2

app = Flask(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
SPREADSHEET_ID = "1VvgqxLmMmMzBLtoNA3zqNaLe5v88k_ol2sHQKOpJgts"

def table_exists(conn):
    cur = conn.cursor()
    cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'formulario')")
    exists = cur.fetchone()[0]
    cur.close()
    return exists

def create_table(conn):
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE formulario (
            id SERIAL PRIMARY KEY,
            marca_temporal VARCHAR,
            correo_electronico VARCHAR,
            lenguajes_programacion VARCHAR,
            conocimiento_postgresql VARCHAR,
            experiencia_pgadmin VARCHAR,
            modelo_entidad_relacion VARCHAR,
            acciones_sql VARCHAR,
            experiencia_nosql VARCHAR,
            experiencia_bodegas VARCHAR
        );
    ''')
    conn.commit()
    cur.close()

def get_google_sheets_data():
    creds = None
    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
    
    if not creds or not creds.valid:
        creds = flow.run_local_server(port=0)
    
    service = build("sheets", "v4", credentials=creds)
    sheet = service.spreadsheets()
    
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range="uno").execute()
    values = result.get("values", [])
    
    return values

def save_to_database(data):
    conn = psycopg2.connect(
        host="localhost",
        database="leidito",
        user="root",
        password="root"
    )
    
    if not table_exists(conn):
        create_table(conn)
    
    cur = conn.cursor()
    for row in data:
        cur.execute(
            "INSERT INTO formulario (marca_temporal, correo_electronico, lenguajes_programacion, conocimiento_postgresql, experiencia_pgadmin, modelo_entidad_relacion, acciones_sql, experiencia_nosql, experiencia_bodegas) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8])
        )
    conn.commit()
    cur.close()
    conn.close()

@app.route("/")
def index():
    try:
        data = get_google_sheets_data()
        save_to_database(data)
        return render_template("index.html", data=data)
    except Exception as e:
        return f"Error al obtener los datos: {e}"

if __name__ == "__main__":
    app.run(debug=True)
