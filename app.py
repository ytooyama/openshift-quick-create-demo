import os
from datetime import datetime

from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func


def build_database_url() -> str:
    explicit_url = os.getenv("DATABASE_URL")
    if explicit_url:
        return explicit_url

    db_user = os.getenv("DB_USER", "todo")
    db_password = os.getenv("DB_PASSWORD", "todo")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "tododb")

    return f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = build_database_url()
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
db_initialized = False


class Todo(db.Model):
    __tablename__ = "todos"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_done = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=datetime.utcnow,
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "is_done": self.is_done,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@app.before_request
def ensure_tables_exist() -> None:
    global db_initialized
    if not db_initialized:
        db.create_all()
        db_initialized = True


@app.get("/healthz")
def healthz():
    try:
        db.session.execute(db.text("SELECT 1"))
        return jsonify({"status": "ok"}), 200
    except Exception as exc:
        return jsonify({"status": "error", "detail": str(exc)}), 500


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/todos")
def list_todos():
    todos = Todo.query.order_by(Todo.id.asc()).all()
    return jsonify([todo.to_dict() for todo in todos]), 200


@app.post("/todos")
def create_todo():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    description = data.get("description")

    if not title:
        return jsonify({"error": "title is required"}), 400

    todo = Todo(title=title, description=description)
    db.session.add(todo)
    db.session.commit()
    return jsonify(todo.to_dict()), 201


@app.patch("/todos/<int:todo_id>")
def update_todo(todo_id: int):
    todo = Todo.query.get_or_404(todo_id)
    data = request.get_json(silent=True) or {}

    if "title" in data:
        title = (data.get("title") or "").strip()
        if not title:
            return jsonify({"error": "title cannot be empty"}), 400
        todo.title = title

    if "description" in data:
        todo.description = data.get("description")

    if "is_done" in data:
        is_done = data.get("is_done")
        if not isinstance(is_done, bool):
            return jsonify({"error": "is_done must be boolean"}), 400
        todo.is_done = is_done

    db.session.commit()
    return jsonify(todo.to_dict()), 200


@app.delete("/todos/<int:todo_id>")
def delete_todo(todo_id: int):
    todo = Todo.query.get_or_404(todo_id)
    db.session.delete(todo)
    db.session.commit()
    return "", 204


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
