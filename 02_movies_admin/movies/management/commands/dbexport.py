
from math import prod
import os, sys
from pprint import pprint

from time import sleep
from datetime import date, datetime
from django.db import transaction
from django.core.management.base import BaseCommand

from movies.models import Filmwork, Person, Genre

sys.path.append('../05_elastic')
import elastic

sys.path.append('movies/management')
from backoff import backoff

sys.path.append('../03_sqlite_to_postgres')
import db


class Command(BaseCommand):
    help = 'Export database updates to external services, like search or messaging'

    def add_arguments(self, parser):
        parser.add_argument(
            '-d', action='store_true',
            help='Whether to run periodically in background, as a daemon')
        parser.add_argument(
            '--interval', type=int,
            help='The daemon would export db updates each <interval> sec.')
        parser.add_argument(
            '--exportafter', type=datetime.fromisoformat,
            help='Records modified after date(iso) would be exported. Override state')

    #@backoff()
    def _etl_process(self, model):
        with db.postgres_manager() as psg:
            producer = db.PostgresProducer(model, psg, chunk_size=500)

            # get direct updates in requested model
            syncfrom = producer.get_startdate()
            src = producer.produce()
            num = producer.num_extracted()

            self.stdout.write(self.style.SUCCESS(
                    f'### ETL: sync {model} from {syncfrom}'))

            # process transitive updates if working model isn't final
            enricher = db.PostgresEnricher(model, psg, chunk_size=500)

            target = enricher.find_target(src) if model != 'film_work' else src
            num = enricher.num_extracted() if model != 'film_work' else num

            # start building elsatic dicts
            enricher.init_target(target)
            self.stdout.write(
                self.style.SUCCESS(
                    f'### ETL: related film_work: found {num} references'
                ))
            
            # enrich target updates
            to_merge = enricher.enrich_target()
            self.stdout.write(
                self.style.SUCCESS(
                    '### ETL: merged & enriched total: ' +
                     f'{enricher.total_uids} records\n'
                ))
            
            # merge enriched rows to match expected data schema
            enricher.merge_target(to_merge)
            
            # load to elasticsearch
            esmanager = elastic.EsManager('movies', chunk_size=500)

            # esmanager.delete_index()
            # esmanager.create_schema('../05_elastic/elastic.schema.json')

            for chunk in db.chunks(enricher.target.values(), chunk_size=500):
                changes = list(chunk)
                esmanager.populate_index(changes)
            
            # update sync pointer
            producer.set_startdate()
            self.stdout.write(
                self.style.SUCCESS(
                        f'### ETL: written sync pointer: {producer.get_startdate()}'))
            
            #esmanager.search('Sci-Fi')

    def handle(self, *args, **options):
        while True:
            for model in ['film_work', 'person', 'genre']:
                self.stdout.write(
                    self.style.WARNING(f'### ETL: syncing {model}...'))
                self._etl_process(model)

            if options['d']:
                self.stdout.write(
                    self.style.SUCCESS('### ETL: running ETL daemon...')
                )
                sleep(options['interval'])
            else:
                break
