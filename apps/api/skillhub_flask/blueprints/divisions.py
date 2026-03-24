"""Divisions reference endpoint — populates submission form dropdown."""
from flask import Blueprint, jsonify
from skillhub_flask.db import get_db
from skillhub_db.models.division import Division

bp = Blueprint("divisions", __name__)

@bp.route("/api/v1/divisions", methods=["GET"])
def list_divisions():
    """List all divisions. Public endpoint for submission form."""
    db = get_db()
    divisions = db.query(Division).order_by(Division.name).all()
    return jsonify([
        {"slug": d.slug, "name": d.name, "color": getattr(d, 'color', None)}
        for d in divisions
    ]), 200
