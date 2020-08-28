#!/usr/bin/python3
# -*- coding: utf-8 -*-
import requests

theList = []
urlList = []
nameList = []
genreList = []
imageList = []
result = []

genres = ['Playlists', 'Hot Now', 'Folk', 'RnB', 'Legends', 'Decades', 'Rock', 'Soul and Motown', 'Jazz', 'Country', 'Soft Rock', 'Blues', 'New Station', 'Easy', 'Classical', 'All Stations', 'Calm', 'World', 'Dance', 'Wellness']

def getValues():
    theList = []
    for line in data:
        name = line.get('title')['rendered'].replace('Exclusively ', '').replace('Exclusively-', '').replace('&#8217;',"'").replace('&#038;', '& ')
        if name.startswith("-") and name.endswith("-"):
            name = name.replace("-", "")
        url = line.get('_exr_postmeta_stream').replace('https', 'http')
        if "radioboss" in url:
            url = f'http://streaming.exclusive.radio/er/{name.replace(" ", "").lower()}/icecast.audio'
        genre = '' 
        length = (len(line.get('_embedded')['wp:term'][0]))
        #print(length)
        if length == 1:    
            genre = line.get('_embedded')['wp:term'][0][0]['name']
        else:
            genre = line.get('_embedded')['wp:term'][0][1]['name']
        genre = genre.replace('Trending -The latest stations added to Exclusive Radio', 'New Station')
        image = line.get('x_featured_media_medium')
        line = f'{name},{url},{genre},{image}'
        theList.append(line)
        genreList.append(genre)
        urlList.append(url)
        nameList.append(name)
        imageList.append(image)
        
        
    return theList
    
def makeList(): ### Radio List
    for g in genres:
        header = f"-- Exclusive Radio {g} --"
        result.append(header)
        for x in range(len(nameList)):
            if genreList[x] == g:
                result.append(f'{nameList[x]},{urlList[x]},{imageList[x]}')
    return('\n'.join(result))


for x in range(1, 9):
    url = f"https://exclusive.radio/app//wp-json/wp/v2/stations/?page={x}&orderby=title&order=asc&_embed=true&per_page=99&search=&station_category=19"
    r = requests.get(url)
    if r:
        ### to json 
        data = r.json() 
        theList.append('\n'.join(getValues()))


result = makeList()

print(result)

with open('/tmp/excl_radio.txt', 'w', encoding='utf8') as f:
    f.write(result) 
    
