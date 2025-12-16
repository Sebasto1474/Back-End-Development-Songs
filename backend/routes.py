from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################

songscoll = db.songs

@app.route("/health", methods=["GET"])
def health():
    return jsonify(dict(status="OK")), 200

@app.route("/count", methods=["GET"])
def count():
    count = songscoll.count_documents({})
    return {"count" : count}, 200

@app.route("/song", methods=["GET"])
def songs():
    songs_list = list(db.songs.find({}))
    return {"songs" : str(songs_list)}, 200

@app.route("/song/<int:id>", methods=["GET"])
def get_song_by_id(id):

    query = str(db.songs.find_one({"id" : id}))

    if query == "None":
        return {"message" : "cancion con id no encontrada"}, 404
    else:
        return {"song" : query}, 200

@app.route("/song", methods=["POST"])
def create_song():
    data = request.get_json()

    existing_song = db.songs.find_one({"id": data.get("id")})
    if existing_song:
        return {"message": f"la cancion con id {data['id']} ya esta presente"}, 302
    
    new_song = db.songs.insert_one(data)

    return {"inserted id": parse_json(new_song.inserted_id)}, 201

@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):
    data = request.get_json()

    existing_song = db.songs.find_one({"id": id})

    if existing_song:
        db.songs.update_one({"id" : id},{"$set": data})
        
        updated_song = db.songs.find_one({"id" : id})

        if updated_song.modified_count > 0:
            return parse_json(updated_song), 201
        else:
            return {"message": "song found, but nothing updated"}, 200
        
    
    return {"message" : "cancion no encontrada"}, 404


@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):
    del_song = db.songs.delete_one({"id": id})

    if del_song.deleted_count == 0:
        return {"message" : "cancion no encontrada"},404
    elif del_song.deleted_count == 1:
        return "", 204
   


