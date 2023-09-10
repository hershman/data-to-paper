import time

import numpy as np
import requests
import re

from dataclasses import dataclass
from typing import List, Dict, Optional

from data_to_paper.env import S2_API_KEY
from data_to_paper.exceptions import data_to_paperException
from data_to_paper.latex.clean_latex import replace_special_latex_chars
from data_to_paper.servers.base_server import DictServerCaller
from data_to_paper.servers.crossref import ServerErrorCitationException
from data_to_paper.servers.types import Citation
from data_to_paper.utils.highlighted_text import print_red
from data_to_paper.utils.nice_list import NiceList


# TODO: this is part of the WORKAROUND. remove it when the bug is fixed.
def remove_word(string, word):
    import re
    pattern = re.compile(r'\b{}\b\s*'.format(re.escape(word)), re.IGNORECASE)
    return re.sub(pattern, '', string)


HEADERS = {
    'x-api-key': S2_API_KEY
}

PAPER_SEARCH_URL = 'https://api.semanticscholar.org/graph/v1/paper/search'
EMBEDDING_URL = 'https://model-apis.semanticscholar.org/specter/v1/invoke'


class SemanticCitation(Citation):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._bibtex_id = None

    @property
    def bibtex(self) -> str:
        bibtex = self['citationStyles']['bibtex']
        # remove commas from authors:
        authors = bibtex.split('author = {', 1)[1].split('},', 1)[0]
        authors = authors.replace(', ', ' and ')
        bibtex = bibtex.split('author = {', 1)[0] + 'author = {' + authors + '},' + bibtex.split('},', 1)[1]
        bibtex = bibtex.encode('ascii', 'ignore').decode('utf-8')
        return replace_special_latex_chars(bibtex)

    @property
    def bibtex_id(self) -> str:
        if self._bibtex_id is None:
            bibtex_id = self['citationStyles']['bibtex'].split('{', 1)[1].split(',\n', 1)[0]
            # replace non unicode chars with unicode equivalent:
            bibtex_id = bibtex_id.encode('ascii', 'ignore').decode('utf-8')
            # characters not allowed in bibtex ids are replaced with ' ':
            pattern = r'[{}(),\\\"-#~^:\'`ʹ]'
            bibtex_id = re.sub(pattern, ' ', bibtex_id)
            self._bibtex_id = bibtex_id
        return self._bibtex_id

    @property
    def title(self) -> Optional[str]:
        return self.get('title', None)

    @property
    def abstract(self) -> Optional[str]:
        return self.get('abstract', None)

    @property
    def journal(self) -> Optional[str]:
        try:
            return self['journal']['name']
        except (KeyError, TypeError):
            return None

    @property
    def year(self) -> Optional[str]:
        return self.get('year', None)

    @property
    def influence(self) -> int:
        return self['influentialCitationCount']

    @property
    def embedding(self) -> Optional[np.ndarray]:
        return self.get('embedding', None)

    @property
    def tldr(self) -> Optional[str]:
        tldr = self.get('tldr', None)
        if tldr is None:
            return None
        return tldr['text']


@dataclass
class ServerErrorNoMatchesFoundForQuery(data_to_paperException):
    """
    Error raised server wasn't able to find any matches for the query.
    """
    query: str

    def __str__(self):
        return f"Server wasn't able to find any matches for the query:\n {self.query}\n please try a different query."


class SemanticScholarPaperServerCaller(DictServerCaller):
    """
    Search for citations with abstracts in Semantic Scholar.
    """

    file_extension = "_semanticscholar_paper.bin"

    @staticmethod
    def _get_server_response(query, rows=25) -> List[dict]:
        """
        Get the response from the semantic scholar server as a list of dict citation objects.
        """

        # TODO: THIS IS A WORKAROUND FOR A BUG IN SEMANTIC SCHOLAR. REMOVE WHEN FIXED.
        words_to_remove_in_case_of_zero_citation_error = \
            ('the', 'of', 'in', 'and', 'or', 'a', 'an', 'to', 'for', 'on', 'at', 'by', 'with', 'from', 'as', 'into',
             'through', 'effect')

        while True:
            params = {
                "query": query,
                "limit": min(rows * 2, 100),  # x2 more to make sure we get enough results after removing faulty ones
                "fields": "title,url,abstract,tldr,journal,year,citationStyles,embedding,influentialCitationCount",
            }
            print_red(f'QUERYING SEMANTIC SCHOLAR FOR: "{query}"')
            response = requests.get(PAPER_SEARCH_URL, headers=HEADERS, params=params)

            if response.status_code == 504:
                print_red("ERROR: Server timed out. We wait for 5 sec and tet's try again.")
                time.sleep(5)
                continue

            if response.status_code != 200:
                raise ServerErrorCitationException(status_code=response.status_code, text=response.text)


            data = response.json()
            try:
                papers = data["data"]
            except KeyError:
                papers = []

            if len(papers) > 0:  # if there is no server bug
                papers = [paper for paper in papers if SemanticCitation(paper).bibtex_id != 'None']
                return papers[:rows]

            for word in words_to_remove_in_case_of_zero_citation_error:
                redacted_query = remove_word(query, word)
                if redacted_query != query:
                    print_red(f"NO MATCHES!  REMOVING '{word}' FROM QUERY")
                    query = redacted_query
                    break
            else:
                # failing gracefully
                return []

    @staticmethod
    def _post_process_response(response, args, kwargs):
        """
        Post process the response from the server.
        """
        query = args[0] if len(args) > 0 else kwargs.get('query', None)
        citations = NiceList(separator='\n', prefix='[\n', suffix='\n]')
        for rank, paper in enumerate(response):

            msg = ''
            embedding = None
            if 'embedding' not in paper:
                msg = 'No embedding attr'
            elif paper['embedding'] is None:
                msg = 'None embedding attr'
            elif 'model' not in paper['embedding']:
                msg = 'No model attr'
            elif paper['embedding']['model'] not in ['specter@v0.1.1', 'specter_v1']:
                msg = 'Wrong model attr'
            else:
                try:
                    assert len(paper['embedding']['vector']) == 768
                except (AssertionError, KeyError, IndexError, TypeError):
                    msg = 'Wrong vector attr'
                else:
                    embedding = np.array(paper['embedding']['vector'])
            paper = paper.copy()
            paper['embedding'] = embedding

            citation = SemanticCitation(paper, search_rank=rank, query=query)

            if msg:
                print_red(f"ERROR: {msg}. ({citation.year}) {citation.journal}, {citation.title}")

            if len(citation.bibtex_id) <= 4:
                print_red(f"ERROR: bibtex_id is too short. skipping. Title: {citation.title}")
                continue
            citations.append(citation)
        return citations


class SemanticScholarEmbeddingServerCaller(DictServerCaller):
    """
    Embed "paper" (title + abstract) using SPECTER Semantic Scholar API.
    """

    file_extension = "_semanticscholar_embedding.bin"

    @staticmethod
    def _get_server_response(paper: Dict[str, str]) -> np.ndarray:
        """
        Send the paper to the SPECTER Semantic Scholar API and get the embedding.
        """
        # check that the paper has id, title and abstract attributes, if not raise an error
        if not all(key in paper for key in ["paper_id", "title", "abstract"]):
            raise ValueError("Paper must have 'paper_id', 'title' and 'abstract' attributes.")

        response = requests.post(EMBEDDING_URL, json=[paper])

        if response.status_code != 200:
            raise ServerErrorCitationException(status_code=response.status_code, text=response.text)

        paper_embedding = response.json()["preds"][0]["embedding"]

        return np.array(paper_embedding)

    @staticmethod
    def _post_process_response(response, args, kwargs):
        """
        Post process the response from the server.
        """
        return response


SEMANTIC_SCHOLAR_SERVER_CALLER = SemanticScholarPaperServerCaller()
SEMANTIC_SCHOLAR_EMBEDDING_SERVER_CALLER = SemanticScholarEmbeddingServerCaller()
