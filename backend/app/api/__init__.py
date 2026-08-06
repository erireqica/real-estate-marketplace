from flask import Blueprint, jsonify

api = Blueprint("api", __name__)

from .auth import auth_bp
from .properties import properties_bp
from .account import account_bp
from .agent import agent_bp
from .admin import admin_bp
from .market import market_bp

api.register_blueprint(auth_bp, url_prefix="/auth")
api.register_blueprint(properties_bp, url_prefix="/properties")
api.register_blueprint(account_bp, url_prefix="/account")
api.register_blueprint(agent_bp, url_prefix="/agent")
api.register_blueprint(admin_bp, url_prefix="/admin")
api.register_blueprint(market_bp, url_prefix="/market")


@api.get("/health")
def health():
    return jsonify({"status": "ok", "service": "havenly-api"})
