# Actux
A Rshiny app visualising usage of lems on french newspapers, and the scrapper doing the data collection.


## Scrapper

Based on Beautifullsoup.

scrap 8 big frenchnewspaper websites: libération, leMonde, l'humanité, lesEchos, le figaro, nouvelObs, leparisien, laCroix

The scrapper is deployed on a AWS ec2 programmed to run at 4am every day.

Data are accecible on a public s3 bucket as a .csv.gz file. (please don't spam request on it i'm limited by free AWS plan)

Lematization is done via spacy's french_lemmatizer

And parsing and classification is done via spacy's fr_core_news_md

## Rshiny APP

Small Rshiny app. ~~hosted here for now: https://drimer.shinyapps.io/actux/~~ (not anymore)

One tab to visualize quatity of data

One tab to search for the apparence of a spécific lem

I plan to add some stat about trending lemme

And maybe one about entities.


