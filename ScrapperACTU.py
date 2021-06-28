#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import boto3
import io
from pyarrow import feather
import gc
import spacy
from spacy_lefff import LefffLemmatizer
from spacy.language import Language
from datetime import datetime
import logging

from scrapperFuncs import newsScrapper

def read_feather_file_from_s3(s3_url):
    assert s3_url.startswith("s3://")
    bucket_name, key_name = s3_url[5:].split("/", 1)

    s3 = boto3.client('s3')
    try:
        retr = s3.get_object(Bucket=bucket_name, Key=key_name)
    except s3.exceptions.NoSuchKey:
        print('url erreur no key')
        return False
    except s3.exceptions.NoSuchBucket:
        print('url erreur bucket')
        return False
    return pd.read_feather(io.BytesIO(retr['Body'].read()))

def read_csv_file_from_s3(s3_url):
    assert s3_url.startswith("s3://")
    bucket_name, key_name = s3_url[5:].split("/", 1)

    s3 = boto3.client('s3')
    try:
        retr = s3.get_object(Bucket=bucket_name, Key=key_name)
    except s3.exceptions.NoSuchKey:
        print('url erreur no key')
        return False
    except s3.exceptions.NoSuchBucket:
        print('url erreur bucket')
        return False
    return pd.read_csv(io.BytesIO(retr['Body'].read()), sep= ';', compression='gzip')


@Language.factory('french_lemmatizer')
def create_french_lemmatizer(nlp, name):
    return LefffLemmatizer()


def specialStopWords(file = 'stopWordsBonus.txt'):
    try:
        with open(file, 'r', encoding= 'utf-8') as f:
            return [l.rstrip() for l in f]
    except FileNotFoundError:
        print('stopWords not found')
        logging.warning('Watch out!')
        return []

def listWordIsnside(text, nlp):
    doc = nlp(text)
    l = [w for w in doc if (not w.is_stop and not w.is_punct and not w.like_num)]
    listWords = set([d._.lefff_lemma if d._.lefff_lemma is not None else d.text.lower().strip() for d in l])
    stopWords = list(nlp.Defaults.stop_words) + specialStopWords()
    return [l for l in listWords if l not in stopWords]

def miseEnFormeDatacount(df):
    nlp = spacy.load('fr_core_news_md')
    nlp.add_pipe('french_lemmatizer', name='lefff')
    df['listWords'] = df['texte'].apply(lambda x: listWordIsnside(x,nlp))
    dfWords = df[['date', 'date_scrap', 'journal', 'domaine', 'listWords','url']].explode('listWords').groupby(['date', 'date_scrap', 'journal', 'domaine', 'listWords']).agg(count =('url', 'count'))
    return dfWords.reset_index()

def main():
    print('-------------------------------')
    print('Scrapping ...')
    logging.info("Scrapping started : {0} ".format(datetime.now().strftime('%m/%d/%Y-%H:%M:%S')))
    dfNew = newsScrapper()
    logging.info("Scrapping complete {0} ".format(datetime.now().strftime('%m/%d/%Y-%H:%M:%S')))
    print('-------------------------------')
    print('Downloading...')
    df_old = read_csv_file_from_s3('s3://actux-bucket/data_Actux.csv.gz')
    print('-------------------------------')
    print('Cleaning...')
    dfNew = dfNew[~dfNew.url.isin(df_old['url'])]
    dfConcat = pd.concat([df_old, dfNew], sort = False)
    dfConcat = dfConcat.reset_index(drop=True)
    dfConcat.to_csv('data_Actux.csv.gz', sep= ';', index=False, compression="gzip")
    del dfConcat, df_old
    gc.collect()
    print('-------------------------------')
    print('Counting Words ...')
    dfWordsNew = miseEnFormeDatacount(dfNew)
    print('-------------------------------')
    print('Downloading...')
    df_old_count = read_csv_file_from_s3('s3://actux-bucket/data_Actux_count.csv.gz')
    dfWorldConcat = pd.concat([dfWordsNew, df_old_count], sort = False)
    dfWorldConcat = dfWorldConcat.reset_index(drop=True)
    dfWorldConcat.to_csv('data_Actux_count.csv.gz', sep= ';', index=False, compression="gzip")
    print('-------------------------------')
    print('Uploading ...')
    del dfWorldConcat, df_old_count
    gc.collect()
    s3 = boto3.resource('s3')
    s3.meta.client.upload_file('data_Actux.csv.gz', 'actux-bucket', 'data_Actux.csv.gz', ExtraArgs={'ACL':'public-read'})
    s3.meta.client.upload_file('data_Actux_count.csv.gz', 'actux-bucket', 'data_Actux_count.csv.gz', ExtraArgs={'ACL':'public-read'})
    logging.info("Uploading csv complete : {0}".format(datetime.now().strftime('%m/%d/%Y-%H:%M:%S')))

if __name__=="__main__":
    logging.basicConfig(filename='scrapper.log', level=logging.INFO)
    try:
        main()
    except:
        logging.ERROR("Scrapping failed :{0} ".format(datetime.now().strftime('%m/%d/%Y-%H:%M:%S')))
