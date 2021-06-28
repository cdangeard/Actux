from bs4 import BeautifulSoup
import urllib.request
import csv
from datetime import date, timedelta
import re
import dateparser
import pandas as pd
# ## LeMonde.fr

# In[31]:


## une fonction BS4 pour scrapper les urls des articles sur la page principale
def leMondeUrlMainPageScrapper(urlMainPage = 'https://www.lemonde.fr/'):
    page = urllib.request.urlopen(urlMainPage)
    soup = BeautifulSoup(page, 'html.parser')
    listUrl = soup.select_one('#habillagepub > section.zone.zone--homepage.old__zone').find_all('a', href=True)
    listUrlarticle = [link['href'] for link in listUrl if link['href'].startswith("https://www.lemonde.fr")]
    return listUrlarticle

## une fonction BS4 pour scrapper les urls de la page en continu du MONDE.FR
def leMondeUrlContinuScrapper(urlPage = 'https://www.lemonde.fr/actualite-en-continu/'):
    page = urllib.request.urlopen(urlPage)
    soup = BeautifulSoup(page, 'html.parser')
    listUrl = soup.select_one('#river').find_all('a', href=True)
    listUrlarticle = [link['href'] for link in listUrl if link['href'].startswith("https://www.lemonde.fr")]
    return listUrlarticle

## Transforme la date affiché sur le site en un format plus standard
def leMondeDateFormater(stringDate):
    string = stringDate.split(',',1)[0]
    if 'hier' in string:
        return (date.today() - timedelta(days=1)).strftime("%d/%m/%Y")
    elif 'aujourd’hui' in string:
        return date.today().strftime("%d/%m/%Y")
    else:
        return dateparser.parse(re.search(r'\d{1,2} \w* \d{4}', string).
                                group(0)).date().strftime("%d/%m/%Y")

## Scraper pour la page d'un article retourne un dictionaire (titre, texte, date, date_scrap)
def leMondeArcticleScrapper(urlArticle):
    page = urllib.request.urlopen(urlArticle)
    soup = BeautifulSoup(page, 'html.parser')
    rejUrl = re.search(r'^https://www.lemonde.fr/(.*?)/(.*?)/', urlArticle)
    typePage = rejUrl.group(2)
    domaine = rejUrl.group(1)
    titre = soup.find_all('h1')[0].get_text(strip=True).replace('\xa0',' ')
    try:
        dateArcticle = leMondeDateFormater(soup.find_all('span',{'class':'meta__date meta__date--header'})[0].get_text(strip=True).replace('\xa0',' '))
    except IndexError:
        dateArcticle = ''
    text = ' '.join([paragraph.get_text().replace('\xa0',' ') for paragraph in soup.find_all('p',{'class':'article__paragraph'})])
    return {'titre' : titre,
            'url' : urlArticle,
            'texte' : text,
            'date' : dateArcticle,
            'date_scrap' : date.today().strftime("%d/%m/%Y"),
            'journal' : 'leMonde.fr',
            'domaine' : domaine,
            'typePage' : typePage}


def leMondeUrlScrapper(continu = True):
    if continu:
        return leMondeUrlContinuScrapper()
    else:
        return leMondeUrlMainPageScrapper()

def leMondeScrapper(continu = False):
    print('scrapping leMonde')
    try:
        urlsArticles = leMondeUrlScrapper()
    except:
        print('failure scrap url leMonde')
        return pd.DataFrame()
    df = pd.DataFrame()
    print('nombre d\'articles :', len(urlsArticles))
    er = 0
    for url in urlsArticles:
        try:
            df = df.append(leMondeArcticleScrapper(url), ignore_index = True)
        except:
            er += 1
            print(f'erreur arcticle {url}')
    print(f'erreur sur : {er} articles')
    return df


# ## Figaro

# In[30]:


## Transforme la date affiché sur le site en un format plus standard
def figaroDateFormater(stringDate):
    string = stringDate.split('T',1)[0]
    return '/'.join([string[8:10], string[5:7], string[0:4]])

## Retourn False si l'url correspond à des pages spéciales non scrapable (vidéo etc...)
def figaroScrapableURL(url):
    return url.startswith("https://www.lefigaro.fr/") and not(url.startswith("https://www.lefigaro.fr/story"))


def figaroUrlScrapper(urlMainPage = 'https://www.lefigaro.fr/'):
    page = urllib.request.urlopen(urlMainPage)
    soup = BeautifulSoup(page, 'html.parser')
    listUrl = soup.find_all('article')
    listUrlArticles = [title.find('a')['href'] for title in listUrl]
    listUrlArticles = [link for link in listUrlArticles if figaroScrapableURL(link)]
    return listUrlArticles

def figaroArticleScrapper(urlArticle):
    page = urllib.request.urlopen(urlArticle)
    soup = BeautifulSoup(page, 'html.parser')
    rejUrl = re.search(r'^https://www.lefigaro.fr/(.*?)/', urlArticle)
    domaine = rejUrl.group(1)
    titre = soup.find_all('h1')[0].get_text(strip=True).replace('\xa0',' ')
    try:
        dateArcticle = figaroDateFormater(soup.select('time')[0]['datetime'])
    except IndexError:
        dateArcticle = ''

    textItems = soup.find_all('p',{'class' : ["fig-standfirst", "fig-paragraph"]})
    text = ' '.join([paragraph.get_text().replace('\xa0',' ') for paragraph in textItems])
    return {'titre' : titre,
            'url' : urlArticle,
            'texte' : text,
            'date' : dateArcticle,
            'date_scrap' : date.today().strftime("%d/%m/%Y"),
            'journal' : 'figaro.fr',
            'domaine' : domaine,
            'typePage' : 'article'}

def figaroScrapper():
    print('scrapping figaro')
    try:
        urlsArticles = figaroUrlScrapper()
    except:
        print('failure scrap url figaro')
        return pd.DataFrame()
    df = pd.DataFrame()
    print('nombre d\'articles :', len(urlsArticles))
    er = 0
    for url in urlsArticles:
        try:
            df = df.append(figaroArticleScrapper(url), ignore_index = True)
        except:
            er += 1
            print(f'erreur arcticle {url}')
    print(f'erreur sur : {er} articles')
    return df


# ## Libération

# In[29]:


## Transforme la date affiché sur le site en un format plus standard
def liberationDateFormater(stringDate):
    rej = re.search(r'^publié le (\d{1,2} \w* \d{4})', stringDate)
    if rej:
        return dateparser.parse(rej.group(1)).date().strftime("%d/%m/%Y")
    else:
        return date.today().strftime("%d/%m/%Y")

## Retourn False si l'url correspond à des pages spéciales non scrapable (vidéo etc...)
def liberationScrapableURl(url):
    return re.match(r'/(.*?)/.+', url) and len(url) > 40


def liberationUrlScrapper(urlMainPage = 'https://www.liberation.fr/'):
    page = urllib.request.urlopen(urlMainPage)
    soup = BeautifulSoup(page, 'html.parser')
    soupMain = soup.find('section',{'class':'main'})
    listUrl = soupMain.find_all('a')
    listUrlArticles = list(set([title['href'] for title in listUrl]))
    listUrlArticles = [f'https://www.liberation.fr{link}' for link in listUrlArticles if liberationScrapableURl(link)]
    return listUrlArticles

def liberationArticleScrapper(urlArticle):
    with urllib.request.urlopen(urlArticle) as response:
        page = response.read().decode('utf-8')
    soup = BeautifulSoup(page, 'html.parser')
    rejUrl = re.search(r'^https://www.liberation.fr/(.*?)/', urlArticle)
    domaine = rejUrl.group(1)
    titre = soup.find_all('h1')[0].get_text(strip=True).replace('\xa0',' ')
    try:
        dateArcticle = soup.find('div', {'class' : 'header-date'}).get_text()
    except IndexError:
        dateArcticle = ''
    textItems = soup.find_all('span', {'class' : "TypologyArticle"})
    textItems += soup.find_all('p')
    text = ' '.join([paragraph.get_text().replace('\xa0',' ') for paragraph in textItems])
    return {'titre' : titre,
            'url' : urlArticle,
            'texte' : text,
            'date' : liberationDateFormater(dateArcticle),
            'date_scrap' : date.today().strftime("%d/%m/%Y"),
            'journal' : 'liberation.fr',
            'domaine' : domaine,
            'typePage' : 'article'}

def liberationScrapper():
    print('scrapping libération')
    try:
        urlsArticles = liberationUrlScrapper()
    except:
        print('failure scrap url libération')
        return pd.DataFrame()
    df = pd.DataFrame()
    print('nombre d\'articles :', len(urlsArticles))
    er = 0
    for url in urlsArticles:
        try:
            df = df.append(liberationArticleScrapper(url), ignore_index = True)
        except:
            er += 1
            print(f'erreur arcticle {url}')
    print(f'erreur sur : {er} articles')
    return df


# ## Le Parisien

# In[28]:


def liberationDateFormater(stringDate):
    rej = re.search(r'^Le (\d{1,2} \w* \d{4})', stringDate)
    if rej:
        return dateparser.parse(rej.group(1)).date().strftime("%d/%m/%Y")
    else:
        return date.today().strftime("%d/%m/%Y")


def parisienUrlScrapper(urlMainPage = 'https://www.leparisien.fr/'):
    page = urllib.request.urlopen(urlMainPage)
    soup = BeautifulSoup(page, 'html.parser')
    listUrl = soup.find_all('div', {'class' : 'story-preview'})
    listUrlArticles = list(set([title.find('a')['href'] for title in listUrl]))
    listUrlArticles = [f'https:{link}' for link in listUrlArticles]
    return listUrlArticles

def parisienArticleScrapper(urlArticle):
    with urllib.request.urlopen(urlArticle) as response:
        page = response.read().decode('utf-8')
    soup = BeautifulSoup(page, 'html.parser')
    rejUrl = re.search(r'^https://www.leparisien.fr/(.*?)/', urlArticle)
    domaine = rejUrl.group(1)
    titre = soup.find_all('h1')[0].get_text(strip=True).replace('\xa0',' ')
    try:
        dateArcticle = liberationDateFormater(soup.find('div', {'class' : 'timestamp'}).get_text())
    except IndexError:
        dateArcticle = ''
    textItems = soup.find_all(['p'], {'class' : 'paragraph'})
    text = ' '.join([paragraph.get_text().replace('\xa0',' ') for paragraph in textItems])
    return {'titre' : titre,
            'url' : urlArticle,
            'texte' : text,
            'date' : dateArcticle,
            'date_scrap' : date.today().strftime("%d/%m/%Y"),
            'journal' : 'leparisien.fr',
            'domaine' : domaine,
            'typePage' : 'article'}

def parisienScrapper():
    print('scrapping parisien')
    try:
        urlsArticles = parisienUrlScrapper()
    except:
        print('failure scrap url parisien')
        return pd.DataFrame()
    df = pd.DataFrame()
    print('nombre d\'articles :', len(urlsArticles))
    er = 0
    for url in urlsArticles:
        try:
            df = df.append(parisienArticleScrapper(url), ignore_index = True)
        except:
            er += 1
            print(f'erreur arcticle {url}')
    print(f'erreur sur : {er} articles')
    return df


# ## Les echos

# In[27]:


def lesechosDateFormater(stringDate):
    rej = re.search(r'^Publié le (\d{1,2} \w* \d{4})', stringDate)
    if rej:
        return dateparser.parse(rej.group(1)).date().strftime("%d/%m/%Y")
    else:
        return date.today().strftime("%d/%m/%Y")

def lesechosUrlScrapper(urlMainPage = 'https://www.lesechos.fr/'):
    page = urllib.request.urlopen(urlMainPage)
    soup = BeautifulSoup(page, 'html.parser')
    listUrl = soup.find_all('article')
    listUrlArticles = list(set([title.find('a')['href'] for title in listUrl]))
    listUrlArticles = [f'https://www.lesechos.fr{link}' if link.startswith('/') else link for link in listUrlArticles]
    listUrlArticles = [link for link in listUrlArticles if link.startswith('https://www.lesechos.fr') ]
    return listUrlArticles

def lesechosArticleScrapper(urlArticle):
    with urllib.request.urlopen(urlArticle) as response:
        page = response.read().decode('utf-8')
    soup = BeautifulSoup(page, 'html.parser')
    rejUrl = re.search(r'^https://www.lesechos.fr/(.*?)/', urlArticle)
    domaine = rejUrl.group(1)
    titre = soup.find_all('h1')[0].get_text(strip=True).replace('\xa0',' ')
    try:
        dateArcticle = lesechosDateFormater(soup.find('span', {'class' : 'sc-1i0ieo8-0'}).get_text())
    except IndexError:
        dateArcticle = ''
    textItems = soup.find_all(['p'], {'class' : 'sc-AxirZ'})
    text = ' '.join([paragraph.get_text().replace('\xa0',' ') for paragraph in textItems])
    return {'titre' : titre,
            'url' : urlArticle,
            'texte' : text,
            'date' : dateArcticle,
            'date_scrap' : date.today().strftime("%d/%m/%Y"),
            'journal' : 'lesechos.fr',
            'domaine' : domaine,
            'typePage' : 'article'}

def lesechosScrapper():
    print('scrapping lesEchos')
    try:
        urlsArticles = lesechosUrlScrapper()
    except:
        print('failure scrap url lesEchos')
        return pd.DataFrame()
    df = pd.DataFrame()
    print('nombre d\'articles :', len(urlsArticles))
    er = 0
    for url in urlsArticles:
        try:
            df = df.append(lesechosArticleScrapper(url), ignore_index = True)
        except:
            er += 1
            print(f'erreur arcticle {url}')
    print(f'erreur sur : {er} articles')
    return df


# ## La Croix

# In[26]:


def dateTimeDateFormater(stringDate):
    string = stringDate.split('T',1)[0]
    return '/'.join([string[8:10], string[5:7], string[0:4]])

def laCroixUrlScrapper(urlMainPage = 'https://www.la-croix.com/'):
    page = urllib.request.urlopen(urlMainPage)
    soup = BeautifulSoup(page, 'html.parser')
    listUrl = soup.find_all('article')
    listUrlArticles = list(set([title.find('a')['href'] for title in listUrl]))
    listUrlArticles = [f'https://www.la-croix.com{link}' if link.startswith('/') else link for link in listUrlArticles]
    listUrlArticles = [link for link in listUrlArticles if link.startswith('https://www.la-croix.com') ]
    return listUrlArticles

def laCroixArticleScrapper(urlArticle):
    with urllib.request.urlopen(urlArticle) as response:
        page = response.read().decode('utf-8')
    soup = BeautifulSoup(page, 'html.parser')
    rejUrl = re.search(r'^https://www.la-croix.com/(.*?)/', urlArticle)
    if rejUrl:
        domaine = rejUrl.group(1)
    else:
        domaine = ''
    titre = soup.find_all('h1')[0].get_text(strip=True)
    try:
        dateArcticle = dateTimeDateFormater(soup.select('time')[0]['datetime'])
    except IndexError:
        dateArcticle = ''
    textItems = soup.find('article').find_all(['p'])
    text = ' '.join([paragraph.get_text().replace('\xa0', ' ') for paragraph in textItems])
    return {'titre' : titre,
            'url' : urlArticle,
            'texte' : text,
            'date' : dateArcticle,
            'date_scrap' : date.today().strftime("%d/%m/%Y"),
            'journal' : 'laCroix.fr',
            'domaine' : domaine,
            'typePage' : 'article'}

def laCroixScrapper():
    print('scrapping laCroix')
    try:
        urlsArticles = laCroixUrlScrapper()
    except:
        print('failure scrap url laCroix')
        return pd.DataFrame()
    df = pd.DataFrame()
    print('nombre d\'articles :', len(urlsArticles))
    er = 0
    for url in urlsArticles:
        try:
            df = df.append(laCroixArticleScrapper(url), ignore_index = True)
        except:
            er += 1
            print(f'erreur arcticle {url}')
    print(f'erreur sur : {er} articles')
    return df


# ## L'humanité

# In[25]:


def humaniteDateFormater(stringDate):
    rej = re.search(r'^\w* (\d{1,2} \w* \d{4})', stringDate)
    if rej:
        return dateparser.parse(rej.group(1)).date().strftime("%d/%m/%Y")
    else:
        return date.today().strftime("%d/%m/%Y")

def humaniteUrlScrapper(urlMainPage = 'https://www.humanite.fr/'):
    page = urllib.request.urlopen(urlMainPage)
    soup = BeautifulSoup(page, 'html.parser')
    listUrl = soup.find_all('div', {'class' : 'group-description'})
    listUrlArticles = list(set([title.find('a')['href'] for title in listUrl]))
    listUrlArticles = [f'https://www.humanite.fr{link}' if link.startswith('/') else link for link in listUrlArticles]
    listUrlArticles = [link for link in listUrlArticles if link.startswith('https://www.humanite.fr/') ]
    return listUrlArticles

def humaniteArticleScrapper(urlArticle):
    with urllib.request.urlopen(urlArticle) as response:
        page = response.read().decode('utf-8', 'ignore')
    soup = BeautifulSoup(page, 'html.parser')
    domaine = soup.find('div', {'class' : 'field-item even'}).get_text()
    titre = soup.find_all('h1')[0].get_text(strip=True).replace('\xa0',' ')
    try:
        dateArcticle = humaniteDateFormater(soup.find('span', {'class' : 'date-display-single'}).get_text())
    except:
        dateArcticle = ''
    textItems = soup.find('div', {'class' : 'group-zone-article'}).find_all(['p'])
    text = ' '.join([paragraph.get_text().replace('\xa0',' ').replace('\u2009', ' ') for paragraph in textItems])
    return {'titre' : titre,
            'url' : urlArticle,
            'texte' : text,
            'date' : dateArcticle,
            'date_scrap' : date.today().strftime("%d/%m/%Y"),
            'journal' : 'humanite.fr',
            'domaine' : domaine,
            'typePage' : 'article'}

def humaniteScrapper():
    print('scrapping humanité')
    try:
        urlsArticles = humaniteUrlScrapper()
    except:
        print('failure scrap url humanite')
        return pd.DataFrame()
    df = pd.DataFrame()
    print('nombre d\'articles :', len(urlsArticles))
    er = 0

    for url in urlsArticles:
        try:
            df = df.append(humaniteArticleScrapper(url), ignore_index = True)
        except:
            er += 1
            print(f'erreur arcticle {url}')
    print(f'erreur sur : {er} articles')
    return df


# ## Nouvelobs

# In[24]:


def nouvelObsTimeDateFormater(stringDate):
    rej = re.search(r'^Publié le (\d{1,2} \w* \d{4})', stringDate)
    if rej:
        return dateparser.parse(rej.group(1)).date().strftime("%d/%m/%Y")
    else:
        return date.today().strftime("%d/%m/%Y")

def nouvelObsScrapableUrl(url):
    return not(url.startswith('https://www.nouvelobs.com/videos/') or
               url.startswith('https://www.nouvelobs.com/club-abonnes/')) and url.endswith('.html')

def nouvelobsUrlScrapper(urlMainPage = 'https://www.nouvelobs.com/'):
    page = urllib.request.urlopen(urlMainPage)
    soup = BeautifulSoup(page, 'html.parser')
    listUrl = soup.find_all('article')
    listUrlArticles = list(set([title.find('a')['href'] for title in listUrl if title.find('a')]))
    listUrlArticles = [link for link in listUrlArticles]
    listUrlArticles = [link for link in listUrlArticles if nouvelObsScrapableUrl(link)]
    return listUrlArticles

def nouvelobsArticleScrapper(urlArticle):
    with urllib.request.urlopen(urlArticle) as response:
        page = response.read().decode('utf-8')
    soup = BeautifulSoup(page, 'html.parser')
    rejUrl = re.search(r'^https://www.nouvelobs.com/(.*?)/', urlArticle)
    if rejUrl:
        domaine = rejUrl.group(1)
    else:
        domaine = ''
    titre = soup.find_all('h1')[0].get_text(strip=True)
    try:
        dateArcticle = nouvelObsTimeDateFormater(soup.find('time', {'class':'article__published-date'}).get_text())
    except IndexError:
        dateArcticle = ''
    textItems = soup.find_all('h2', {'class': 'article__abstract'})
    textItems += soup.find('div', {'class' : 'ObsArticle-body'}).find_all(['p'])
    text = ' '.join([paragraph.get_text().replace('\xa0', ' ') for paragraph in textItems])
    return {'titre' : titre,
            'url' : urlArticle,
            'texte' : text,
            'date' : dateArcticle,
            'date_scrap' : date.today().strftime("%d/%m/%Y"),
            'journal' : 'nouvelobs.com',
            'domaine' : domaine,
            'typePage' : 'article'}

def nouvelobsScrapper():
    print('scrapping nouvelObs')
    try:
        urlsArticles = nouvelobsUrlScrapper()
    except:
        print('failure scrap url nouvelObs')
        return pd.DataFrame()
    df = pd.DataFrame()
    print('nombre d\'articles :', len(urlsArticles))
    er = 0
    for url in urlsArticles:
        try:
            df = df.append(nouvelobsArticleScrapper(url), ignore_index = True)
        except:
            er += 1
            print(f'erreur arcticle {url}')
    print(f'erreur sur : {er} articles')
    return df


def oneNewScrapper(urlScrapper, articleScrapper):
    try:
        urlsArticles = urlScrapper()
    except:
        print(f'failure scrap {urlScrapper.__name__}')
        return pd.DataFrame()
    df = pd.DataFrame()
    print('nombre d\'articles :', len(urlsArticles))
    er = 0
    for url in urlsArticles:
        try:
            df = df.append(articleScrapper(url), ignore_index = True)
        except:
            er += 1
            print(f'erreur arcticle {url}')
    print(f'erreur sur : {er} articles')
    return df

def newsScrapper(listScrapper = [leMondeScrapper,
                            nouvelobsScrapper,
                            humaniteScrapper,
                            lesechosScrapper,
                            laCroixScrapper,
                            figaroScrapper,
                            liberationScrapper,
                            parisienScrapper]):
    df = pd.concat([scrapper() for scrapper in listScrapper])
    return df
