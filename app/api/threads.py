from app.models import User, Thread
from app.api.errors import error_response
from app.main import bp
from flask import jsonify
from app import db
import json

@bp.route('/api/threads')
def api_threads():
    threads = Thread.query.all()  # Ruft alle Threads ab
    threads_dict = []
    for thread in threads:
        threads_dict.append(thread.todict())
    return jsonify(threads_dict)
    


