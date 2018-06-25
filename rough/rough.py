#coding=utf8

import re
import itertools
from collections import defaultdict
import urlparse

import requests
from lxml import etree
import click


class Rough(object):
    def __init__(self, seed_url,
                allow_patterns=None,
                assets=True,
                depth=1,
                verbose=1,
            ):
        """
        :params seed_url: start url
        :type seed_url: string
        :params allow_patterns: limit recursive check domain
                              if None, allow same domain
        :type allow_patterns: list or None
        :params assets: check js/css file or None, default is True
        :type assets: bool
        :params depth: recursive depth, default is 1
        :type depth: int
        """
        self.seed_url = seed_url
        self.allow_patterns = allow_patterns
        self.assets = assets
        self.depth = depth
        self.verbose = verbose

        if self.allow_patterns is None:
            self.allow_patterns = [re.escape(urlparse.urlparse(self.seed_url).netloc)]

        if isinstance(self.allow_patterns, basestring):
            self.allow_patterns = [self.allow_patterns]

        self._curr_depth = 0
        self._seen = set()
        self._status_code_stat = defaultdict(list)  # map[status_code][]urls

    def run(self):
        next_urls = [self.seed_url]
        while self._curr_depth <= self.depth:
            curr_urls = next_urls
            next_urls = []

            extract = self._curr_depth != self.depth
            for url in curr_urls:
                next_urls.extend(self.check_url(url, extract=extract))

            self._curr_depth += 1

        self.verbose_stat()

    def verbose_stat(self):
        self.verbose_log(0, '')
        total = sum([len(v) for v in self._status_code_stat.values()])
        for status_code in sorted(self._status_code_stat.keys()):
            urls = self._status_code_stat[status_code]
            self.verbose_log(0, '{} | {} ({:.2f}%)'.format(status_code, len(urls), len(urls)*100.0/total))
            for url in urls:
                if status_code == 200:
                    self.verbose_log(2, '\t{}'.format(url))
                else:
                    self.verbose_log(1, '\t{}'.format(url))

    def check_url(self, url, extract=True):
        if url in self._seen:
            return []

        status_code, content = self.http_get(url)
        self._status_code_stat[status_code].append(url)
        self._seen.add(url)
        self.verbose_log(1, '{} | {} | {} {}'.format(self._curr_depth, len(self._seen), status_code, url))

        if status_code != 200:
            return []

        if not extract:
            return []

        dom = etree.HTML(content)
        return list(self.iter_links(dom, url, self.assets))

    def http_get(self, url):
        resp = requests.get(url)
        return resp.status_code, resp.content

    def iter_links(self, dom, base_url, assets):
        generator = [dom.xpath('//a/@href')]
        if assets:
            generator.append(dom.xpath('//link/@href'))
            generator.append(dom.xpath('//script/@src'))

        for href in itertools.chain(*generator):
            link = urlparse.urljoin(base_url, href.split('#')[0])
            if self.is_allow_url(link):
                yield link

    def is_allow_url(self, url):
        for posfix in ('.jpg', '.jpeg', '.png'):
            if url.endswith(posfix):
                return False

        for pattern in self.allow_patterns:
            if re.search(pattern, url):
                return True
        return False

    def verbose_log(self, level, fmt, *args):
        if self.verbose >= level:
            if len(args) > 0:
                print fmt % args
            else:
                print fmt


@click.command()
@click.option('-d', '--depth', default=1, help='treverse depth')
@click.option('-a', '--assets', is_flag=True, help='check js/css')
@click.option('-v', '--verbose', default=1, help='verbose level')
@click.argument('url')
def cli(depth, assets, verbose, url):
    r = Rough(seed_url=url, depth=depth, assets=assets, verbose=verbose)
    r.run()


def run():
    cli()
