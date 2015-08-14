#!/usr/bin/python
# -*- coding: utf-8 -*-

data = """South Denmark
Central Jutland
North Denmark
Vaestra Goetaland
Ostfold
Oppland
Hedmark
Hedmark
Nord-Trondelag
Nord-Trondelag
Nord-Trondelag
Nordland
Nordland
Nordland
Nordland
Nordland
Skane
Skane
Joenkoeping
Vaestra Goetaland
Vaermland
Vaermland
Dalarna
Jaemtland
Jaemtland
Nord-Trondelag
Nordland
Nordland
Nordland
Nordland
Nordland
Nordland
West Pomeranian Voivodeship
Blekinge
Kalmar
OEstergoetland
Vaestmanland
Dalarna
Gaevleborg
Vaesternorrland
Jaemtland
Vaesterbotten
Vaesterbotten
Nordland
Nordland
Troms
Nordland
Nordland
Pomeranian Voivodeship
Gotland
Gotland
Gotland
Stockholm
Uppsala
Uppsala
Vaesternorrland
Vaesternorrland
Vaesterbotten
Norrbotten
Norrbotten
Troms
Troms
Troms
Troms

Rucavas
Pavilostas
Ventspils
Alands skaergard
Southwest Finland
Satakunta
Ostrobothnia
Ostrobothnia
Vaesterbotten
Norrbotten
Norrbotten
Norrbotten
Troms
Troms
Troms
Kauno apskritis

Riga
Laeaene
Harju
Uusimaa
Pirkanmaa
Southern Ostrobothnia
Central Ostrobothnia
Northern Ostrobothnia
Norrbotten
Lapland
Lapland
Lapland
Finnmark Fylke
Finnmark Fylke
Minsk
Varkava
Gulbenes Rajons
Tartu
Laeaene-Virumaa
Kymenlaakso
Southern Savonia
Central Finland
Northern Savo
Northern Ostrobothnia
Lapland
Lapland
Lapland
Lapland
Lapland
Finnmark Fylke
Vitebsk
Pskov
Pskov
Pskov
Leningrad
Leningrad
South Karelia
North Karelia
North Karelia
Kainuu
Northern Ostrobothnia
Lapland
Lapland
Finnmark Fylke
Finnmark Fylke
Finnmark Fylke
Smolensk
Tverskaya
Novgorod
Novgorod
Novgorod
Leningrad
Republic of Karelia
Republic of Karelia
Republic of Karelia
Republic of Karelia
Republic of Karelia
Murmansk
Murmansk
Murmansk
Murmansk
Finnmark Fylke
"""

data = data.split("\n")
for row in set(data):
    print row