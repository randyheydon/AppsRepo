#!/usr/bin/env python2

import os, urllib, json
from lxml import html, etree


download_uri = 'http://apps.openpandora.org/cgi-bin/dl.pl?%s.pnd'

def download_apps(storage_dir):
    categories = ('Emulators', 'Games', 'Applications', 'Other')
    directory_uri = 'http://apps.openpandora.org/cgi-bin/viewarea.pl?%s'
    destination_path = os.path.join(storage_dir, '%s.pnd')

    for cat in categories:
        page = html.parse(directory_uri % cat)
        for i in page.xpath("//div[@class='itemlist']/ul/li/@onclick"):
            name = i.rsplit('/',1)[1].rsplit('.',1)[0]
            print 'Getting', name
            urllib.urlretrieve(download_uri % name, destination_path % name)


def generate_json(storage_dir, output):
    repo_data = {'repository':{'name':'Pandora Apps', 'version': 3.0},
        'packages':[]}

    pxml_start_key = '<PXML'; pxml_end_key = '</PXML>'

    # Bytes of PND to check at a time, so we don't have to load the whole thing
    # into memory at once.
    window = 4096
    # But maintain some overlap between each window to ensure the '<PXML'
    # doesn't get cut off at the edge of one.
    seek_jump = -window + len(pxml_start_key)*2

    for fname in (i for i in os.listdir(storage_dir) if i.endswith('.pnd')):
        try:
            print 'Parsing', fname

            fpath = os.path.join(storage_dir, fname)
            f = open(fpath, 'rb')
            f.seek(-window, os.SEEK_END)
            # Seek backwards to start of PXML.
            pxml_start = -1
            while pxml_start == -1:
                text = f.read(window)
                f.seek(seek_jump-window, os.SEEK_CUR)
                pxml_start = text.rfind(pxml_start_key)
            f.seek(pxml_start-seek_jump, os.SEEK_CUR)

            # Read remainder of file, then remove everything after end of PXML.
            pxml = f.read().split(pxml_end_key, 1)[0] + pxml_end_key
            # Strip out the stupid goddamn namespace stuff that I hate.
            pxml = '<PXML>' + pxml.split('>',1)[1]

            # Parse PXML through lxml.etree.
            parser = etree.XMLParser(recover=True, remove_comments=True)
            root = etree.fromstring(pxml, parser)

            # Extract relevant data.
            package = {}
            package['id'] = root.xpath('/PXML/*/@id')[0]
            package['uri'] = download_uri % fname[:-4]

            package['version'] = {'major':'0', 'minor':'0', 'release':'0',
                'build':'0', 'type':'release'}
            try:
                version = root.xpath('/PXML/*/version')[0]
                package['version']['major'] = version.xpath('@major')[0]
                package['version']['minor'] = version.xpath('@minor')[0]
                package['version']['release'] = version.xpath('@release')[0]
                package['version']['build'] = version.xpath('@build')[0]
                package['version']['type'] = version.xpath('@type')[0]
            except IndexError: pass

            titles = {}
            for title in root.xpath('''/PXML/package/titles/title | /PXML/package/title
                | /PXML/application[1]/titles/title | /PXML/application[1]/title'''):
                lang = title.get('lang')
                if lang is not None and lang not in titles:
                    titles[lang] = title.text
            descriptions = {}
            for desc in root.xpath('''/PXML/package/descriptions/description |
                /PXML/package/description | /PXML/application[1]/descriptions/description
                | /PXML/application[1]/description'''):
                lang = desc.get('lang')
                if lang is not None and lang not in descriptions:
                    descriptions[lang] = desc.text
            package['localizations'] = {}
            for lang in titles.iterkeys():
                l = {}
                try:
                    l['title'] = titles[lang]
                    l['description'] = descriptions[lang]
                except KeyError: pass
                package['localizations'][lang] = l

            package['size'] = os.path.getsize(fpath)

            # TODO: Calculate MD5.

            try:
                author = root.xpath('/PXML/*/author')[0]
                package['author'] = {}
                for i in ('name', 'website', 'email'):
                    j = author.get(i)
                    if j is not None:
                        package['author'][i] = j
            except IndexError: pass

            # TODO: Icons, previewpics from apps.o.o.

            package['categories'] = list(set(root.xpath('/PXML/application/categories//@name')))

            # Add package to list.
            repo_data['packages'].append(package)

        except:
            print 'Failed to parse', fname

    json.dump(repo_data, open(output, 'w'))


if __name__ == '__main__':
    storage = '/media/disk/pnd_storage'
    outfile = '/home/randy/www/extra/repo.json'
    #download_apps(storage)
    generate_json(storage, outfile)
