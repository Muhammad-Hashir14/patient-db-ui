from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
import psycopg2.extras
import os
from datetime import date, datetime

app = Flask(__name__, static_folder="../static", static_url_path="")
CORS(app)

DATABASE_URL = os.environ.get("DATABASE_URL", "")


def get_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)


def serialize(row):
    d = dict(row)
    for k, v in d.items():
        if isinstance(v, (date, datetime)):
            d[k] = v.isoformat()
    return d


@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/api/patients")
def list_patients():
    search = request.args.get("search", "").strip()
    with get_conn() as conn:
        with conn.cursor() as cur:
            if search:
                cur.execute(
                    """SELECT * FROM patients WHERE deleted_at IS NULL
                       AND (first_name ILIKE %s OR last_name ILIKE %s OR phone_number ILIKE %s)
                       ORDER BY created_at DESC""",
                    (f"%{search}%", f"%{search}%", f"%{search}%"),
                )
            else:
                cur.execute("SELECT * FROM patients WHERE deleted_at IS NULL ORDER BY created_at DESC")
            rows = cur.fetchall()
    return jsonify([serialize(r) for r in rows])


@app.route("/api/patients/<patient_id>", methods=["PUT"])
def update_patient(patient_id):
    data = request.json
    allowed = [
        "first_name", "last_name", "date_of_birth", "sex", "phone_number",
        "address_line_1", "address_line_2", "city", "state", "zip_code",
        "email", "insurance_provider", "insurance_member_id",
        "preferred_language", "emergency_contact_name", "emergency_contact_phone",
    ]
    fields = {k: v for k, v in data.items() if k in allowed}
    if not fields:
        return jsonify({"error": "No valid fields provided"}), 400

    set_clause = ", ".join(f"{k} = %s" for k in fields)
    values = list(fields.values()) + [patient_id]

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE patients SET {set_clause}, updated_at = NOW() WHERE patient_id = %s AND deleted_at IS NULL",
                values,
            )
            if cur.rowcount == 0:
                return jsonify({"error": "Patient not found"}), 404
        conn.commit()
    return jsonify({"success": True})


@app.route("/api/patients/<patient_id>", methods=["DELETE"])
def delete_patient(patient_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE patients SET deleted_at = NOW() WHERE patient_id = %s AND deleted_at IS NULL",
                (patient_id,),
            )
            if cur.rowcount == 0:
                return jsonify({"error": "Patient not found"}), 404
        conn.commit()
    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(debug=True)
