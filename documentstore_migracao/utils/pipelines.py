import logging

import plumber
from lxml import etree

from documentstore_migracao.utils import xml as xml_utils


@plumber.filter
def fetch_article_body(context: dict) -> dict:
    """Incorpora o corpo `html` do artigo dentro do contexto de processamento."""

    context["body"] = body = context["etree"].find(".//body")

    if not body is not None and len(body.findtext("p") or "") > 0:
        raise ValueError(
            "Cannot find a HTML body to operate in. Please vetify your input."
        )

    return context


@plumber.filter
def remove_article_body_when_text_is_available_only_in_pdf(context: dict) -> dict:
    """Remove o corpo do documento quando o texto completo está disponível
    apenas em pdf."""

    def find_pdf_links(body: etree.Element) -> list:
        TEXT_LINK_FOR_PDF = [
            "texto completo disponível apenas em pdf.",
            "full text available only in pdf format.",
            "texto completo solamente en formato pdf.",
        ]
        renditions = []

        for node in body.findall(".//a"):
            if not node.get("href", "").endswith(".pdf"):
                continue

            if node.text is not None and node.text.lower() in TEXT_LINK_FOR_PDF:
                renditions.append(node)

        return renditions

    has_self_uri_tags = len(context["etree"].findall(".//self-uri")) > 0
    full_text_available_in_pdf = len(find_pdf_links(context["body"])) > 0

    if has_self_uri_tags and full_text_available_in_pdf:
        parent = context["body"].getparent()
        parent.remove(context["body"])

    return context


class ArticleTransformationsPipeline:
    """Pipeline responsável por executar transformações no XML envolvendo
    o `body` e elementos vizinhos."""

    def __init__(self, **kwargs):
        self.context = kwargs
        self.pipelines = plumber.Pipeline(
            fetch_article_body, remove_article_body_when_text_is_available_only_in_pdf,
        )

    def deploy(self) -> dict:
        return next(self.pipelines.run(self.context, rewrap=True))
