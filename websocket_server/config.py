import yaml
import logging
import os
from sqlalchemy import create_engine


def load_yaml_config(path_to_file):
    with open(path_to_file, 'r') as yaml_config:
        return yaml.load(yaml_config)


config = load_yaml_config('config.yaml')

GAME_CONFIG = config['GAME_PARAMS']
ENEMY_CONFIG = config['ENEMY_PARAMS']
PLATFORM_CONFIG = config['PLATFORM_PARAMS']
PLAYER_CONFIG = config['PLAYER_PARAMS']

BRANCH_NAME = os.getenv('BRANCH_NAME', 'develop')
SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://docker:docker@postgresql-{}:5432/space-invaders'.format(BRANCH_NAME)
SQLALCHEMY_ENGINE = create_engine(SQLALCHEMY_DATABASE_URI)

LOGGER = logging.getLogger(__name__)
formatter = logging.Formatter('[%(asctime)s] - %(levelname)s - [%(game_id)s] - %(message)s')

sh = logging.StreamHandler()
sh.setFormatter(formatter)
sh.setLevel(logging.DEBUG)

LOGGER.addHandler(sh)
LOGGER.setLevel(logging.DEBUG)
