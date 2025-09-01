import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))
os.environ['ENCRYPTION_PASSWORD'] = 'test-password'

from app.database import models

import pytest


@pytest.fixture
def db(tmp_path):
    models.DB_PATH = tmp_path / 'test.db'
    return models.ETLDatabase()


def test_instruction_crud(db):
    instruction = models.URLInstruction(
        url_pattern='https://example.com',
        instructions=[{'action': 'fetch'}],
        return_format='html',
        max_chars=100,
        description='test instruction',
    )

    instruction_id = db.add_instruction(instruction)
    assert instruction_id > 0

    fetched = db.get_instruction_for_url('https://example.com')
    assert fetched is not None
    assert fetched.url_pattern == instruction.url_pattern
    assert fetched.instructions == instruction.instructions

    assert db.delete_instruction(instruction_id)
    assert db.get_instruction_for_url('https://example.com') is None


def test_transform_rule_crud(db):
    rule = models.TransformRule(
        rule_name='rule1',
        rules=[{'find': 'a', 'replace': 'b'}],
        output_format='xml',
        description='test rule',
    )

    rule_id = db.add_transform_rule(rule)
    assert rule_id > 0

    fetched = db.get_transform_rule('rule1')
    assert fetched is not None
    assert fetched.rule_name == rule.rule_name
    assert fetched.rules == rule.rules

    assert db.delete_transform_rule(rule_id)
    assert db.get_transform_rule('rule1') is None


def test_ssh_route_crud(db):
    route = models.SSHTransferRoute(
        route_id='route1',
        hostname='example.com',
        port=22,
        username='user',
        password='secret',
        private_key='keydata',
        target_directory='/tmp',
        description='test route',
    )

    route_db_id = db.add_ssh_route(route)
    assert route_db_id > 0

    fetched = db.get_ssh_route('route1')
    assert fetched is not None
    assert fetched.route_id == 'route1'
    assert fetched.password != 'secret'
    creds = fetched.get_decrypted_credentials()
    assert creds['password'] == 'secret'
    assert creds['private_key'] == 'keydata'

    assert db.delete_ssh_route(route_db_id)
    assert db.get_ssh_route('route1') is None
