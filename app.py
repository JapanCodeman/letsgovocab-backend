import datetime
from distutils.log import error
import json

import os
import pymongo
from bson.objectid import ObjectId
from bson import json_util
from dotenv import load_dotenv
from flask_jwt_extended import create_access_token
from flask_jwt_extended import JWTManager
from flask import Flask, jsonify, make_response, Response, request
from flask_cors import CORS
from pymongo import ReturnDocument
import uuid
from werkzeug.security import generate_password_hash, check_password_hash


CONNECTION_URL = os.environ.get('MONGODB_URI')
SECRET_KEY = os.environ.get('SECRET_KEY')

load_dotenv() #find_dotenv() <--- this can be put in load_dotenv() as an argument to auto search folders for .env

# CONNECTION_URL = os.getenv('MONGODB_URI') <---- for running locally

app = Flask(__name__, static_folder='./static') 
app.config['CORS_HEADERS'] = 'Content-Type'
cors = CORS(app)

app.config['JWT_SECRET_KEY'] = SECRET_KEY
jwt = JWTManager(app)

html = '''
<!doctype html>
<html>
  <head>
    <link rel="shortcut icon" href="/favicon.ico">
    <title>Hello world!</title>
  </head>
  <body>
    <p>Hello world!</p>
  </body>
</html>
'''


try:
  client = pymongo.MongoClient(CONNECTION_URL, serverSelectionTimeoutMS = 5000)

except:
  print("Error - cannot connect to database")

Database = client.get_database('letsgovocab')

users = Database.users
administrators = Database.admin

cards = Database.cards

# Test to see if flask is working
@app.route('/')
def test():
  return html

# Login route
@app.route("/login", methods=["POST"])
def create_token():
  email = request.json.get("email", None)
  password = request.json.get("password", None)

  if not email or not password:
    return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required"'})
  
  user = users.find_one({"email" : email})

  if not user:
    return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login Required"'})

  if check_password_hash(user["password"], password):
    try:
      token = create_access_token(identity={"email" : email, "role" : user["role"], 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=30)})
      return jsonify(token=token)
    except:
      return "Token unable to be distributed", error

  return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required"'})

# Register a new instructor
@app.route('/register-instructor/', methods=['POST'])
def register_one_instructor():
  first = request.json.get("first")
  last = request.json.get("last")
  email = request.json.get("email")
  course = request.json.get("course")
  password = request.json.get("password")
  logged_status = "False"

  _hashed_password = generate_password_hash(password, method='sha256')

  queryObject = {
    "first": first,
    "last": last,
    "role": 'Instructor',
    "public_id": str(uuid.uuid4()),
    "email": email,
    "course": course,
    "password": _hashed_password,
    "logged_in": logged_status
  }
  query = users.insert_one(queryObject)
  return f'{first} {last} and associated data registered to user database as Instructor'

# List all instructors from user database
@app.route('/instructors', methods=['GET'])
def find_all_instructors():
  results = list(users.find({"role" : "Instructor"}))
  for instructor in results:
    instructor["_id"] = str(instructor["_id"])

  return Response(
    response=json.dumps(results),
    status=200,
    mimetype="application/json"
  )

# Find one user by id
@app.route('/user/<id>', methods=['GET'])
def find_one_user(id):
  user = users.find_one({"_id":ObjectId(id)})
  user["_id"] = str(user["_id"])
  
  return Response(
    response=json.dumps(user),
    status=200,
    mimetype="application/json"
  )

# Find one user by public id (uuid)
@app.route('/user-by-public-id', methods=['GET'])
def user_by_public_id():
  public_id = request.json.get("public_id")
  user = users.find_one({"public_id": public_id})
  del user["_id"]

  return Response(
    response=json.dumps(user),
    status=200,
    mimetype="application/json"
  )

# Look user up by e-mail
@app.route('/user-email/<email>', methods=['GET'])
def get_user_by_email(email):
  user = users.find_one({"email":email})
  user["_id"] = str(user["_id"])
  
  return Response(
    response=json.dumps(user),
    status=200,
    mimetype="application/json"
  )

# Update one instructor
@app.route('/update-user/<id>', methods=['PATCH', 'PUT'])
def update_one_user(id):
  id = ObjectId(id)

  updateObject = request.get_json()
  jsonify(updateObject)

  result = users.find_one_and_update({"_id" : id}, 
  { "$set" : updateObject },
  return_document = ReturnDocument.AFTER)

  return "User Updated"

# Delete one user
@app.route('/delete-user/<id>', methods=['DELETE'])
def delete_one_user(id):
  id = ObjectId(id)
  id_call = {"_id" : id}
  id = users.delete_one(id_call)
  return 'User deleted'

# Delete entire instructor document
@app.route('/delete-all-users/', methods=['DELETE'])
def delete_all_users():
  result = users.delete_many({})
  return 'User table dropped'

# Register a new student
@app.route('/register-student', methods=['POST'])
def register_one_student():
  first = request.json.get("first")
  last = request.json.get("last")
  email = request.json.get("email")
  course = request.json.get("course")
  password = request.json.get("password")
  logged_status = "False"
  # scheduled_study_set = 0
  full_card_collection = []
  # vocabulary_box_one = []
  # vocabulary_box_two = []
  # vocabulary_box_three = []
  # vocabulary_box_four = []
  # vocabulary_box_five = []
  # vocabulary_box_six = []
  # vocabulary_box_seven = []

  _hashed_password = generate_password_hash(password, method='sha256')

  queryObject = {
    "first" : first,
    "last" : last,
    "email" : email,
    "role" : "Student",
    "course" : course,
    "password" : _hashed_password,
    "logged_in": logged_status,
    "public_id": str(uuid.uuid4()),
    # "current_box_index": 0,
    "full_card_collection": full_card_collection,
    # "scheduled_study_set": scheduled_study_set,
    # "vocabulary_box_one": vocabulary_box_one,
    # "vocabulary_box_two": vocabulary_box_two,
    # "vocabulary_box_three": vocabulary_box_three,
    # "vocabulary_box_four": vocabulary_box_four,
    # "vocabulary_box_five": vocabulary_box_five,
    # "vocabulary_box_six": vocabulary_box_six,
    # "vocabulary_box_seven": vocabulary_box_seven
  }
  query = users.insert_one(queryObject)
  return 'registered'

@app.route('/users-by-course/<course>', methods=['GET'])
def get_users_by_class(course):
  user_results = []
  for user in users.find({"course":course}):
    user["_id"] = str(user["_id"])
    user_results.append(user)

  return Response(
  response=json_util.dumps(user_results),
  status=200,
  mimetype="application/json"
  )

@app.route('/student-email/<email>', methods=['GET'])
def get_student_by_email(email):
  student = users.find_one({"email":email})
  student["_id"] = str(student["_id"])
  
  return Response(
    response=json.dumps(student),
    status=200,
    mimetype="application/json"
  )

@app.route('/students/', methods=['GET'])
def find_all_students():
  results = list(users.find({"role" : "Student"}))
  for student in results:
    student["_id"] = str(student["_id"])

  return Response(
    response=json.dumps(results),
    status=200,
    mimetype="application/json"
  )

# Update one user by email
@app.route('/update-user-by-email/<email>', methods=['PATCH', 'PUT', 'GET'])
def update_one_user_email(email):
  updateObject = request.get_json()
  jsonify(updateObject)

  result = users.find_one_and_update({"email" : email}, 
  { "$set" : updateObject }, 
  return_document=ReturnDocument.AFTER)
  return "User updated by email"

# Delete entire student document
@app.route('/delete-all-students', methods=['DELETE'])
def delete_all_students():
  result = users.delete_many({"role" : "Student" })
  return 'All students deleted'

# Create many cards
@app.route('/create-cards', methods=['POST'])
def create_cards():
  cards_list = request.get_json()

  for card in cards_list:
    card["public_id"] = str(uuid.uuid4())

  result = cards.insert_many(cards_list)
  return 'Multiple cards uploaded'

# View all cards
@app.route('/cards', methods=['GET'])
def get_all_cards():
  results = list(cards.find())
  for card in results:
    card["_id"] = str(card["_id"])

  return Response(
    response=json.dumps(results),
    status=200,
    mimetype="application/json"
  )

# Get cards by course
@app.route('/cards-course/<course>', methods=['GET'])
def get_cards_by_course(course):
  results = list(cards.find({'course' : course}))
  for card in results:
    card["_id"] = str(card["_id"])

  return Response(
    response=json.dumps(results),
    status=200,
    mimetype="application/json"
  )


# Get card sets by instructor
@app.route('/sets-by-instructor/<user>', methods=['GET', 'POST'])
def get_sets_by_instructor(user):
  
  card_sets = cards.find({
    "created_by" : user
  })

  card_sets_cur = list(card_sets)

  unique_sets = []

  for card in card_sets_cur:
    card["_id"] = str(card["_id"])
    if card["set_name"] not in unique_sets:
      unique_sets.append(card["set_name"])
    else:
      continue

  return Response(
    response=json.dumps(unique_sets),
    status=200,
    mimetype="application/json"
  )

# Get cards by set name
@app.route('/cards-by-setname/<setname>', methods=['GET'])
def cards_by_setname(setname):
  set = cards.find({
    "set_name" : setname
  })

  card_sets = list(set)

  for card in card_sets:
    card["_id"] = str(card["_id"])

  return Response(
  response=json.dumps(card_sets),
  status=200,
  mimetype="application/json"
)

# Get card public ids by set name
@app.route('/card-public-id-by-setname/<setname>', methods=['GET'])
def cards_by_public_id(setname):
  setname = cards.find({
    "set_name" : setname
  })

  card_ids = []

  for card in setname:
    card_ids.append(card["public_id"])

  return Response(
  response=json.dumps(card_ids),
  status=200,
  mimetype="application/json"
)

# Get cards by course
@app.route('/cards-by-course/<course>', methods=['GET'])
def cards_by_course(course):
  set = cards.find({
    "course" : course
  })

  deck_name = []

  for card in set:
    set_name = card["set_name"]
    if set_name not in deck_name: 
      deck_name.append(set_name)

  return Response(
    response=json.dumps(deck_name),
    status=200,
    mimetype="application/json"
  )

# Get all new cards so they can be assigned to box 1
@app.route('/get-todays-cards/<id>')
def get_todays_cards(id):
  id = ObjectId()

  student = users.find({
    "_id" : id
  })
  student["_id"] = str(student["_id"])

  return Response(
  response=json.dumps(student),
  status=200,
  mimetype="application/json"
)

# Get all unboxed cards - needed for future revisions
@app.route('/get-new-cards/<course>', methods=['GET'])
def get_new_cards(course):
  new_cards = cards.find({
    "course" : course
  })

  new_card_ids = []

  for card in new_cards:
    new_card_ids.append(str(card["public_id"]))

  return Response(
    response=json.dumps(new_card_ids),
    status=200,
    mimetype="application/json"
  )  

@app.route('/get-card-by-id/<public_id>', methods=['GET'])
def get_card_by_id(public_id):

  card = cards.find_one({
    "public_id" : public_id
  })
  card.pop("_id")

  return Response(
  response=json.dumps(card),
  status=200,
  mimetype="application/json"
)

# Takes an array of ids and returns all the cards associated with those as objects in an array
@app.route('/get-cards-by-ids', methods=['GET', 'POST'])
def get_cards_by_ids():
  list_of_cards = request.get_json()
  return_cards = []

  for card in list_of_cards:
    card = cards.find({
      "public_id" : card
    })
    del card["_id"]
    return_cards.append(card)

  return Response(
  response=json.dumps(return_cards),
  status=200,
  mimetype="application/json"
)

# Update a card 
@app.route('/update-card/<id>', methods=['PATCH'])
def update_a_card(id):
  id = ObjectId(id)
  id_call = {"_id" : id}
  request_params = request.get_json()
  updateObject = request_params

  result = cards.find_one_and_update(id_call, {"$set":updateObject}, return_document=ReturnDocument.AFTER)
  return f'Card information updated {updateObject}'

@app.route('/delete-card/<id>', methods=['DELETE'])
def delete_a_card(id):
  id = ObjectId(id)
  id_call = {"_id" : id}

  result = cards.find_one_and_delete(id_call)
  return "Card deleted"

@app.route('/delete-card-set/<set_name>', methods=['DELETE'])
def delete_a_set(set_name):
  delete_set = {"set_name" : set_name}

  result = cards.delete_many(delete_set)
  
  return Response(
  status=200,
  mimetype="application/json"
)

# Delete all cards
@app.route('/delete-all-cards', methods=['DELETE'])
def delete_all_cards():
  result = cards.delete_many({})
  return 'Cards table dropped'

# Register a new administrator
@app.route('/register-admin', methods=['POST'])
def register_one_admin():
  first = request.json.get("first")
  last = request.json.get("last")
  email = request.json.get("email")
  password = request.json.get("password")
  logged_status = "False"

  _hashed_password = generate_password_hash(password, method='sha256')

  queryObject = {
    "first" : first,
    "last" : last,
    "email" : email,
    "role" : 'Administrator',
    "password" : _hashed_password,
    "logged_in": logged_status
  }
  query = users.insert_one(queryObject)
  return f'{first} {last} registered with administrator privileges.'

# Find User by email
@app.route('/user-by-email/<email>', methods=['GET'])
def find_admin_by_email(email):
  user = users.find_one({"email":email})
  user["_id"] = str(user["_id"])

  return Response(
    response=json.dumps(user),
    status=200,
    mimetype="application/json"
  )

# Find all administrators
@app.route('/administrators', methods=['GET'])
def find_all_admins():
  results = list(users.find({"role" : "Administrator"}))
  for admin in results:
    admin["_id"] = str(admin["_id"])

  return Response(
    response=json.dumps(results),
    status=200,
    mimetype="application/json"
  )

# Update one administrator
@app.route('/update-administrator/<id>', methods=['PATCH'])
def update_one_administrator(id):
  request_params = request.get_json()
  updateObject = request_params
  id = ObjectId(id)
  id_call = {"_id" : id}

  result = administrators.find_one_and_update(id_call, {"$set":updateObject}, return_document=ReturnDocument.AFTER)
  return f'{result["first"]} {result["last"]}\'s information updated {updateObject}'


# Update one administrator by email
@app.route('/update-administrator-by-email/<email>', methods=['PATCH'])
def update_one_administrator_email(email):
  request_params = request.get_json()
  updateObject = request_params
  email = {"email" : email}

  result = administrators.find_one_and_update(email, {"$set":updateObject}, return_document=ReturnDocument.AFTER)
  return f'{result["first"]} {result["last"]}\'s information updated {updateObject}'

# Delete one administrator 
@app.route('/delete-administrator/<id>', methods=['DELETE'])
def delete_one_administrator(id):
  id_call = {"_id":ObjectId(id)}


  result = administrators.find_one_and_delete(id_call)
  return f'Administrator removed from database.'

if __name__ == '__main__':
  app.run(debug=False) # Change to false before deploying?