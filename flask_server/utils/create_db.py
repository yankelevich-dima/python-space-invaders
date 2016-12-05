import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(CURRENT_DIR))

from app import db  # NOQA

if __name__ == '__main__':
    db.create_all()
