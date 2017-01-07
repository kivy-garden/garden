'''
This script serves as a Kivy Garden page generator. It looks for all existing
Kivy-Garden flowers via GitHub API, creates a nice grid with their screenshots
(or flower js fallback if not available) and links to their GitHub repository.

Usage:

    Render html output:

        python generate.py

    Rebuild html from cache (without using GitHub API):

        python generate.py --rebuild

    Clean everything (even cache):

        python generate.py --clean
'''

from __future__ import print_function
from os.path import sep, join, dirname, abspath, exists
from distutils.dir_util import copy_tree
from os import mkdir, remove
from shutil import rmtree
from re import findall
import requests
import json
import sys

api = 'https://api.github.com/users/kivy-garden/'
raw = 'https://raw.githubusercontent.com/kivy-garden/'
root = join(dirname(abspath(__file__)), 'source')
dest = join(dirname(abspath(__file__)), 'build')
exclude = ['garden', 'kivy-garden.github.io']

try:
    if sys.argv[1] == '--clean':
        rmtree(dest)
        exit()
    elif sys.argv[1] == '--rebuild':
        rmtree(join(dest, 'html'))
except IndexError:
    pass

# Templates
emptysquare = (
    '<td><div class="emptysquare"><a href="$url$">'
    '<img src="$scr$" onerror=\'this.src = "stylesheets/flowerscr.png"\' />'
    '<span>$text$</span></a></div></td>'
)

square = (
    '<td><div class="square"><a href="$url$">'
    '<img src="$scr$" onerror=\'this.src = "stylesheets/flowerscr.png"\' />'
    '<span>$text$</span></a></div></td>'
)

template = '''
                <tr>
                    $0$
                    $1$
                    $2$
                    $3$
                    $4$
                </tr>
'''

# check folders
if exists(dest):
    if exists(join(dest, 'html')):
        print('Build already exists! Exiting...')
        exit()
    else:
        mkdir(join(dest, 'html'))
else:
    mkdir(dest)
    mkdir(join(dest, 'temp'))
    mkdir(join(dest, 'html'))

gallery = ''  # for html output
flowers = []  # for catching all flowers

page = 1
while True:
    url = api + 'repos?callback=getPages&page=' + str(page)
    leftstrip = 13  # strip this:  /**/getPages(

    # if not cached, get data from repository
    temp_page = 'temp{}.txt'.format(str(page))
    if not exists(join(dest, 'temp', temp_page)):
        print('Cached data not available, getting data from repo...\n\t', url)
        r = requests.get(url)
        content = json.loads(r.content[leftstrip:-1])

        # cache it https://developer.github.com/v3/search/#rate-limit
        with open(join(dest, 'temp', temp_page), 'w') as f:
            f.write(json.dumps(content))
    else:
        print('Cached data available...')
        with open(join(dest, 'temp', temp_page)) as f:
            content = json.loads(f.read())

    # get pages
    links = content['meta']['Link']
    for link in links:
        if 'last' in link[1]['rel']:
            last = int(findall(r'getPages&page=(\d+)', link[0])[0])
        else:
            last = int(page)

    # get values from data
    data = content['data']
    for d in data:
        name = d['name'].lstrip('garden')
        if name.startswith('.') or name.startswith('_'):
            name = name[1:]

        # ensure non-empty and allowed name
        if name and name not in exclude:
            print('Flower -> {}'.format(name))
            flower = {}
            flower['name'] = name
            flower['url'] = d['html_url']
            flower['scr'] = flower['url'] + '/raw/master/screenshot.png'

            flowers.append(flower)

    if page < last:
        page += 1
    else:
        print('Flowers gathered...')
        break

flowers = sorted(flowers, key=lambda k: k['name'])

pagination = 4  # X + 1 rows per page (append on 0)
pages = []
round = 0
start = 0
while True:
    tpl = template

    # get even or odd row
    if round % 2:
        _rows = [emptysquare, square, emptysquare, square, emptysquare]
    else:
        _rows = [square, emptysquare, square, emptysquare, square]

    # get row values
    first_five = flowers[start:start + 5]
    start += 5

    # fill up the template
    rows = []
    for i, row in enumerate(_rows):
        try:
            row = row.replace('$url$', first_five[i]['url'])
            row = row.replace('$scr$', first_five[i]['scr'])
            row = row.replace('$text$', first_five[i]['name'])
            rows.append(row)
        except IndexError:
            pass
    for i, row in enumerate(_rows):
        try:
            tpl = tpl.replace('${}$'.format(str(i)), rows[i])
        except IndexError:
            tpl = tpl.replace('${}$'.format(str(i)), '')

    round += 1
    if pagination:
        gallery += tpl
        pagination -= 1
    else:
        gallery += tpl
        pages.append(gallery)
        gallery = ''
        pagination = 4
    if len(first_five) < 5:
        pages.append(gallery)
        break

# write pages
for i, page in enumerate(pages):
    with open(join(root, 'gallery.template.html')) as f:
        content = f.read()
    if i != 0:
        file = join(dest, 'html', 'gallery{}.html'.format(str(i + 1)))
    else:
        file = join(dest, 'html', 'gallery.html')
    with open(file, 'w') as f:
        content = content.replace('$CONTENT$', page)
        if i == 1:
            content = content.replace('$PREV$', 'gallery.html')
            content = content.replace('<!--$P$', '').replace('$P$-->', '')
        elif i > 0:
            content = content.replace(
                '$PREV$', 'gallery{}.html'.format(str(i))
            )
            content = content.replace('<!--$P$', '').replace('$P$-->', '')
        if i != len(pages) - 1:
            content = content.replace(
                '$NEXT$', 'gallery{}.html'.format(str(i + 2))
            )
            content = content.replace('<!--$N$', '').replace('$N$-->', '')
        f.write(content)

# copy garden source
copy_tree(root, join(dest, 'html'))
remove(join(dest, 'html', 'gallery.template.html'))
print('Build complete')
