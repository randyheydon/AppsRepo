#!/usr/bin/env python2

import os, urllib, json
from lxml import html, etree

def download_apps(storage_dir):
    categories = ('Emulators', 'Games', 'Applications', 'Other')
    directory_uri = 'http://apps.openpandora.org/cgi-bin/viewarea.pl?%s'
    download_uri = 'http://apps.openpandora.org/cgi-bin/dl.pl?%s.pnd'
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
    pxml_start = pxml_end = -1
    window = 4096
    seek_jump = -window + len(pxml_start_key)*2 # Cause who wants to bughunt?
    for fname in (i for i in os.listdir(storage_dir) if i.endswith('.pnd')):
        f = open(os.path.join(storage_dir, fname), 'rb')
        f.seek(0, os.SEEK_END)
        while pxml_start == -1:
            f.seek(seek_jump, os.SEEK_CUR)
            text = f.read(window)
            #TODO: more.

    json.dump(repo_data, open(output, 'w'))


if __name__ == '__main__':
    #download_apps('store')
    generate_json('store', 'repo.json')
