from app.models import User, Post
from app.api.errors import error_response
from app.main import bp
from flask import jsonify
from app import db
import json

@bp.route('/api/posts')
def api_posts():
    posts = Post.query.all()  # Ruft alle posts ab
    posts_dict = []
    for post in posts:
        posts_dict.append(post.todict())
    return jsonify(posts_dict)
    


