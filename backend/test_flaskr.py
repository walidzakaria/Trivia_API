import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        # Please change the below settings to work on your own machine
        self.username = "postgres"
        self.password = "wwzzaahh"
        self.database_path = f"postgresql+psycopg2://{self.username}:{self.password}@localhost:5432/{self.database_name}"

        # self.database_path = "postgres://{}/{}".format('localhost:5432', self.database_name)
        setup_db(self.app, self.database_path)

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()

    def tearDown(self):
        """Executed after reach test"""
        pass

    """
    TODO
    Write at least one test for each test for successful operation and for expected errors.
    """

    def test_get_categories(self):
        res = self.client().get('/categories')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['total_categories'])
        self.assertTrue(len(data['categories']))

    def test_404_get_wrong_endpoint(self):
        res = self.client().get('/wrong_endpoint_path')
        data = json.loads(res.data)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')
        self.assertEqual(res.status_code, 404)

    def test_get_paginated_questions(self):
        res = self.client().get('/questions')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['total_questions'])
        self.assertTrue(len(data['questions']))

    def test_404_send_requesting_beyond_valid_page(self):
        res = self.client().get('/questions?page=1000')
        data = json.loads(res.data)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')
        self.assertEqual(res.status_code, 404)

    def test_delete_question(self):
        res = self.client().delete('/questions/2')
        data = json.loads(res.data)
        question = Question.query.filter(Question.id == 2).one_or_none()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(data['deleted'], 2)
        self.assertTrue(data['total_questions'])
        self.assertTrue(len(data['questions']))
        self.assertEqual(question, None)

    def test_422_question_does_not_exist(self):
        res = self.client().delete('/questions/1000')
        data = json.loads(res.data)
        question = Question.query.filter(Question.id == 1000).one_or_none()
        self.assertEqual(res.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'unprocessable')

    def test_create_new_question(self):
        res = self.client().post('/questions', json={
            "question": "this is my first question?",
            "answer": "yes",
            "category": 2,
            "difficulty": 1
        })
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['created'])
        self.assertTrue(len(data['questions']))

    def test_create_new_question_failure(self):
        res = self.client().post('/questions', json={
            "category": 2,
            "difficulty": 1
        })
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'unprocessable')

    def test_get_question_search_with_result(self):
        res = self.client().post('/questions', json={'searchTerm': 'title'})
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['total_questions'])
        self.assertEqual(len(data['questions']), 2)

    def test_get_question_search_without_result(self):
        res = self.client().post('/questions', json={'searchTerm': 'applejack'})
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(data['total_questions'], 0)
        self.assertEqual(len(data['questions']), 0)

    def test_get_questions_by_category(self):
        res = self.client().get('/categories/5/questions')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['total_questions'])
        self.assertEqual(len(data['questions']), 2)

    def test_get_questions_by_category_no_exiting(self):
        res = self.client().get('/categories/100/questions')
        data = json.loads(res.data)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')
        self.assertEqual(res.status_code, 404)

    def test_get_questions_by_quizzes(self):
        res = self.client().post('/quizzes', json={
            "previous_questions": [1, 2, 3],
            "quiz_category": Category.query.first().format()
        })
        question = Question.query.filter(Question.category == 4).filter(Question.id > 3).first()
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['question'])
        self.assertEqual(len(data['question']), question.id)

    def test_get_questions_by_quizzes_failure(self):
        res = self.client().post('/quizzes', json={})
        question = Question.query.filter(Question.category == 4).filter(Question.id > 3).first()
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'unprocessable')


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
