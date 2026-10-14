import unittest

from cleanup_csv import clean_csv


class CleanupTests(unittest.TestCase):
    def test_explicit_rules_keep_identifiers_and_remove_only_identical_rows(self):
        source = 'id,email,amount\n001, USER@example.com ,0\n001,USER@example.com,0\n001,other@example.com,0\n001,other@example.com,0\n'
        output, report = clean_csv(source, trim=['email'], lowercase=['email'], key=['id'])
        self.assertIn('001,user@example.com,0', output)
        self.assertIn('001,other@example.com,0', output)
        self.assertEqual(report['removed_duplicate_rows'], 2)
        self.assertEqual(len(report['conflicting_keys_retained']), 1)

    def test_blank_keys_are_retained_and_reported(self):
        output, report = clean_csv('id,name\n,First\n,Second\n', trim=[], lowercase=[], key=['id'])
        self.assertEqual(report['output_rows'], 2)
        self.assertEqual(report['missing_key_rows_retained'], [2, 3])

    def test_quoted_commas_newlines_and_unicode_survive(self):
        source = 'id,notes\n007,"München, office\nsecond line"\n'
        output, report = clean_csv(source, trim=[], lowercase=[], key=[])
        self.assertEqual(output, source)
        self.assertEqual(report['changed_cells'], 0)

    def test_invalid_structure_and_unknown_columns_fail(self):
        for source in ['id,id\n1,2\n', 'id,name\n1\n', 'id,name\n1,One,Extra\n']:
            with self.assertRaises(ValueError):
                clean_csv(source, trim=[], lowercase=[], key=[])
        with self.assertRaises(ValueError):
            clean_csv('id\n1\n', trim=['missing'], lowercase=[], key=[])

    def test_zero_blank_dates_and_formula_like_text_are_preserved(self):
        source = 'id,amount,date,note\n001,0,03/04/2026,=1+1\n002,,,\n'
        output, report = clean_csv(source, trim=[], lowercase=[], key=['id'])
        self.assertEqual(output, source)
        self.assertEqual(report['output_rows'], 2)


if __name__ == '__main__':
    unittest.main()
