
import json
import logging
import os, sys
from pprint import pprint

from typing import Dict
from dataclasses import asdict

from elasticsearch import Elasticsearch
from elasticsearch import helpers

sys.path.append('../03_sqlite_to_postgres')
import db

logger = logging.getLogger(__name__)
logger.setLevel('INFO')


class EsManager:
    def __init__(self, index, chunk_size=1000):
        host=os.environ["ELASTIC_HOST"]
        port=os.environ["ELASTIC_PORT"]

        self.es_client = Elasticsearch([f'{host}:{port}'])
        logger.info(self.es_client.ping())

        self.__chunk_size = chunk_size
        self.__index = index

    def create_index(self, schema: Dict) -> None:
        '''
        Create an ES index.
        :param index_name: Name of the index.
        :param mapping: Mapping of the index
        '''
        logger.info(f'### Elastic: Creating index {self.__index} with the following schema: \
                     {json.dumps(schema, indent=2)}')
        self.es_client.indices.create(index=self.__index, body=schema, ignore=400)
    
    def delete_index(self) -> None:
        # ignore 404 and 400
        self.es_client.indices.delete(index=self.__index, ignore=[400, 404])


    def create_schema(self, schema_file: str) -> None:
        if not os.path.exists(schema_file): 
            with open(schema_file, 'w') as fp:
                fp.write('{}')
        
        with open(schema_file) as fp:
            schema = json.load(fp)
            self.create_index(schema)


    def populate_index(self, docs: list) -> None:
        '''
        Populate an index from docs list
        :param docs: The list of prepared docs to insert.
        :param index_name: Name of the index to which documents should be written.
        '''
        logger.info(f'### Elastic: Bulk Write {len(docs)} docs to {self.__index}')
        k = [{
                "_index": self.__index,
                "_id"   : doc['id'],
                "_source": json.dumps(doc),
             } for doc in docs]

        helpers.bulk(self.es_client, k)
        logger.info('### Elastic: Written last doc in batch')

    def search(self, term):
        query_body = {
            "query": {
                "bool": {
                "must": {
                    "match": {      
                    "genre": term
                    }
                }
                }
            }
        }
        pprint(self.es_client.search(index=self.__index, body=query_body))
