from app.models import User, Post
from app.api.errors import error_response
from app.main import bp
from flask import jsonify
from app import db
import json

@bp.route('/api/posts')
def api_posts():
    posts = Post.query.all()  # Ruft alle posts ab
    posts_dict = []  # Liste zur Speicherung der Posts
    for post in posts:
        posts_dict.append(post.todict())  # Fügt das Dictionary jedes Beitrags zur Liste hinzu
    return jsonify(posts_dict)  # Gibt die Beitrag-Dictionaries im JSON-Format aus



