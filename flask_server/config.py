import os

BRANCH_NAME = os.getenv('BRANCH_NAME', 'develop')
SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://docker:docker@postgresql-{}:5432/space-invaders'.format(BRANCH_NAME)
SQLALCHEMY_TRACK_MODIFICATIONS = False
