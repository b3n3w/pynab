import multiprocessing
import time
import logging

from pynab import log
from pynab.db import db_session, Release

import pynab.groups
import pynab.binaries
import pynab.releases
import pynab.tvrage
import pynab.rars
import pynab.nfos
import pynab.imdb

import scripts.quick_postprocess
import scripts.rename_bad_releases

import config


def mp_error(msg, *args):
    return multiprocessing.get_logger().error(msg, *args)


def process_tvrage():
    pynab.tvrage.process(500)


def process_nfos():
    pynab.nfos.process(500)


def process_rars():
    pynab.rars.process(200)


def process_imdb():
    pynab.imdb.process(500)


if __name__ == '__main__':
    log.info('Starting post-processing...')

    # print MP log as well
    multiprocessing.log_to_stderr().setLevel(logging.DEBUG)

    # start with a quick post-process
    log.info('starting with a quick post-process to clear out the cruft that\'s available locally...')
    scripts.quick_postprocess.local_postprocess()

    while True:
        with db_session() as db:
            # delete passworded releases first so we don't bother processing them
            if config.postprocess.get('delete_passworded', True):
                query = db.query(Release)
                if config.postprocess.get('delete_potentially_passworded', True):
                    query = query.filter(Release.passworded=='MAYBE')

                query = query.filter(Release.passworded=='YES')
                query.delete()

            # delete any nzbs that don't have an associated release
            # and delete any releases that don't have an nzb

            # grab and append tvrage data to tv releases
            tvrage_p = None
            if config.postprocess.get('process_tvrage', True):
                tvrage_p = multiprocessing.Process(target=process_tvrage)
                tvrage_p.start()

            imdb_p = None
            if config.postprocess.get('process_imdb', True):
                imdb_p = multiprocessing.Process(target=process_imdb)
                imdb_p.start()

            # grab and append nfo data to all releases
            nfo_p = None
            if config.postprocess.get('process_nfos', True):
                nfo_p = multiprocessing.Process(target=process_nfos)
                nfo_p.start()

            # check for passwords, file count and size
            rar_p = None
            if config.postprocess.get('process_rars', True):
                rar_p = multiprocessing.Process(target=process_rars)
                rar_p.start()

            if rar_p:
                rar_p.join()

            if imdb_p:
                imdb_p.join()

            if tvrage_p:
                tvrage_p.join()

            if nfo_p:
                nfo_p.join()

            # rename misc->other and all ebooks
            scripts.rename_bad_releases.rename_bad_releases(8010)
            scripts.rename_bad_releases.rename_bad_releases(7020)

            if config.postprocess.get('delete_bad_releases', False):
                pass
                #log.info('Deleting bad releases...')
                # not confident in this yet

        # wait for the configured amount of time between cycles
        postprocess_wait = config.postprocess.get('postprocess_wait', 1)
        log.info('sleeping for {:d} seconds...'.format(postprocess_wait))
        time.sleep(postprocess_wait)