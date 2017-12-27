from pyquery import PyQuery as pq
import requests as req
import os
import time
import sys

_startTime = time.time()

packageNames = sys.argv[1:]
architecture = 'armhf'
favoriteMirror = 'ftp.kr.debian.org/debian'
codeName = 'jessie'

DB_PATH = './db.txt'
db = []
DEB_PATH = './deb'


def checkSearchSucceed(q):
    if q('#psearchres h2:first').text() == 'Exact hits':
        return True
    else:
        return False

def searchPackage(packageName):
    global architecture
    global codeName

    res = req.get('https://packages.debian.org/search?suite=' + codeName + '&arch=' + architecture + '&searchon=names&keywords=' + packageName)
    q = pq(res.content)

    if checkSearchSucceed(q):
        return q('#psearchres > ul:first-of-type a:first-of-type').attr('href')
    else:
        return False
    
def getDependencies(package):
    res = req.get('https://packages.debian.org' + package)
    q = pq(res.content)

    return getDependenciesFromPyQuery(q)

def getDependenciesFromPyQuery(q):
    li = q('.uldep li')
    li = li[1:]
        
    dependencies = [pq(x)('a:first-of-type').attr('href') for x in li]
    return dependencies

def loadDB():
    global DB_PATH
    global db
    global DEB_PATH

    if os.path.exists(DB_PATH):
        f = open(DB_PATH, 'r+')
    else:
        f = open(DB_PATH, 'w+')
    db = f.read().splitlines()
    f.close()

    # donwload folder
    if not os.path.exists(DEB_PATH):
        os.makedirs(DEB_PATH)

def saveDB():
    global DB_PATH
    global db

    if os.path.exists(DB_PATH):
        f = open(DB_PATH, 'r+')
    else:
        f = open(DB_PATH, 'w+')
    f.write('\n'.join(db))
    f.close()

def addDB(package):
    global db

    db.append(package)

def checkDB(package):
    global db

    return package in db

def downloadPackageWithAllDependencies(package):
    global architecture
    global favoriteMirror

    # check already downloaded
    if checkDB(package):
        print(package + ' already downloaded')
        return True

    res = req.get('https://packages.debian.org' + package)
    q = pq(res.content)
    dependencies = getDependenciesFromPyQuery(q)

    link = ''
    tr = q('#pdownload tr')[1:]
    tr1 = pq(pq(tr[0])('a')[0])
    if tr1.text() == 'all':
        link = tr1.attr('href')
    else:
        for t in tr:
            t = pq(pq(t)('a')[0])
            if t.text() == architecture:
                link = t.attr('href')
                break

    if link == '':
        print('cannot resolve ' + package)
        return False

    res = req.get('https://packages.debian.org' + link)
    q = pq(res.content)
    url = ''
    for a in q('#content a'):
        if a.text == favoriteMirror:
            url = a.get('href')
            break

    downloadFromUrl(url)
    addDB(package)

    for d in dependencies:
        downloadPackageWithAllDependencies(d)


def downloadFromUrl(url):
    global DEB_PATH

    res = req.get(url, stream=True)
    if res.status_code == 200:
        with open(DEB_PATH + '/' + os.path.basename(url), 'wb') as f:
            for chunk in res.iter_content(1024):
                f.write(chunk)

    print(os.path.basename(url) + ' download complete')

loadDB()

for packageName in packageNames:
    package = searchPackage(packageName)
    downloadPackageWithAllDependencies(package)
    saveDB() # fucking unkown error may shit this program

print("--- %s seconds ---" % (time.time() - _startTime))