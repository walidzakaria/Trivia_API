import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.wrappers import BaseRequest
from werkzeug.wsgi import responder
from werkzeug.exceptions import HTTPException, NotFound

import random

from sqlalchemy import func

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


# Create questions pagination
def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    '''
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after
    completing the TODOs
    '''
    cors = CORS(app, resources={r"/*": {"origins": "*"}})

    '''
    @TODO: Use the after_request decorator to set Access-Control-Allow
    '''

    # CORS Headers
    @app.after_request
    def after_request(response):
        response.headers.add(
            'Access-Control-Allow-Headers', 'Content-Type,Authorization,true'
        )
        response.headers.add(
            'Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS'
        )
        return response

    '''
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    '''

    @app.route('/categories')
    def retrieve_categories():
        categories = Category.query.order_by(Category.id).all()
        category_list = {category.id: category.type for category in categories}

        if len(categories) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'categories': category_list,
            'total_categories': len(Category.query.all()),
        })

    '''
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen
    for three pages.
    Clicking on the page numbers should update the questions.
    '''

    @app.route('/questions')
    def retrieve_questions():
        questions = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, questions)
        categories = Category.query.all()
        category_list = {category.id: category.type for category in categories}
        if len(current_questions) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(Question.query.all()),
            'categories': category_list
        })

    '''
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will
    be removed.
    This removal will persist in the database and when you refresh the page.
    '''

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'deleted': question_id,
                'questions': current_questions,
                'total_questions': len(Question.query.all())
            })
        except:
            abort(422)

    '''
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the
    last page of the questions list in the "List" tab.
    '''
    '''&'''
    '''
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    '''

    @app.route('/questions', methods=['POST'])
    def create_question():
        body = request.get_json()
        question = body.get('question', None)
        answer = body.get('answer', None)
        category = body.get('category', None)
        difficulty = body.get('difficulty', None)
        search = body.get('searchTerm', None)
        try:
            # if json body contains no search, a new question will be created
            if not search:
                if question is None or answer is None \
                        or category is None or difficulty is None:
                    abort(422)

                new_question = Question(
                    question=question,
                    answer=answer,
                    category=category,
                    difficulty=difficulty)
                new_question.insert()

                selection = Question.query.order_by(Question.id).all()
                current_questions = paginate_questions(request, selection)

                return jsonify({
                    'success': True,
                    'created': new_question.id,
                    'questions': current_questions,
                    'total_questions': len(Question.query.all())
                })
            else:
                # If the json request contains search, a search will be
                # implemented
                selection = Question.query.order_by(Question.id).filter(
                    Question.question.ilike(f'%{search}%'))
                current_questions = paginate_questions(request, selection)
                return jsonify({
                    'success': True,
                    'questions': current_questions,
                    'total_questions': len(selection.all())
                })
        except:
            abort(422)

    '''
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    '''

    @app.route('/categories/<int:category_id>/questions')
    def get_category_questions(category_id):
        selection = Question.query.order_by(Question.id).filter(
            Question.category == category_id)
        current_questions = paginate_questions(request, selection)
        current_category = Category.query.get(category_id)

        if len(current_questions) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(current_questions),
            'current_category': current_category.type
        })

    '''
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    '''

    @app.route('/quizzes', methods=['POST'])
    def retrieve_quizzes():
        body = request.get_json()
        previous_questions = body.get('previous_questions', None)
        quiz_category = body.get('quiz_category', None)

        if previous_questions is None or quiz_category is None:
            abort(422)

        # Get questions either by category or all
        if quiz_category['id'] != 0:
            questions = Question.query \
                .filter(Question.category == quiz_category['id']) \
                .filter(~Question.id.in_(previous_questions))
        else:
            questions = Question.query \
                .filter(~Question.id.in_(previous_questions))

        if not questions:
            abort(404)

        # Get a list of all the filtered IDs in order to select a random
        # number from it
        random_list = [question.id for question in questions]
        print(random_list)
        random_id = random.choice(random_list)
        # Select one random question against the random list
        question = Question.query.get(random_id)

        return jsonify({
            'success': True,
            'question': question.format(),
        })

    '''
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    '''

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "bad request"
        }), 400

    def view(request):
        raise NotFound()

    @responder
    def application(environ, start_response):
        request = BaseRequest(environ)
        try:
            return view(request)
        except NotFound as e:
            return not_found(request)
        except HTTPException as e:
            return e

    return app
