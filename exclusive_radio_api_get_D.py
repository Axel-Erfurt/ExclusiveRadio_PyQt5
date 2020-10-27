#!/usr/bin/python3
# -*- coding: utf-8 -*-
import requests, os, sys

class Updater():
    def __init__(self):
        self.theList = []
        self.urlList = []
        self.nameList = []
        self.genreList = []
        self.imageList = []
        self.result = []

        self.genres = ['Playlists', 'Hot Now', 'Folk', 'RnB', 'Legends', 'Decades', 'Rock', 'Soul and Motown', 'Jazz', 'Country', 'Soft Rock', 'Blues', 'New Station', 'Easy', 'Classical', 'All Stations', 'Calm', 'World', 'Dance', 'Wellness']
        
    def update(self):      
        for x in range(1, 9):
            url = f"https://exclusive.radio/app//wp-json/wp/v2/stations/?page={x}&orderby=title&order=asc&_embed=true&per_page=99&search=&station_category=19"
            r = requests.get(url)
            if r:
                ### to json 
                self.data = r.json() 
                self.theList.append('\n'.join(self.getValues()))
        
        self.result = self.makeList()
        
        #print(self.result)
        
        myfile = f"{os.path.dirname(sys.argv[0])}/excl_radio.txt"
        with open(myfile, 'w', encoding='utf8') as f:
            f.write(self.result) 

    def getValues(self):
        theList = []
        for line in self.data:
            name = line.get('title')['rendered'].replace('Exclusively ', '').replace('Exclusively-', '').replace('&#8217;',"'").replace('&#038;', ' and ')
            if name.startswith("-") and name.endswith("-"):
                name = name.replace("-", "")
            name = name.replace(",", " ")
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
            self.theList.append(line)
            self.genreList.append(genre)
            self.urlList.append(url)
            self.nameList.append(name)
            self.imageList.append(image)
            
            
        return self.theList
        
    def makeList(self): ### Radio List
        for g in self.genres:
            header = f"-- Exclusive Radio {g} --"
            self.result.append(header)
            for x in range(len(self.nameList)):
                if self.genreList[x] == g:
                    self.result.append(f'{self.nameList[x]},{self.urlList[x]},{self.imageList[x]}')
        return('\n'.join(self.result))
        print('\n'.join(self.result))

        
#upd = Updater()
#upd.update()
