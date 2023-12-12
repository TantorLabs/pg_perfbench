import unittest
from pg_perfbench.context.utils import get_deparsed_arguments, sanitize_raw_args


class TestUtilsFunctions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print('\ntest_utils module')

    def test_sanitize_raw_args(self):
        given = {'a': 'line', 'b': True, 'c': None}
        expected = {'a': 'line', 'b': True, 'c': None}
        self.assertEqual(sanitize_raw_args(given), expected)

        given = {'a': 'line', 'ssh_key': 'abracadabra'}
        expected = {'a': 'line', 'ssh_key': '***********'}
        self.assertEqual(sanitize_raw_args(given), expected)

        given = {'a': 'line', 'ssh_key': 'abracadabra', 'pg_user_password': 'woosh'}
        expected = {'a': 'line', 'ssh_key': '***********', 'pg_user_password': '*****'}
        self.assertEqual(sanitize_raw_args(given), expected)

    def test_get_deparsed_arguments(self):
        given = {'a': 'line', 'b': True, 'c': None}
        expected = [('a', 'line'), ('b',)]
        self.assertEqual(get_deparsed_arguments(given), expected)


if __name__ == '__main__':
    unittest.main()
