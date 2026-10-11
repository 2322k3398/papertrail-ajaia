import os
import sqlite3
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort, jsonify
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "documents.db"))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
ALLOWED_EXTENSIONS = {"txt", "md"}

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-this-secret")
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

SEED_USERS = [
    {"name": "Vishnu Priya", "email": "vishnupriya200636@gmail.com"},
    {"name": "Alex Morgan", "email": "alex@example.com"},
    {"name": "Sam Taylor", "email": "sam@example.com"},
]

def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with connect_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL DEFAULT '',
            owner_id INTEGER NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(owner_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS shares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            permission TEXT NOT NULL DEFAULT 'edit',
            UNIQUE(document_id, user_id),
            FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """)
        for user in SEED_USERS:
            db.execute("INSERT OR IGNORE INTO users(name,email) VALUES (?,?)",
                       (user["name"], user["email"]))
        db.commit()

init_db()

def current_user():
    if "user_id" not in session:
        return None
    with connect_db() as db:
        return db.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()

def document_access(doc_id, user_id):
    with connect_db() as db:
        doc = db.execute("""
            SELECT d.*, u.name AS owner_name, u.email AS owner_email
            FROM documents d JOIN users u ON u.id=d.owner_id WHERE d.id=?
        """, (doc_id,)).fetchone()
        if not doc:
            return None, None
        shared = db.execute("SELECT permission FROM shares WHERE document_id=? AND user_id=?",
                            (doc_id, user_id)).fetchone()
        if doc["owner_id"] == user_id:
            return doc, "owner"
        if shared:
            return doc, shared["permission"]
        return doc, None

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user():
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

@app.route("/")
def index():
    if not current_user():
        return redirect(url_for("login"))
    user = current_user()
    with connect_db() as db:
        owned = db.execute("""
            SELECT d.*, 'owner' AS access, u.name AS owner_name
            FROM documents d JOIN users u ON u.id=d.owner_id
            WHERE d.owner_id=? ORDER BY d.updated_at DESC
        """, (user["id"],)).fetchall()
        shared = db.execute("""
            SELECT d.*, s.permission AS access, u.name AS owner_name
            FROM shares s JOIN documents d ON d.id=s.document_id
            JOIN users u ON u.id=d.owner_id
            WHERE s.user_id=? AND d.owner_id != ? ORDER BY d.updated_at DESC
        """, (user["id"], user["id"])).fetchall()
        users = db.execute("SELECT * FROM users WHERE id != ? ORDER BY name", (user["id"],)).fetchall()
    return render_template("index.html", user=user, owned=owned, shared=shared, users=users)

@app.route("/login", methods=["GET", "POST"])
def login():
    with connect_db() as db:
        users = db.execute("SELECT * FROM users ORDER BY name").fetchall()
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        with connect_db() as db:
            user = db.execute("SELECT * FROM users WHERE lower(email)=?", (email,)).fetchone()
        if not user:
            flash("Choose one of the seeded demo accounts.", "error")
            return render_template("login.html", users=users)
        session["user_id"] = user["id"]
        return redirect(url_for("index"))
    return render_template("login.html", users=users)

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/documents/new", methods=["POST"])
@login_required
def create_document():
    user = current_user()
    title = (request.form.get("title") or "Untitled document").strip()[:120] or "Untitled document"
    now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    with connect_db() as db:
        cur = db.execute("INSERT INTO documents(title,content,owner_id,updated_at) VALUES (?,?,?,?)",
                         (title, "<p>Start writing your ideas here...</p>", user["id"], now))
        doc_id = cur.lastrowid
        db.commit()
    return redirect(url_for("edit_document", doc_id=doc_id))

@app.route("/documents/import", methods=["POST"])
@login_required
def import_document():
    file = request.files.get("file")
    if not file or not file.filename:
        flash("Choose a .txt or .md file to import.", "error")
        return redirect(url_for("index"))
    filename = secure_filename(file.filename)
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        flash("Only .txt and .md files are supported.", "error")
        return redirect(url_for("index"))
    raw = file.read(1_000_001)
    if len(raw) > 1_000_000:
        flash("Files must be smaller than 1 MB.", "error")
        return redirect(url_for("index"))
    text_content = raw.decode("utf-8", errors="replace")
    # Escape imported plain text by placing it into a preformatted block.
    import html
    content = "<pre>" + html.escape(text_content) + "</pre>"
    title = filename.rsplit(".", 1)[0][:120] or "Imported document"
    user = current_user()
    now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    with connect_db() as db:
        cur = db.execute("INSERT INTO documents(title,content,owner_id,updated_at) VALUES (?,?,?,?)",
                         (title, content, user["id"], now))
        doc_id = cur.lastrowid
        db.commit()
    flash("File imported as a new editable document.", "success")
    return redirect(url_for("edit_document", doc_id=doc_id))

@app.route("/documents/<int:doc_id>")
@login_required
def edit_document(doc_id):
    user = current_user()
    doc, access = document_access(doc_id, user["id"])
    if not doc or not access:
        abort(404)
    with connect_db() as db:
        shares = db.execute("""
            SELECT u.name,u.email,s.permission FROM shares s JOIN users u ON u.id=s.user_id
            WHERE s.document_id=? ORDER BY u.name
        """, (doc_id,)).fetchall() if access == "owner" else []
        users = db.execute("SELECT * FROM users WHERE id NOT IN (SELECT user_id FROM shares WHERE document_id=?) AND id != ? ORDER BY name",
                           (doc_id, doc["owner_id"])).fetchall() if access == "owner" else []
    return render_template("editor.html", user=user, doc=doc, access=access, shares=shares, users=users)

@app.route("/api/documents/<int:doc_id>", methods=["PUT"])
@login_required
def save_document(doc_id):
    user = current_user()
    doc, access = document_access(doc_id, user["id"])
    if not doc or not access:
        return jsonify({"error": "Document not found or access denied"}), 404
    if access == "view":
        return jsonify({"error": "You have view-only access"}), 403
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", doc["title"])).strip()[:120] or "Untitled document"
    content = str(data.get("content", doc["content"]))
    if len(content) > 500_000:
        return jsonify({"error": "Document content is too large"}), 413
    now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    with connect_db() as db:
        db.execute("UPDATE documents SET title=?,content=?,updated_at=? WHERE id=?",
                   (title, content, now, doc_id))
        db.commit()
    return jsonify({"ok": True, "title": title, "updated_at": now})

@app.route("/documents/<int:doc_id>/share", methods=["POST"])
@login_required
def share_document(doc_id):
    user = current_user()
    doc, access = document_access(doc_id, user["id"])
    if not doc or access != "owner":
        abort(403)
    email = request.form.get("email", "").strip().lower()
    permission = request.form.get("permission", "edit")
    if permission not in ("edit", "view"):
        permission = "edit"
    with connect_db() as db:
        target = db.execute("SELECT * FROM users WHERE lower(email)=?", (email,)).fetchone()
        if not target:
            flash("That email is not a seeded demo user. Try Alex or Sam.", "error")
        elif target["id"] == user["id"]:
            flash("You already own this document.", "error")
        else:
            db.execute("INSERT INTO shares(document_id,user_id,permission) VALUES (?,?,?) ON CONFLICT(document_id,user_id) DO UPDATE SET permission=excluded.permission",
                       (doc_id, target["id"], permission))
            db.commit()
            flash(f"Shared with {target['email']} ({permission} access).", "success")
    return redirect(url_for("edit_document", doc_id=doc_id))

@app.route("/documents/<int:doc_id>/share/<email_hash>", methods=["POST"])
@login_required
def revoke_share(doc_id, email_hash):
    user = current_user()
    doc, access = document_access(doc_id, user["id"])
    if not doc or access != "owner":
        abort(403)
    email = request.form.get("email", "").strip().lower()
    with connect_db() as db:
        target = db.execute("SELECT id FROM users WHERE lower(email)=?", (email,)).fetchone()
        if target:
            db.execute("DELETE FROM shares WHERE document_id=? AND user_id=?", (doc_id, target["id"]))
            db.commit()
    return redirect(url_for("edit_document", doc_id=doc_id))

@app.errorhandler(413)
def too_large(_error):
    flash("Upload is too large. Maximum request size is 2 MB.", "error")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
