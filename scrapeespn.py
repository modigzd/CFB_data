# -*- coding: utf-8 -*-
"""
Class to scrape ESPN data


Zach Modig
December 2016

To do:
    
    Think about subclasses- college and nfl
"""


import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from bs4 import SoupStrainer
import urllib
import re
import itertools


class ScrapeESPN(object):
    
    
    def __init__(self):
        
        #instantiate some properties
        self.team_ids = dict()
        self.game_ids = []
        

        
    def getTeamIDs(self,url):
    #get team IDs given a url
    #
    #Set the team name/id dictionary as a property of ScrapeESPN
    #Return the data set if requested
    
    
        r = urllib.request.urlopen(url).read() #read the html contents into r
        soup = BeautifulSoup(r, 'html.parser') #create a BeautifulSoup class object
        #soup = BeautifulSoup(r, 'lxml')
        
        #get all team names/IDs
        #to do - get conference, FBS/FCS
        tags = soup.find_all('a', class_="bi") #get the team tags
        ids = dict()
        for team in tags:
            
            tmpid = re.findall(r'.+/id/([0-9]+?)/.+',str(team)) #team ID
            tmpnm = team.string #team name
            ids[tmpnm] = int(tmpid[0]) #set the dictionary {team name:id(as an integer)}
        
        #set the team name/id dictionary as a property of the scraper
        self.team_ids = ids
        
        #return ids #return the id dictionary if requested
    
    
    
    def getPlaybyPlay(self,url):
    #actually scrape the play-by-play data
        
        #use SoupStrainer to break into parts for easier/more reliable browsing
        at = SoupStrainer('div',class_="team away") #away team data
        ht = SoupStrainer('div',class_="team home") #home team data
        pbp = SoupStrainer('div',id="gamepackage-play-by-play") #pbp data
        
        r = urllib.request.urlopen(url).read() #read url data

        #get team data
        home = self.getHeaderData(r,ht)
        away = self.getHeaderData(r,at)
        
        soup = BeautifulSoup(r,'html.parser',parse_only=pbp) #get just the play-by-play part of the html

        #get relevant drive information
        offense = []
        defense = []
        details = []
        result = []
        #play = []
        #dnd = []
        drive_info = []
        #home_team = []
        home_score = []
        #away_team = []
        away_score = []
        drive = []
        cnt = 1
        #for tx in soup.findAll('li',class_="accordion-item"):
        for tx in soup.findAll('div',class_="accordion-header"):
            
            #get the team on offense (and on defense) and save team name info rather than url link
            tmp = tx.contents[0].findAll('img',class_="team-logo")[0].get('src')
            if home['url'][0] == tmp:
                offense.append(home['Abbreviation'][0])
                defense.append(away['Abbreviation'][0])
            else:
                offense.append(away['Abbreviation'][0])
                defense.append(home['Abbreviation'][0])
                
            result.append(tx.contents[0].find('span',class_="headline").text)
            details.append(tx.contents[0].find('span',class_="drive-details").text)
            #home_team.append(tx.contents[0].find('span',class_="home").find('span',class_="team-name").text)
            home_score.append(int(tx.contents[0].find('span',class_="home").find('span',class_="team-score").text))
            #away_team.append(tx.contents[0].find('span',class_="away").find('span',class_="team-name").text)
            away_score.append(int(tx.contents[0].find('span',class_="away").find('span',class_="team-score").text))
        
            drive.append(cnt)
            cnt += 1
            
        for tx in soup.findAll('ul',class_="drive-list"):
            
            ptmp = []
            dtmp = []
            #maybe create a unique key here? Link that to the play? Try - GameID_DriveNumber?
            #add possession number, team possession number, play number, team play number, and play number of drive to info
            for tx2 in tx.findAll('span',class_="post-play"):
                ptmp.append(str.strip(tx2.text))
            for tx2 in tx.findAll('h3'):
                dtmp.append(tx2.text)

            #update play and down&distance
            di = pd.DataFrame({'Play Description':ptmp,'Down and Distance':dtmp})
            drive_info.append(di)
            #play.append(ptmp)
            #dnd.append(dtmp)
            
        #package as a dataframe for output
        #d = {'Drive Number':drive,'Down Distance':dnd,'Play-by-Play':play,'Result':result,'Drive Summary':details,
        #     'Offense':offense,'Defense':defense,'Home Score':home_score,'Away Score':away_score}
        d = {'Drive Number':drive,'Drive Info':drive_info,'Result':result,'Drive Summary':details,
             'Offense':offense,'Defense':defense,'Home Score':home_score,'Away Score':away_score}
        
        
        play_by_play = pd.DataFrame(d)
        
        
        return play_by_play, home, away
        
            
        
    def getGameInfo(self,url):
    #get ESPN game information

        r = urllib.request.urlopen(url).read() #read the html contents into r
        part = SoupStrainer('article',class_="sub-module game-information")#define the submodule as game-info
        soup = BeautifulSoup(r,'html.parser',parse_only=part) #parse only the submodule
        
        #get info
        stadium = str.strip(soup.find(class_="caption-wrapper").text) #stadium name
        coverage = str.strip(soup.find(class_="game-network").text) #tv coverage
        location = str.strip(soup.find('li',class_="icon-font-before icon-location-solid-before").text)        
        
        #get the zip code
        tmpz = re.findall(r'[0-9]+',soup.li.text)
        zip_code = int(tmpz[0])
        
        #get kick-off time
        tmp = str(soup.span)
        tmp = re.findall(r'data-date=\"(.+)\"',tmp) #list of strings
        tmp = re.split('T',tmp[0]) #split into date and time
        date = tmp[0]
        time = tmp[1]
        
        #store the variables in a data frame
        Game_Info = pd.DataFrame(data={'stadium':stadium,'coverage':coverage,'location':location,
                                       'zip':zip_code,'date':date,'time':time},index=[0])
        
        #output game info
        return Game_Info 
        
        

    def getAllGameIDs(self,year,week):
    #get a list of all gameIDs by year
    #year and week are lists of all 
        
        game_ids = pd.DataFrame(data={'Game ID':[],'Year':[],'Week':[]})
        for ii in range(len(year)):
            for jj in range(len(week)):
                
                #build the url string
                if week == 'bowl':            
                    url = 'http://www.espn.com/college-football/schedule/_/year/' + str(year[ii])                    
                elif week != 1:            
                    url = 'http://www.espn.com/college-football/schedule/_/seasontype/2/year/' + str(year[ii]) + '/week/' + str(week[jj]) 
                else:
                    url = 'http://www.espn.com/college-football/schedule/_/seasontype/2/year/' + str(year[ii])
                
                ids = self.getGameIDs(url)
                yr = list(itertools.repeat(int(year[ii]),len(ids)))
                wk = list(itertools.repeat(int(week[jj]),len(ids)))
                
                tmp = pd.DataFrame(data={'Game ID':ids,'Year':yr,'Week':wk})
                    
                game_ids = game_ids.append(tmp)
                
        self.game_ids = game_ids
    
        
    
    def getGameIDs(self,url):
    #return all game Id's for a given year/week
    #return a list of the game Ids 
    
        r = urllib.request.urlopen(url).read()
        game_ids = re.findall(r'gameId=([0-9]+?)\"',str(r))
        
        return game_ids
    
        
        
    def getHeaderData(self,html,part):
    #get header info (home/away) from play-by-play page
    #return the data as a pandas data frame
    
        #just get the 
        soup = BeautifulSoup(html,'html.parser',parse_only=part)
        
        img_tag = soup.findAll('img')[0].get('src') #get url for the image (to determine home/away)
        long = str(soup.find('span',class_="long-name").text)
        short = str(soup.find('span',class_="short-name").text)
        abbr = str(soup.find('span',class_="abbrev").text)
        record = str(soup.find('div',class_="record").text)
        
        #package for export
        team_id = pd.DataFrame(data={'url':img_tag,'Long Name':long,'Short Name':short,
                                     'Abbreviation':abbr,'Team Record':record},index=[0])
    
        return team_id

    

