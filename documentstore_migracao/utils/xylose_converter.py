import logging
import uuid
from typing import List
from datetime import datetime
from xylose.scielodocument import Journal, Issue

logger = logging.getLogger(__name__)


def get_journal_principal_issn_from_issue(issue) -> str:
    return issue.data.get("issue").get("v35")[0]["_"]


def parse_date(date: str) -> str:
    """Traduz datas em formato simples ano-mes-dia, ano-mes para
    o formato iso utilizado durantr a persistência do Kernel"""

    _date = None

    try:
        _date = (
            datetime.strptime(date, "%Y-%m-%d").isoformat(timespec="microseconds") + "Z"
        )
    except ValueError:
        try:
            _date = (
                datetime.strptime(date, "%Y-%m").isoformat(timespec="microseconds")
                + "Z"
            )
        except ValueError:
            _date = (
                datetime.strptime(date, "%Y").isoformat(timespec="microseconds") + "Z"
            )

    return _date


def date_to_datetime(date: str) -> datetime:
    """Transforma datas no formato ISO em objetos datetime"""
    return datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%fZ")


def set_metadata(date: str, data: any) -> List[List]:
    """Retorna a estrutura básica de um `campo` de metadata
    no formato do Kernel"""

    return [[date, data]]


def journal_to_kernel(journal):
    """Transforma um objeto Journal (xylose) para o formato
    de dados equivalente ao persistido pelo Kernel em um banco
    mongodb"""

    # TODO: Virá algo do xylose para popular o campo de métricas?

    _id = journal.any_issn()

    if not _id:
        _id = journal.scielo_issn

    if not _id:
        raise ValueError("É preciso que o periódico possua um id")

    _creation_date = parse_date(journal.creation_date)
    _metadata = {}
    _bundle = {
        "_id": _id,
        "id": _id,
        "created": _creation_date,
        "updated": _creation_date,
        "items": [],
        "metadata": _metadata,
    }

    if journal.mission:
        _mission = [
            {"language": lang, "value": value}
            for lang, value in journal.mission.items()
        ]
        _metadata["mission"] = set_metadata(_creation_date, _mission)

    if journal.title:
        _metadata["title"] = set_metadata(_creation_date, journal.title)

    if journal.abbreviated_iso_title:
        _metadata["title_iso"] = set_metadata(
            _creation_date, journal.abbreviated_iso_title
        )

    if journal.abbreviated_title:
        _metadata["short_title"] = set_metadata(
            _creation_date, journal.abbreviated_title
        )

    _metadata["acronym"] = set_metadata(_creation_date, journal.acronym)

    if journal.scielo_issn:
        _metadata["scielo_issn"] = set_metadata(_creation_date, journal.scielo_issn)

    if journal.print_issn:
        _metadata["print_issn"] = set_metadata(_creation_date, journal.print_issn)

    if journal.electronic_issn:
        _metadata["electronic_issn"] = set_metadata(
            _creation_date, journal.electronic_issn
        )

    if journal.status_history:
        _metadata["status"] = []

        for status in journal.status_history:
            _status = {"status": status[1]}

            if status[2]:
                _status["reason"] = status[2]

            # TODO: Temos que verificar se as datas são autoritativas
            _metadata["status"].append([parse_date(status[0]), _status])

    if journal.subject_areas:
        _metadata["subject_areas"] = set_metadata(
            _creation_date, [area.upper() for area in journal.subject_areas]
        )

    if journal.sponsors:
        _sponsors = [{"name": sponsor} for sponsor in journal.sponsors]
        _metadata["sponsors"] = set_metadata(_creation_date, _sponsors)

    if journal.wos_subject_areas:
        _metadata["subject_categories"] = set_metadata(
            _creation_date, journal.wos_subject_areas
        )

    if journal.submission_url:
        _metadata["online_submission_url"] = set_metadata(
            _creation_date, journal.submission_url
        )

    if journal.next_title:
        _next_journal = {"name": journal.next_title}
        _metadata["next_journal"] = set_metadata(_creation_date, _next_journal)

    if journal.previous_title:
        _previous_journal = {"name": journal.previous_title}
        _metadata["previous_journal"] = set_metadata(_creation_date, _previous_journal)

    _contact = {}
    if journal.editor_email:
        _contact["email"] = journal.editor_email

    if journal.editor_address:
        _contact["address"] = journal.editor_address

    if _contact:
        _metadata["contact"] = set_metadata(_creation_date, _contact)

    return _bundle


def issue_to_kernel(issue):
    """Transforma um objeto Issue (xylose) para o formato
    de dados equivalente ao persistido pelo Kernel em um banco
    mongodb"""

    _id = [get_journal_principal_issn_from_issue(issue)]
    _creation_date = parse_date(issue.publication_date)
    _metadata = {}
    _bundle = {
        "created": _creation_date,
        "updated": _creation_date,
        "items": [],
        "metadata": _metadata,
    }

    _year = str(date_to_datetime(_creation_date).year)
    _metadata["publication_year"] = set_metadata(_creation_date, _year)
    _id.append(_year)

    if issue.volume:
        _metadata["volume"] = set_metadata(_creation_date, issue.volume)
        _id.append("v%s" % issue.volume)

    if issue.number:
        _metadata["number"] = set_metadata(_creation_date, issue.number)
        _id.append("n%s" % issue.number)

    if issue.type is "supplement":
        _supplement = "0"

        if issue.supplement_volume:
            _supplement = issue.supplement_volume
        elif issue.supplement_number:
            _supplement = issue.supplement_number

        _metadata["supplement"] = set_metadata(_creation_date, _supplement)
        _id.append("s%s" % _supplement)

    if issue.titles:
        _titles = [
            {"language": lang, "value": value} for lang, value in issue.titles.items()
        ]
        _metadata["titles"] = set_metadata(_creation_date, _titles)

    _bundle["_id"] = "-".join(_id)
    _bundle["id"] = "-".join(_id)

    return _bundle
