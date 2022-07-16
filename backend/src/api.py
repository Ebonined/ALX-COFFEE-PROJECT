from crypt import methods
import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc, asc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)


def list_dict_to_json(listdict):
    if isinstance(listdict, list):
        recipe_json = '['
        for i, parts in enumerate(listdict):
            if i < len(listdict) - 1:
                recipe_json += json.dumps(parts) + ','
            else:
                recipe_json += json.dumps(parts) + ']'
    elif isinstance(listdict, dict):
        recipe_json = '['+json.dumps(listdict)+']'
    return recipe_json

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''

# db_drop_and_create_all()

# ROUTES
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks', methods=['GET'])
def get_drinks():

    drinks_objs = Drink.query.all()

    drinks = [drink.short() for drink in drinks_objs]

    return jsonify({
        'success': True,
        'drinks': drinks
    }), 200


'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_details(payload):

    drinks_objs = Drink.query.all()

    drinks = [drink.long() for drink in drinks_objs]

    return jsonify({
        'success': True,
        'drinks': drinks
    }), 200


'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def post_drinks(payload):

    try:
        title = request.get_json()['title']
        recipe = request.get_json()['recipe']
    except Exception:
        abort(400)

    # Get new id of drink table and obtain new_id
    drinks_objs = Drink.query.with_entities(Drink.id).\
        order_by(asc(Drink.id)).all()

    ids = [tup[0] for tup in drinks_objs]
    id = 0

    for i, new_id in enumerate(ids, 1):
        if new_id - 1 == id:
            id += 1
        elif new_id - 1 > id:
            id += 1
            break
        elif i == len(ids):
            id = new_id + 1

    recipe_json = list_dict_to_json(recipe)

    new_drink = Drink(id=id, title=title, recipe=recipe_json)
    new_drink.insert()
    new_drink_array = [new_drink.short()]

    return jsonify({
        'success': True,
        'drinks': new_drink_array
    }), 200



'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def patch_drinks(payload, id):

    # get update items from the database
    try:
        title = request.get_json()['title']
        recipe = request.get_json()['recipe']
    except KeyError:
        try:
            title = request.get_json()['title']
        except KeyError:
            recipe = request.get_json()['recipe']

    # Get drink to be updated from the database
    drink_patch = Drink.query.filter_by(id=id).one_or_none()

    # Check for unknown id
    if not drink_patch:
        abort(404)

    # Do modification of drinks based on patch changes
    try:
        recipe_json = list_dict_to_json(recipe)
        drink_patch.recipe = recipe_json
    except Exception:
        pass
    try:
        drink_patch.title = title
    except Exception:
        pass
    drink_patch.update()

    # reform updated drink item to return
    drink_array = [drink_patch.short()]

    return jsonify({
        'success': True,
        'drink': drink_array
    }), 200

'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drinks(payload, id):

    # get drink to be deleted
    drink_delete = Drink.query.filter_by(id=id).one_or_none()

    # Check for unknown id
    if not drink_delete:
        abort(404)

    drink_delete.delete()

    return jsonify({
        'success': True,
        'delete': id
    }), 200

# Error Handling
'''
Example error handling for unprocessable entity
'''

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": error.name
    }), 404

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": error.name
    }), 400
'''
@TODO implement error handler for 404
    error handler should conform to general task above
'''
@app.errorhandler(403)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 403,
        "message": 'Values not provided'
    }), 403


'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''
@app.errorhandler(AuthError)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": error.status_code,
        "message": error.error['description']
    }), error.status_code
