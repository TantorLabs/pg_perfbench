import unittest
from pg_perfbench.context.schemes.db import DBParameters


class TestDBParametersConstruction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print('\nTesting the DBParameters context scheme')

    def test_db_params_construction_with_default_params(self):
        given = {
            'pg_host': '127.0.0.1',
            'pg_port': '5432',
            'pg_user': 'test_user',
            'pg_database': 'example_database',
            'pg_user_password': 'test_user_password',
            'pg_data_path': 'etc/postgresql/15/main',
            'pg_bin_path': 'usr/lib/postgresql/15/bin',
        }
        db = DBParameters.model_validate(given)
        self.assertTrue(hasattr(db, 'pg_host'))
        self.assertTrue(hasattr(db, 'pg_port'))
        self.assertTrue(hasattr(db, 'pg_database'))
        self.assertTrue(hasattr(db, 'pg_user'))
        self.assertTrue(hasattr(db, 'pg_password'))
        self.assertTrue(hasattr(db, 'pg_bin_path'))

    def test_db_params_construction_with_empty_user_password(self):
        given = {
            'pg_host': '127.0.0.1',
            'pg_port': '5432',
            'pg_user': '',
            'pg_database': 'example_database',
            'pg_user_password': '',
            'pg_data_path': 'etc/postgresql/15/main',
            'pg_bin_path': 'usr/lib/postgresql/15/bin',
        }
        db = DBParameters.model_validate(given)
        self.assertTrue(hasattr(db, 'pg_host'))
        self.assertTrue(hasattr(db, 'pg_port'))
        self.assertTrue(hasattr(db, 'pg_database'))
        self.assertTrue(hasattr(db, 'pg_user'))
        self.assertTrue(hasattr(db, 'pg_password'))
        self.assertTrue(hasattr(db, 'pg_bin_path'))


if __name__ == '__main__':
    unittest.main()
