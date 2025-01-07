from newsfilter.scorer import Scorer
from newsfilter.loader import NewsArticle
import datetime


def test_score_1():
    article = NewsArticle(
        link="https://nos.nl/l/2550842",
        title="Sporttrainer die kinderkampen begeleidde verdacht van seksueel misbruik",
        summary="<p>Een 37-jarige man uit Bodegraven wordt verdacht van seksueel misbruik van minderjarigen en het delen van kinderporno. Dat gebeurde mogelijk jarenlang. Dat bleek tijdens een pro-formazitting bij de rechtbank in Den Haag. De man zit al sinds de zomer vast.</p>\n<p>Uit het onderzoek naar de man is volgens justitie naar boven gekomen dat hij zeker drie minderjarigen fysiek heeft misbruikt. Ook bleek daaruit dat de man kinderporno deelde via een versleutelde communicatiedienst. Daarbij gaat het niet om materiaal van de nu bekende slachtoffers, zegt het OM. De verdenkingen staan vooralsnog los van elkaar.</p>\n<p>De man benaderde slachtoffers mogelijk bij een klimvereniging in sportcentrum Pentagon in Dordrecht, waar hij van 2003 tot eind 2019 actief was als sporttrainer.</p>\n<p>Daarnaast was hij van 2003 tot eind 2018 verbonden aan de Zuidhovenkerk in Dordrecht, waar hij kinderkampen begeleidde. Daarna was hij tot juli 2024 lid van de Ichthuskerk in Bodegraven. Volgens het OM is het niet uitgesloten dat hij via die kerken in contact kwam met minderjarigen.</p>\n<h2>Versleutelde apps</h2>\n<p>Het Team Bestrijding Kinderporno en Kindersekstoerisme van de politie kwam de man op het spoor in de zomer van vorig jaar, bij een onderzoek naar kinderporno op versleutelde chatapps. De man viel op omdat hij beelden deelde van seksueel misbruik van soms zeer jonge kinderen in verschillende groepen, aldus het OM.</p>\n<p>In de chats sprak de verdachte veelvuldig over het jarenlange seksueel misbruik van minderjarigen dat hij zou hebben gepleegd, bij zowel jongens als meisjes. De man is aangehouden op 26 juli vorig jaar en zit sindsdien in voorlopige hechtenis.</p>\n<p>Hoeveel slachtoffers hij heeft gemaakt is onduidelijk. De politie is op zoek naar slachtoffers en getuigen.</p>",
        image_url="https://cdn.nos.nl/image/2025/01/07/1176663/1008x567.jpg",
        published=datetime.datetime.now(),
    )

    scored = Scorer().score(article)

    print(f'Scored {scored.score} because "{scored.reason}"')

    assert scored.score < 7


def test_score_2():
    article = NewsArticle(
        link="https://nos.nl/l/2550872",
        title="Meta stopt samenwerking met factcheckers in de VS vanwege 'censuur'",
        published=datetime.datetime.now(),
        summary='<p>Het Amerikaanse techbedrijf Meta stopt de samenwerking met factcheckers in de Verenigde Staten. Dat heeft eigenaar Mark Zuckerberg vandaag aangekondigd. In plaats daarvan gaat Meta, het moederbedrijf van Facebook en Instagram, over op een systeem waarbij andere gebruikers commentaar kunnen leveren op mogelijk misleidende berichtgeving.</p>\n<p>Het systeem op basis van opmerkingen van gebruikers is vergelijkbaar met Community Notes van X. In dit systeem hebben gebruikers de mogelijkheid om commentaar te geven op potentieel misleidende posts. Het zijn dus niet meer professionele factcheckers die de inhoud toetsen.</p>\n<p>Het bedrijf zegt de samenwerking met experts, onder wie journalisten van grote internationale persbureaus, op omdat die volgens Zuckerberg "politiek bevooroordeeld" zijn. "De factcheckers hebben het vertrouwen meer kwaad dan goed gedaan", zegt Zuckerberg in een videoboodschap.</p>\n<h2>Immigratie en gender</h2>\n<p>Zuckerberg zegt ook het moderatiebeleid rondom bepaalde onderwerpen te willen veranderen. "We willen minder restricties rondom onderwerpen als immigratie en gender." Volgens hem zijn Facebook en Instagram veranderd van inclusieve platforms naar platforms waar mensen te snel de mond wordt gesnoerd.</p>\n<p>Ook worden er volgens hem te veel berichten op feiten gecheckt en gecensureerd. Partijen die de factchecks doen zijn bijvoorbeeld medewerkers van grote internationale persbureaus als AFP, AP en Reuters.</p>\n<p>Zuckerberg zei dat de afgelopen verkiezingen in de VS een grote rol hebben gespeeld bij zijn besluit. "De laatste verkiezingen voelen als een cultureel omslagpunt om vrijheid van meningsuiting opnieuw op de voorgrond te zetten."</p>\n<p>De wijzigingen zullen gevolgen hebben voor Instagram, Facebook en Threads. De socialemediaplatforms hebben wereldwijd miljarden gebruikers. Zuckerberg zegt de aanpassingen de komende maanden te willen doorvoeren.</p>\n<p>Wat dit nieuws betekent voor de platforms van Meta in Europa, is nog niet duidelijk.</p>',
        image_url="https://cdn.nos.nl/image/2025/01/07/1176766/1008x567.jpg",
    )

    scored = Scorer().score(article)

    print(f'Scored {scored.score} because "{scored.reason}"')

    assert scored.score < 7
