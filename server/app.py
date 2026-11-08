#!/usr/bin/env python3

from flask import Flask, make_response, jsonify, request, session
from flask_migrate import Migrate
from flask_restful import Api, Resource

from models import db, Article, User, ArticlesSchema, UserSchema

app = Flask(__name__)
# Flask uses this key to sign session cookies so clients cannot safely alter their contents.
app.secret_key = b'Y\xf1Xz\x00\xad|eQ\x80t \xca\x1a\x10K'
# Store the SQLite database in the server's instance folder.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

# Connect database migrations and SQLAlchemy to this Flask app.
migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)

class Login(Resource):
    def post(self):
        # Read the submitted username, then find its matching database record.
        username = request.json.get('username')
        user = User.query.filter_by(username=username).first()

        # Save the user's database ID in the session for later requests.
        session['user_id'] = user.id
        # Convert the user model to JSON and return HTTP 200 (success).
        return UserSchema().dump(user), 200

class Logout(Resource):
    def delete(self):
        # Remove the login ID; the default makes logout safe if already logged out.
        session.pop('user_id', None)
        # HTTP 204 means the request succeeded and has no response body.
        return '', 204

class CheckSession(Resource):

    def get(self):
        # Find the logged-in user's ID in the session cookie.
        user_id = session.get('user_id')
        if user_id:
            # If logged in, load and return that user's public data.
            user = User.query.get(user_id)
            return UserSchema().dump(user), 200
        # If no ID is stored, report that the request is unauthorized.
        return {}, 401

class ClearSession(Resource):

    def delete(self):
        # Clear both the article-view counter and login ID for testing.
        session['page_views'] = None
        session['user_id'] = None

        return {}, 204

class IndexArticle(Resource):
    
    def get(self):
        # Serialize every article so Flask can send the list as JSON.
        articles = [ArticlesSchema().dump(article) for article in Article.query.all()]
        return articles, 200

class ShowArticle(Resource):

    def get(self, id):
        # Count article requests in the session and allow only three views.
        session['page_views'] = 0 if not session.get('page_views') else session.get('page_views')
        session['page_views'] += 1

        if session['page_views'] <= 3:

            # Look up the requested article and serialize it for the response.
            article = Article.query.filter(Article.id == id).first()
            article_json = ArticlesSchema.dump(article)

            return make_response(article_json, 200)

        # Refuse further views after the session reaches its limit.
        return {'message': 'Maximum pageview limit reached'}, 401

# Map each URL and HTTP method to the resource that handles its requests.
api.add_resource(ClearSession, '/clear')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(CheckSession, '/check_session')
api.add_resource(IndexArticle, '/articles')
api.add_resource(ShowArticle, '/articles/<int:id>')

if __name__ == '__main__':
    # Start the development server when this file is run directly.
    app.run(port=5555, debug=True)
