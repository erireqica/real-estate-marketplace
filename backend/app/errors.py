from flask import jsonify
from sqlalchemy.exc import IntegrityError
from .extensions import db


class ApiError(Exception):
    def __init__(self, message: str, status: int = 400, details=None):
        super().__init__(message)
        self.message, self.status, self.details = message, status, details


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(error):
        payload = {"error": {"message": error.message}}
        if error.details:
            payload["error"]["details"] = error.details
        return jsonify(payload), error.status

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(_error):
        db.session.rollback()
        return jsonify({"error": {"message": "The request conflicts with existing data."}}), 409

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"error": {"message": "Resource not found."}}), 404

