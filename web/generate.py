from __future__ import print_function
from distutils.dir_util import copy_tree
from shutil import rmtree
from os.path import sep
import os.path as op
import itertools
import requests
import json
import sys
import re
import os

api = 'https://api.github.com/users/kivy-garden/'
raw = 'https://raw.githubusercontent.com/kivy-garden/'
root = op.join(op.dirname(op.abspath(__file__)), 'source') + sep
dest = op.join(op.dirname(op.abspath(__file__)), 'build') + sep
exclude = ['garden', 'kivy-garden.github.io']

try:
    if sys.argv[1] == '--clean':
        rmtree(dest)
        exit()
    elif sys.argv[1] == '--rebuild':
        rmtree(op.join(dest, 'html'))
except IndexError:
    pass

# Templates
emptysquare = '<td><div class="emptysquare"><a href="$url$"><img src="$scr$"\
 /><span>$text$</span></a></div></td>'

square = '<td><div class="square"><a href="$url$"><img src="$scr$"\
 /><span>$text$</span></a></div></td>'

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
if op.exists(dest):
    if op.exists(op.join(dest, 'html')):
        print('Build already exists! Exiting...')
        exit()
    else:
        os.mkdir(op.join(dest, 'html'))
else:
    os.mkdir(dest)
    os.mkdir(op.join(dest, 'temp'))
    os.mkdir(op.join(dest, 'html'))

gallery = ''  # for html output
flowers = []  # for catching all flowers

page = 1
while True:
    url = api+'repos?callback=getPages&page='+str(page)
    leftstrip = 13  # strip this:  /**/getPages(

    # if not cached, get data from repository
    if not op.exists(op.join(dest, 'temp', 'temp' + str(page) + '.txt')):
        print('Cached data not available, getting data from repo...\n', url)
        r = requests.get(url)
        content = json.loads(r.content[leftstrip:-1])

        # cache it https://developer.github.com/v3/search/#rate-limit
        with open(op.join(dest, 'temp', 'temp'+str(page) + '.txt'), 'w') as f:
            f.write(json.dumps(content))
    else:
        print('Cached data available...')
        with open(op.join(dest, 'temp', 'temp'+str(page)+'.txt')) as f:
            content = json.loads(f.read())

    # get pages
    links = content['meta']['Link']
    for link in links:
        if 'last' in link[1]['rel']:
            last = int(re.findall(r'getPages&page=(\d+)', link[0])[0])
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
            flower = {}
            flower['name'] = name
            flower['url'] = d['html_url']
            # flower['scr'] = ''  # <some screenshot from RAW>
            flower['scr'] = 'stylesheets/flowerscr.png'
            flowers.append(flower)

    if page < last:
        page += 1
    else:
        print('Flowers gathered...')
        break

flowers = sorted(flowers, key=lambda k: k['name'])

pagination = 5  # rows per page
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
    first_five = flowers[start:start+5]
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
    for i in range(5):
        try:
            tpl = tpl.replace('$'+str(i)+'$', rows[i])
        except IndexError:
            tpl = tpl.replace('$'+str(i)+'$', '')

    round += 1
    if pagination:
        gallery += tpl
        pagination -= 1
    else:
        pages.append(gallery)
        gallery = ''
        pagination = 5
    if len(first_five) < 5:
        pages.append(gallery)
        break

# write pages
for i, page in enumerate(pages):
    with open(root+'temp_gallery.html') as f:
        content = f.read()
    if i != 0:
        file = op.join(dest, 'html', 'gallery'+str(i+1)+'.html')
    else:
        file = op.join(dest, 'html', 'gallery.html')
    with open(file, 'w') as f:
        content = content.replace('$CONTENT$', page)
        if i == 1:
            content = content.replace('$PREV$', 'gallery.html')
            content = content.replace('<!--$P$', '').replace('$P$-->', '')
        elif i > 0:
            content = content.replace('$PREV$', 'gallery'+str(i)+'.html')
            content = content.replace('<!--$P$', '').replace('$P$-->', '')
        if i != len(pages) - 1:
            content = content.replace('$NEXT$', 'gallery'+str(i+2)+'.html')
            content = content.replace('<!--$N$', '').replace('$N$-->', '')
        f.write(content)

# copy garden source
copy_tree(root, op.join(dest, 'html'))
os.remove(op.join(dest, 'html', 'temp_gallery.html'))
print('Build complete')