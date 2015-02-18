
from pyquery import PyQuery as query
import re
import urllib

from addic7ed.request import get, get_last_url
from addic7ed.version import Version

__all__ = ['search']

class Episode(object):

    def __init__(self, url, title=None):
        self.url = url
        self.title = title
        self.versions = []

    def __eq__(self, other):
        return self.url == other.url and self.title == other.title

    def __unicode__(self):
        return self.title

    def __repr__(self):
        return 'Episode(%s, %s)' % (repr(self.url), repr(self.title))

    def __str__(self):
        return unicode(self).encode('utf-8')

    def add_version(self, *args):
        self.versions.append(Version(*args))

    def fetch_versions(self):
        if self.versions:
            return

        result = get(self.url)
        tables = result('.tabel95')
        self.title = tables.find('.titulo').contents()[0].strip()

        for i, table in enumerate(tables[2:-1:2]):
            trs = query(table)('tr')

            release = trs.find('.NewsTitle').text().partition(',')[0]
            release = re.sub('version ', '', release, 0, re.I)

            infos = trs.next().find('.newsDate').eq(0).text()
            infos = re.sub('(?:should)? works? with ', '', infos, 0, re.I)

            for tr in trs[2:]:
                tr = query(tr)
                language = tr('.language')
                if not language:
                    continue

                completeness = language.next().text().partition(' ')[0]
                language = language.text()
                download = tr('a[href*=updated]') or tr('a[href*=original]')
                if not download:
                    continue
                hearing_impaired = \
                    bool(tr.next().find('img[title="Hearing Impaired"]'))
                download = download.attr.href
                self.add_version(download, language, release, infos,
                                 completeness, hearing_impaired)

    def filter_versions(self, languages=[], release=set(), completed=True,
                        hearing_impaired=False):

        for version in self.versions:
            version.weight = 0
            version.match_languages(languages)
            version.match_release(release)
            version.match_completeness(completed)
            version.match_hearing_impaired(hearing_impaired)

        result = []
        last_weight = None
        for version in sorted(self.versions, key=lambda v: v.weight,
                              reverse=True):
            if last_weight is None:
                last_weight = version.weight
            elif last_weight - version.weight >= 0.5:
                break

            result.append(version)

        return result


def search(query):
    results = get('/search.php', search=query, submit='Search')
    last_url = get_last_url()
    if '/search.php' in last_url:
        return [
            Episode(urllib.quote(link.attrib['href'].encode('utf8')),
                    link.text)
            for link in results('.tabel a')
        ]
    else:
        title = results('.titulo').contents()[0].strip()
        return [Episode(last_url, title)]