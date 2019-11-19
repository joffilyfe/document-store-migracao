""" module to methods xml file """

import re
import logging
import itertools
import html
from io import StringIO
from lxml import etree
from xml.dom.minidom import parseString

from documentstore_migracao import config
from documentstore_migracao.utils import string, convert_html_body, files
from xylose.scielodocument import CLEANUP_MIXED_CITATION, REPLACE_TAGS_MIXED_CITATION


logger = logging.getLogger(__name__)

CLEANUP_MIXED_CITATION = re.compile(
    CLEANUP_MIXED_CITATION.pattern + "|< *?font.*?>|< *?br.*?>"
)


def str2objXML(_string):
    _string = string.normalize(_string)
    try:
        parser = etree.HTMLParser(remove_blank_text=True, recover=True)
        return etree.fromstring("<body>%s</body>" % (_string), parser=parser)
    except etree.XMLSyntaxError as e:
        logger.exception(e)
        return etree.fromstring("<body></body>")


def file2objXML(file_path):
    return loadToXML(file_path)


def objXML2file(file_path, obj_xml, pretty=False):
    files.write_file_binary(
        file_path,
        etree.tostring(
            obj_xml,
            doctype=config.DOC_TYPE_XML,
            xml_declaration=True,
            method="xml",
            encoding="utf-8",
            pretty_print=pretty,
        ),
    )


def prettyPrint_format(xml_string):
    return parseString(xml_string).toprettyxml()


def loadToXML(file):
    """Parses `file` to produce an etree instance.

    The XML can be retrieved given its filesystem path,
    an URL or a file-object.
    """
    parser = etree.XMLParser(remove_blank_text=True, no_network=True)
    xml = etree.parse(file, parser)
    return xml


def convert_html_tags_to_jats(xml_etree):
    """
        This methods receives an etree node and replace all "html tags" to
        jats compliant tags.
    """

    tags = (
        ("b", "bold"),
        ("strong", "bold"),
        ("i", "italic"),
        ("u", "underline"),
        ("small", "sc"),
    )

    for from_tag, to_tag in tags:
        for element in xml_etree.findall(".//" + from_tag):
            element.tag = to_tag

    return xml_etree


def convert_ahref_to_extlink(xml_etree):
    """
        This methods receives an etree node and replace all "a href" elements to
        a valid ext-link jats compliant format.
    """

    for ahref in xml_etree.findall(".//a"):
        uri = ahref.get("href", "")
        ahref.tag = "ext-link"
        ahref.set("ext-link-type", "uri")
        ahref.set("{http://www.w3.org/1999/xlink}href", uri)
        for key in [
            i
            for i in ahref.keys()
            if i not in ["ext-link-type", "{http://www.w3.org/1999/xlink}href"]
        ]:
            ahref.attrib.pop(key)

    return xml_etree


def cleanup_mixed_citation_text(text):
    cleaned = CLEANUP_MIXED_CITATION.sub("", text)
    for pattern, value in REPLACE_TAGS_MIXED_CITATION:
        cleaned = pattern.sub(value, cleaned)

    cleaned = re.sub(" +", " ", cleaned)
    return cleaned.strip()


def create_mixed_citation_element(citation_text: str) -> etree.Element:
    """Cria um elemento `mixed-citation` a partir do texto informado.

    Durante a criação do elemento `mixed-citation` são aplicados tratamentos no
    texto para normatizar os elementos interiores.

    Params:
        citation_text (str): Texto da citação

    Returns:
        new_mixed_citation (etree.Element): Nova citação produzida a partir do
            texto informado.
    """
    new_mixed_citation = etree.parse(
        StringIO(html.unescape(citation_text)), parser=etree.HTMLParser()
    )

    convert_html_tags_to_jats(new_mixed_citation)
    convert_ahref_to_extlink(new_mixed_citation)

    if new_mixed_citation.find(".//p") is not None:
        new_mixed_citation = new_mixed_citation.find(".//p")
    elif new_mixed_citation.find(".//body") is not None:
        new_mixed_citation = new_mixed_citation.find(".//body")

    new_mixed_citation.tag = "mixed-citation"

    return new_mixed_citation
