from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import psycopg2
import psycopg2.extras
import os
from datetime import date, datetime

app = Flask(__name__)
CORS(app)

DATABASE_URL = os.environ.get("DATABASE_URL", "")

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Patient Registry</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: system-ui, sans-serif; background: #f4f6f9; color: #1a1a2e; }
  header { background: #1a1a2e; color: white; padding: 16px 32px; display: flex; align-items: center; justify-content: space-between; }
  header h1 { font-size: 1.2rem; font-weight: 600; }
  .container { padding: 24px 32px; }
  .toolbar { display: flex; gap: 12px; margin-bottom: 20px; }
  .toolbar input { flex: 1; padding: 10px 14px; border: 1px solid #ddd; border-radius: 8px; font-size: 0.9rem; }
  .toolbar button { padding: 10px 18px; background: #1a1a2e; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 0.9rem; }
  .toolbar button:hover { background: #2d2d5e; }
  table { width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
  thead { background: #1a1a2e; color: white; }
  th, td { padding: 12px 14px; text-align: left; font-size: 0.85rem; }
  tbody tr:nth-child(even) { background: #f9f9fb; }
  tbody tr:hover { background: #eef0f8; }
  .badge { padding: 3px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }
  .badge-male { background: #dbeafe; color: #1d4ed8; }
  .badge-female { background: #fce7f3; color: #be185d; }
  .badge-other { background: #e0e7ff; color: #4338ca; }
  .actions { display: flex; gap: 8px; }
  .btn-edit { padding: 5px 12px; background: #3b82f6; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.8rem; }
  .btn-edit:hover { background: #2563eb; }
  .btn-delete { padding: 5px 12px; background: #ef4444; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.8rem; }
  .btn-delete:hover { background: #dc2626; }
  .empty { text-align: center; padding: 48px; color: #888; }
  .overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.45); z-index: 100; align-items: center; justify-content: center; }
  .overlay.active { display: flex; }
  .modal { background: white; border-radius: 12px; padding: 28px; width: 620px; max-width: 95vw; max-height: 90vh; overflow-y: auto; }
  .modal h2 { font-size: 1.1rem; margin-bottom: 20px; }
  .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
  .field { display: flex; flex-direction: column; gap: 4px; }
  .field.full { grid-column: 1 / -1; }
  label { font-size: 0.78rem; font-weight: 600; color: #555; text-transform: uppercase; letter-spacing: 0.04em; }
  input, select { padding: 8px 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 0.88rem; }
  input:focus, select:focus { outline: none; border-color: #3b82f6; }
  .modal-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 22px; }
  .btn-cancel { padding: 9px 18px; background: #f1f1f1; border: none; border-radius: 8px; cursor: pointer; }
  .btn-save { padding: 9px 18px; background: #1a1a2e; color: white; border: none; border-radius: 8px; cursor: pointer; }
  .btn-save:hover { background: #2d2d5e; }
  .toast { position: fixed; bottom: 24px; right: 24px; padding: 12px 20px; border-radius: 8px; color: white; font-size: 0.88rem; z-index: 200; opacity: 0; transition: opacity 0.3s; pointer-events: none; }
  .toast.show { opacity: 1; }
  .toast.success { background: #16a34a; }
  .toast.error { background: #dc2626; }
  #count { font-size: 0.85rem; color: #888; align-self: center; }
</style>
</head>
<body>
<header>
  <h1>Patient Registry</h1>
  <span id="count"></span>
</header>
<div class="container">
  <div class="toolbar">
    <input id="search" type="text" placeholder="Search by name or phone..." />
    <button onclick="loadPatients()">Search</button>
    <button onclick="clearSearch()">Clear</button>
  </div>
  <table>
    <thead>
      <tr>
        <th>Name</th><th>DOB</th><th>Sex</th><th>Phone</th><th>Address</th><th>Registered</th><th>Actions</th>
      </tr>
    </thead>
    <tbody id="tbody"></tbody>
  </table>
</div>
<div class="overlay" id="overlay">
  <div class="modal">
    <h2>Edit Patient</h2>
    <div class="grid2">
      <div class="field"><label>First Name</label><input id="f_first_name" /></div>
      <div class="field"><label>Last Name</label><input id="f_last_name" /></div>
      <div class="field"><label>Date of Birth</label><input id="f_date_of_birth" type="date" /></div>
      <div class="field"><label>Sex</label>
        <select id="f_sex">
          <option value="male">Male</option>
          <option value="female">Female</option>
          <option value="other">Other</option>
          <option value="decline to answer">Decline to answer</option>
        </select>
      </div>
      <div class="field"><label>Phone</label><input id="f_phone_number" /></div>
      <div class="field"><label>Email</label><input id="f_email" type="email" /></div>
      <div class="field full"><label>Address Line 1</label><input id="f_address_line_1" /></div>
      <div class="field full"><label>Address Line 2</label><input id="f_address_line_2" /></div>
      <div class="field"><label>City</label><input id="f_city" /></div>
      <div class="field"><label>State</label><input id="f_state" maxlength="2" /></div>
      <div class="field"><label>ZIP Code</label><input id="f_zip_code" /></div>
      <div class="field"><label>Insurance Provider</label><input id="f_insurance_provider" /></div>
      <div class="field"><label>Insurance Member ID</label><input id="f_insurance_member_id" /></div>
      <div class="field"><label>Emergency Contact</label><input id="f_emergency_contact_name" /></div>
      <div class="field"><label>Emergency Phone</label><input id="f_emergency_contact_phone" /></div>
      <div class="field"><label>Preferred Language</label><input id="f_preferred_language" /></div>
    </div>
    <div class="modal-actions">
      <button class="btn-cancel" onclick="closeModal()">Cancel</button>
      <button class="btn-save" onclick="savePatient()">Save Changes</button>
    </div>
  </div>
</div>
<div class="toast" id="toast"></div>
<script>
  let currentId = null;

  async function loadPatients() {
    const search = document.getElementById("search").value.trim();
    const url = search ? `/api/patients?search=${encodeURIComponent(search)}` : "/api/patients";
    const res = await fetch(url);
    const patients = await res.json();
    renderTable(patients);
    document.getElementById("count").textContent = `${patients.length} patient${patients.length !== 1 ? "s" : ""}`;
  }

  function clearSearch() {
    document.getElementById("search").value = "";
    loadPatients();
  }

  function renderTable(patients) {
    const tbody = document.getElementById("tbody");
    if (!patients.length) {
      tbody.innerHTML = `<tr><td colspan="7" class="empty">No patients found.</td></tr>`;
      return;
    }
    tbody.innerHTML = patients.map(p => `
      <tr>
        <td><strong>${p.first_name} ${p.last_name}</strong></td>
        <td>${formatDate(p.date_of_birth)}</td>
        <td><span class="badge badge-${p.sex.replace(/ /g,"-")}">${p.sex}</span></td>
        <td>${formatPhone(p.phone_number)}</td>
        <td>${p.address_line_1}, ${p.city}, ${p.state} ${p.zip_code}</td>
        <td>${formatDate(p.created_at)}</td>
        <td class="actions">
          <button class="btn-edit" onclick='openEdit(${JSON.stringify(p)})'>Edit</button>
          <button class="btn-delete" onclick="deletePatient('${p.patient_id}','${p.first_name} ${p.last_name}')">Delete</button>
        </td>
      </tr>`).join("");
  }

  function formatDate(iso) {
    if (!iso) return "";
    return new Date(iso).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
  }

  function formatPhone(p) {
    if (!p || p.length !== 10) return p || "";
    return `(${p.slice(0,3)}) ${p.slice(3,6)}-${p.slice(6)}`;
  }

  function openEdit(p) {
    currentId = p.patient_id;
    ["first_name","last_name","date_of_birth","sex","phone_number","email",
     "address_line_1","address_line_2","city","state","zip_code",
     "insurance_provider","insurance_member_id","emergency_contact_name",
     "emergency_contact_phone","preferred_language"].forEach(f => {
      const el = document.getElementById("f_" + f);
      if (el) el.value = p[f] || "";
    });
    document.getElementById("overlay").classList.add("active");
  }

  function closeModal() {
    document.getElementById("overlay").classList.remove("active");
    currentId = null;
  }

  async function savePatient() {
    const data = {};
    ["first_name","last_name","date_of_birth","sex","phone_number","email",
     "address_line_1","address_line_2","city","state","zip_code",
     "insurance_provider","insurance_member_id","emergency_contact_name",
     "emergency_contact_phone","preferred_language"].forEach(f => {
      const el = document.getElementById("f_" + f);
      if (el && el.value.trim()) data[f] = el.value.trim();
    });
    const res = await fetch(`/api/patients/${currentId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    const json = await res.json();
    if (json.success) { closeModal(); showToast("Patient updated", "success"); loadPatients(); }
    else showToast(json.error || "Update failed", "error");
  }

  async function deletePatient(id, name) {
    if (!confirm(`Delete ${name}? This cannot be undone.`)) return;
    const res = await fetch(`/api/patients/${id}`, { method: "DELETE" });
    const json = await res.json();
    if (json.success) { showToast("Patient deleted", "success"); loadPatients(); }
    else showToast(json.error || "Delete failed", "error");
  }

  function showToast(msg, type) {
    const t = document.getElementById("toast");
    t.textContent = msg;
    t.className = `toast ${type} show`;
    setTimeout(() => t.classList.remove("show"), 3000);
  }

  document.getElementById("search").addEventListener("keydown", e => { if (e.key === "Enter") loadPatients(); });
  document.getElementById("overlay").addEventListener("click", e => { if (e.target === document.getElementById("overlay")) closeModal(); });
  loadPatients();
</script>
</body>
</html>"""


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
    return Response(HTML, mimetype="text/html")


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
