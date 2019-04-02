import unittest
from unittest.mock import patch

from documentstore_migracao.main import process, main, migrate_issues


class TestMainProcess(unittest.TestCase):
    @patch("documentstore_migracao.processing.extrated.extrated_all_data")
    def test_arg_extrateFiles(self, mk_extrated_all_data):

        process(["--extrateFiles"])
        mk_extrated_all_data.assert_called_once_with()

    @patch("documentstore_migracao.processing.extrated.extrated_selected_journal")
    def test_arg_issn_journal(self, mk_extrated_selected_journal):

        process(["--issn-journal", "1234-5678"])
        mk_extrated_selected_journal.assert_called_once_with("1234-5678")

    @patch("documentstore_migracao.processing.conversion.conversion_article_ALLxml")
    def test_arg_conversionFiles(self, mk_conversion_article_ALLxml):

        process(["--conversionFiles"])
        mk_conversion_article_ALLxml.assert_called_once_with()

    @patch("documentstore_migracao.processing.conversion.conversion_article_xml")
    def test_arg_pathFile(self, mk_conversion_article_xml):

        process(["--pathFile", "/tmp/example.xml"])
        mk_conversion_article_xml.assert_called_once_with("/tmp/example.xml")

    @patch("documentstore_migracao.processing.reading.reading_article_ALLxml")
    def test_arg_readFiles(self, mk_reading_article_ALLxml):

        process(["--readFiles"])
        mk_reading_article_ALLxml.assert_called_once_with()

    @patch("documentstore_migracao.processing.validation.validator_article_ALLxml")
    def test_arg_validationFiles(self, mk_validator_article_ALLxml):

        process(["--validationFiles"])
        mk_validator_article_ALLxml.assert_called_once_with()

    @patch("documentstore_migracao.processing.generation.article_ALL_html_generator")
    def test_arg_generationFiles(self, mk_article_ALL_html_generator):

        process(["--generationFiles"])
        mk_article_ALL_html_generator.assert_called_once_with()

    @patch("documentstore_migracao.processing.validation.validator_article_xml")
    def test_arg_valideFile(self, mk_validator_article_xml):

        process(["--valideFile", "/tmp/example.xml"])
        mk_validator_article_xml.assert_called_once_with("/tmp/example.xml")

    def test_not_arg(self):

        with self.assertRaises(SystemExit) as cm:
            process([])
            self.assertEqual("Vc deve escolher algum parametro", str(cm.exception))


class TestMainMain(unittest.TestCase):
    @patch("documentstore_migracao.main.process")
    def test_main_process(self, mk_process):

        mk_process.return_value = 0
        self.assertRaises(SystemExit, main)
        mk_process.assert_called_once_with(["test"])


class TestMigrateIssueCommands(unittest.TestCase):
    def test_data_source_is_required(self):
        with self.assertRaises(SystemExit):
            migrate_issues([])

    @patch("documentstore_migracao.processing.pipeline.process_isis_issue")
    def test_pipeline_interface_is_called_once(self, process_isis_issue_mock):
        migrate_issues(["-d", "i"])
        process_isis_issue_mock.assert_called_once_with(extract=False)

    @patch("documentstore_migracao.processing.pipeline.process_isis_issue")
    def test_pipeline_should_extract_if_extract_argument_is_passed(
        self, process_isis_issue_mock
    ):
        migrate_issues(["-d", "i", "-e"])
        process_isis_issue_mock.assert_called_once_with(extract=True)

    def test_data_source_has_scielo_manager_data_flag(self):
        migrate_issues(["-d", "m"])