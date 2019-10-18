# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, MergeDicts
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads, dumps as json_dumps
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
###################################################

###################################################
# FOREIGN import
###################################################
import re
import urllib
import datetime
import HTMLParser
###################################################


def gettytul():
    return 'http://raiplay.it/'

class Raiplay(CBaseHostClass):
 
    def __init__(self):

        CBaseHostClass.__init__(self, {'history':'raiplay', 'cookie':'raiplay.it.cookie'})
        self.MAIN_URL = 'http://raiplay.it/'
        self.MENU_URL="http://www.rai.it/dl/RaiPlay/2016/menu/PublishingBlock-20b274b1-23ae-414f-b3bf-4bdc13b86af2.html?homejson"
        self.CHANNELS_URL= "http://www.rai.it/dl/RaiPlay/2016/PublishingBlock-9a2ff311-fcf0-4539-8f8f-c4fee2a71d58.html?json"
        self.CHANNELS_RADIO_URL="http://rai.it/dl/portaleRadio/popup/ContentSet-003728e4-db46-4df8-83ff-606426c0b3f5-json.html"
        self.EPG_URL_OLD = "http://www.rai.it/dl/palinsesti/Page-e120a813-1b92-4057-a214-15943d95aa68-json.html?canale=[nomeCanale]&giorno=[dd-mm-yyyy]"
        #self.EPG_URL = "https://www.raiplay.it/guidatv/lista?canale=[nomeCanale]&giorno=[dd-mm-yyyy]"
        self.EPG_URL = 'https://www.raiplay.it/palinsesto/guidatv/lista/[idCanale]/[dd-mm-yyyy].html'
        self.TG_URL = "http://www.tgr.rai.it/dl/tgr/mhp/home.xml"
        
        self.RAISPORT_MAIN_URL = 'https://www.raisport.rai.it'
        self.RAISPORT_LIVE_URL = self.RAISPORT_MAIN_URL + '/dirette.html'
        self.RAISPORT_ARCHIVIO_URL = self.RAISPORT_MAIN_URL + '/archivio.html'        
        self.RAISPORT_SEARCH_URL = self.RAISPORT_MAIN_URL + "/atomatic/news-search-service/api/v1/search?transform=false"
        
        self.DEFAULT_ICON_URL = "https://images-eu.ssl-images-amazon.com/images/I/41%2B5P94pGPL.png"
        self.NOTHUMB_URL = "http://www.rai.it/cropgd/256x144/dl/components/img/imgPlaceholder.png"

        self.HTTP_HEADER = self.cm.getDefaultHeader(browser='chrome')        
        self.RELINKER_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36"

        self.defaultParams = {'header':self.HTTP_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.RaiSportKeys = []
        
    def getPage(self, url, addParams = {}, post_data = None):
        if addParams == {}:
            addParams = dict(self.defaultParams)
        return self.cm.getPage(url, addParams, post_data)

    def getThumbnailUrl(self, pathId):
        if pathId == "":
            url = self.NOTHUMB_URL
        else:
            url = self.getFullUrl(pathId)
            url = url.replace("[RESOLUTION]", "256x-")
        return url

    def getFullUrl(self, url):
        if url == "" : return
        
        if url[:9] == "/raiplay/":
            url = url.replace ("/raiplay/",self.MAIN_URL)

        while url[:1] == "/" :
            url=url[1:]
            
        # Add the server to the URL if missing
        if url.find("://") == -1:
            url = self.MAIN_URL + url

        url = url.replace(" ", "%20")
        #url = urllib.quote(url, safe="%/:=&?~#+!$,;'@()*[]")
            
        #printDBG("PathID: " + url)
        
        return url
    
    def getLinksForVideo(self, cItem):
        printDBG("Raiplay.getLinksForVideo [%s]" % cItem)
        #sts, data=self.getPage(cItem["url"])
        #if not sts: return

        #printDBG(data)

        linksTab=[]
        if (cItem["category"] == "live_tv") or (cItem["category"] == "live_radio") or (cItem["category"]=="video_link") or (cItem["category"] == "raisport_video"):   
            url = cItem['url']
            linksTab.append({'name': 'hls', 'url': url})           
            
            url = strwithmeta( url, {'User-Agent': self.RELINKER_USER_AGENT})
            linksTab.extend(getDirectM3U8Playlist(url, checkExt=False, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999))  
            
        elif (cItem["category"] == "program"):
            # read relinker page
            program_url=cItem["url"]
            program_url=program_url.replace ("/raiplay/",self.MAIN_URL)
            
            sts, data = self.getPage(program_url)
            if sts:
                # bypass an error of delimiters in json
                s_name = re.findall("\"name\": \"(.*?)\",",data)
                for s in s_name:
                    data = data.replace(s, s.replace("\""," "))   
                #
                response =json_loads(data)
                video_url=response["video"]["contentUrl"]
                printDBG(video_url);
                video_url=strwithmeta(video_url, {'User-Agent': self.RELINKER_USER_AGENT })
                linksTab.append({'name': 'hls', 'url': video_url})           
                linksTab.extend(getDirectM3U8Playlist(video_url, checkExt=False, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999))  
            
        else:
            printDBG("Raiplay: video form category %s with url %s not handled" % (cItem["category"],cItem["url"]));
            linksTab.append({'url': cItem["url"], 'name': 'link1'})
        
        return linksTab

    def listMainMenu(self, cItem):
        MAIN_CAT_TAB = [{'category':'live_tv', 'title': 'Dirette tv'},
                        {'category':'live_radio', 'title': 'Dirette radio'},
                        {'category':'replay', 'title': 'Replay'},
                        {'category':'ondemand', 'title': 'Programmi on demand'},
                        {'category':'tg', 'title': 'Archivio Telegiornali'},
                        {'category':'raisport_main', 'title':'Archivio Rai Sport'}]  
        self.listsTab(MAIN_CAT_TAB, cItem)  

    def listLiveTvChannels(self, cItem):
        printDBG("Raiplay - start live channel list")
        sts, data = self.getPage(self.CHANNELS_URL)
        if not sts: return
 
        response = json_loads(data)
        tv_stations = response["dirette"]
        #printDBG(data)

        for station in tv_stations:
            title = station["channel"]
            desc = station["description"]
            icon = self.getThumbnailUrl(station["transparent-icon"])           
            url = station["video"]["contentUrl"]
            params = dict(cItem)
            params = {'title':title, 'url':url, 'icon':icon, 'category': 'live_tv', 'desc': desc}
            self.addVideo(params)
        
        #add raisport webstreams
        sts, data = self.getPage(self.RAISPORT_LIVE_URL)
        if not sts: 
            return
         
        tmp = self.cm.ph.getDataBeetwenNodes(data, '<ul class="canali">', '</ul>')[1]
        items = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<li>', '</li>')
        for i in items:
            url = self.cm.ph.getSearchGroups(i, '''data-video-url=['"]([^'^"]+?)['"]''')[0]
            if url:
                icon = self.cm.ph.getSearchGroups(i, '''stillframe=['"]([^'^"]+?)['"]''')[0]
                #if icon:
                #    icon = icon
                title = self.cleanHtmlStr(i)

                params = dict(cItem)
                params = {'title':title, 'url':url, 'icon':icon, 'category': 'live_tv', 'desc': desc}
                self.addVideo(params)
            
    def listLiveRadioChannels(self, cItem):
        printDBG("Raiplay - start live radio list")
        sts, data = self.getPage(self.CHANNELS_RADIO_URL)
        if not sts: return
 
        response = json_loads(data)
        radio_stations = response["dati"]
        #printDBG(data)

        for station in radio_stations:
            title = station["nome"]
            desc = station["chText"]
            icon = "http://www.rai.it" + station["chImage"]       
            if station["flussi"]["liveAndroid"] != "":
                url = station["flussi"]["liveAndroid"]
            params = dict(cItem)
            params = {'title':title, 'url':url, 'icon':icon, 'category': 'live_radio', 'desc': desc }

            self.addVideo(params)

    def daterange(self, start_date, end_date):
        for n in range((end_date - start_date).days + 1):
            yield end_date - datetime.timedelta(n)

    def listReplayDate (self, cItem):
        printDBG("Raiplay - start replay/EPG section")

        days = ["Domenica", "Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato"]
        months = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", 
        "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
    
        epgEndDate = datetime.date.today()
        epgStartDate = datetime.date.today() - datetime.timedelta(days=7)
    
        for day in self.daterange(epgStartDate, epgEndDate):
            day_str = days[int(day.strftime("%w"))] + " " + day.strftime("%d") + " " + months[int(day.strftime("%m"))-1]
            self.addDir(MergeDicts(cItem, {'category':'replay_date', 'title': day_str , 'name': day.strftime("%d-%m-%Y")}))              

    def listReplayChannels(self, cItem):
        day=cItem['name']
        printDBG("Raiplay - start replay/EPG section - channels list for %s " % day)

        sts, data = self.getPage(self.CHANNELS_URL)
        if not sts: return
 
        response = json_loads(data)
        tv_stations = response["dirette"]
    
        for station in tv_stations:
            title = station["channel"] 
            name = day + "|" + station["channel"]
            icon = self.MAIN_URL + station["icon"]          
            self.addDir(MergeDicts(cItem, {'category':'replay_channel', 'title': title , 'name': name }))              

            
    def listEPG(self, cItem):
        str1 = cItem['name']
        epgDate = str1[:10]
        channelName = str1[11:]
        printDBG("Raiplay - start EPG for channel %s and day %s" % (channelName,epgDate))
        
        channel_id = channelName.replace(" ", "-").lower()
        url = self.EPG_URL
        url = url.replace("[idCanale]", channel_id)
        url = url.replace("[dd-mm-yyyy]", epgDate)
        
        sts, data = self.getPage(url)
        if not sts: 
            return
        
        items = self.cm.ph.getAllItemsBeetwenMarkers(data, ('<li', '>', 'eventSpan'), '</li>')
        
        for i in items:
            videoUrl = self.getFullUrl(self.cm.ph.getSearchGroups(i, '''data-href=['"]([^'^"]+?)['"]''')[0])
            
            icon = self.cm.ph.getSearchGroups(i, '''data-img=['"]([^'^"]+?)['"]''')[0]
            if icon:
                icon = self.getFullUrl(icon)
            else:
                icon =''
            title = re.findall("<p class=\"info\">([^<]+?)</p>", i)
            if title:
                title = title[0]
            else:
                title = ''
            
            startTime = re.findall("<p class=\"time\">([^<]+?)</p>", i)
            if startTime:
                title = startTime[0] + " " + title
            
            desc = re.findall("<p class=\"descProgram\">([^<]+?)</p>", i, re.S)
            if desc:
                desc= desc[0]
            else:
                desc=""
            
            params={}
            if videoUrl:
                if not videoUrl.endswith('json'):
                    videoUrl = videoUrl + "?json"
                params = {'title':title, 'url':videoUrl, 'icon': icon, 'category': 'program', 'desc': desc}
            else:
                # programme is not available
                title = title + "\c00??8800 [" + _("not available") + "]"
                params = {'title':title, 'url':'', 'icon': icon, 'desc': desc, 'category': 'nop'}
                
            printDBG(str(params)) 
            self.addVideo(params)
            
        
    def listOnDemandMain(self, cItem):
        printDBG("Raiplay - start on demand main list")
        sts, data = self.getPage(self.MENU_URL)
        if not sts: return
 
        response = json_loads(data)
        items=response["menu"]

        for item in items:
            if item["sub-type"] in ("RaiPlay Tipologia Page", "RaiPlay Genere Page", "RaiPlay Tipologia Editoriale Page"):
                icon_url=self.MAIN_URL + item["image"]
                self.addDir(MergeDicts(cItem, {'category':'ondemand_items', 'title': item["name"] , 'name': item["name"], 'url': item["PathID"], 'icon': icon_url, 'sub-type': item["sub-type"] }))            

                
    def listOnDemandCategory(self, cItem):
        pathId=cItem["url"]
        pathId=self.getFullUrl(pathId)
        printDBG("Raiplay - processing item %s of sub-type %s with pathId %s" % (cItem["title"], cItem["sub-type"], pathId ))
        
        sts, data = self.getPage(pathId)
        if not sts: return
 
        response = json_loads(data)
        blocks=response["blocchi"]

        if len(blocks) > 1:
            printDBG("Blocchi: " + str(len(blocks)))
        
        for item in blocks[0]["lanci"]:
            if item["images"]["portrait"]!="" :
                icon_url=self.getThumbnailUrl(item["images"]["portrait"])
            else:
                icon_url=self.getThumbnailUrl(item["images"]["landscape"])

            self.addDir(MergeDicts(cItem, {'category':'ondemand_items', 'title': item["name"] , 'name': item["name"], 'url': item["PathID"], 'sub-type': item["sub-type"], 'icon': icon_url }))           

            
    def listOnDemandAZ(self,cItem):
        pathId=cItem["url"]
        pathId=self.getFullUrl(pathId)
        printDBG("Raiplay - processing list with pathId %s" % pathId )

        # 0-9
        self.addDir(MergeDicts(cItem, {'category':'ondemand_list', 'title': "0-9" , 'name': "0-9", 'url': pathId} ))              
        
        #a-z
        for i in range(26):
            self.addDir(MergeDicts(cItem, {'category':'ondemand_list', 'title': chr(ord('A')+i) , 'name': chr(ord('A')+i), 'url': pathId} ))              

            
    def listOnDemandIndex(self,cItem):
        pathId=cItem["url"]
        pathId=self.getFullUrl(pathId)
        
        sts, data = self.getPage(pathId)
        if not sts: return
 
        response = json_loads(data)
        items=response[cItem["name"]]
        for item in items:
            name=item["name"]
            url=item["PathID"]
            self.addDir(MergeDicts(cItem, {'category':'ondemand_items', 'title': name , 'name': name, 'url': url, 'sub-type': 'PLR programma Page' } ))              
            
    def listOnDemandProgram(self,cItem):
        pathId=cItem["url"]
        pathId=self.getFullUrl(pathId)

        sts, data = self.getPage(pathId)
        if not sts: return
        
        response = json_loads(data)
        blocks=response["Blocks"]

        for block in blocks:
            for set in block["Sets"]:
                name = set["Name"]
                url=set["url"]
                self.addDir(MergeDicts(cItem, {'category':'ondemand_program', 'title': name , 'name': name, 'url': url} ))              
                
    def listOnDemandProgramItems(self,cItem):
        pathId=cItem["url"]
        pathId=self.getFullUrl(pathId)

        sts, data = self.getPage(pathId)
        if not sts: return

        response = json_loads(data)
        items = response["items"]

        for item in items:
            title = item["name"]
            if "subtitle" in item and item["subtitle"] != "" and item["subtitle"] != item["name"]:
                title = title + " (" + item["subtitle"] + ")"
            
            videoUrl=item["pathID"]
            if item["images"]["portrait"]!="" :
                icon_url=self.getThumbnailUrl(item["images"]["portrait"])
            else:
                icon_url=self.getThumbnailUrl(item["images"]["landscape"])
            
            params = {'title':title, 'url':videoUrl, 'icon': icon_url, 'category': 'program'}
            printDBG ("add video '%s' with pathId '%s'" % (title,videoUrl)) 
            
            self.addVideo(params)
    
    def listTg(self,cItem):
        printDBG("Raiplay start tg list")
        TG_TAB = [{'category':'tg1', 'title': 'TG 1'}, {'category':'tg2', 'title': 'TG 2'},
                  {'category':'tg3', 'title': 'TG 3'}, {'category':'tgr-root', 'title': 'TG Regionali'}]
        self.listsTab(TG_TAB, cItem)  
    
    
    def listTgr(self,cItem):
        printDBG("Raiplay. start tgr list")
        if cItem["category"]!="tgr-root" :
            url=cItem["url"]
        else:
            url =self.TG_URL
            
        sts, data = self.getPage(url)
        if not sts: return
        
        # search for dirs
        items = ph.findall(data, '<item behaviour="region">', '</item>', flags=0)
        items.extend( ph.findall(data, '<item behaviour="list">', '</item>', flags=0))

        for item in items:
            r_title=ph.find(item,'<label>','</label>',flags=0)
            r_url=ph.find(item,'<url type="list">','</url>',flags=0)
            r_image=ph.find(item,'<url type="image">','</url>',flags=0)
            if r_title[0] and r_url[0]:
                if r_image[0]:
                    icon= self.MAIN_URL + r_image[1]
                else:
                    icon=self.NOTHUMB_URL
                    
                title=r_title[1]
                url=self.MAIN_URL + r_url[1]
                self.addDir(MergeDicts(cItem, {'category':'tgr', 'title': title , 'url': url, 'icon': icon} ))              
                
        # search for video links
        items = ph.findall(data, '<item behaviour="video">', '</item>', flags=0)
        for item in items:
            r_title=ph.find(item,'<label>','</label>',flags=0)
            r_url=ph.find(item,'<url type="video">','</url>',flags=0)
            r_image=ph.find(item,'<url type="image">','</url>',flags=0)
            if r_title[0] and r_url[0]:
                if r_image[0]:
                    icon= self.MAIN_URL + r_image[1]
                else:
                    icon=self.NOTHUMB_URL
                    
                title=r_title[1]
                videoUrl = r_url[1]
                params = {'title':title, 'url':videoUrl, 'icon': icon, 'category': 'video_link'}
                printDBG ("add video '%s' with pathId '%s'" % (title,videoUrl)) 
                self.addVideo(params)
    
    def searchLastTg(self,cItem):
        category=cItem['category']
        if category == 'tg1' :
            tag="NomeProgramma:TG1^Tematica:Edizioni integrali"
        elif category == 'tg2' :
            tag="NomeProgramma:TG2^Tematica:Edizione integrale"
        elif category == 'tg3':
            tag="NomeProgramma:TG3^Tematica:Edizioni del TG3"
        else:
            printDBG("Raiplay unhandled tg category %s" % category)
            return
                       
        items=self.getLastContentByTag(tag)
        if items == None : return
        
        for item in items:
            title=item["name"]
            if item["images"]["portrait"]!="" :
                icon_url=self.getThumbnailUrl(item["images"]["portrait"])
            else:
                icon_url=self.getThumbnailUrl(item["images"]["landscape"])

            videoUrl=item["Url"]
            params = {'title':title, 'url':videoUrl, 'icon': icon_url, 'category': 'video_link'}
            printDBG ("add video '%s' with pathId '%s'" % (title,videoUrl)) 
            
            self.addVideo(params)
    
    def getLastContentByTag(self, tags="", numContents=16):
        tags = urllib.quote(tags)
        domain = "RaiTv"
        xsl = "rai_tv-statistiche-raiplay-json"
        
        url = "http://www.rai.it/StatisticheProxy/proxyPost.jsp?action=getLastContentByTag&numContents=%s&tags=%s&domain=%s&xsl=%s" % (str(numContents), tags, domain, xsl)
        sts, data = self.getPage (url) 
        if not sts: return 
        
        if data == "" : 
            return
        response=json_loads(data)
        return response["list"]
    
    def fillRaiSportKeys(self):
        printDBG("Raiplay.fillRaiSportKeys")
        
        # search for items in main menu
        sts, data = self.getPage(self.RAISPORT_MAIN_URL)
        if not sts: 
            return
        menu = self.cm.ph.getDataBeetwenMarkers(data, '<a href="javascript:void(0)">Menu</a>', '</div>')[1]
        #printDBG(menu)
        
        links = re.findall("<a href=\"(?P<url>[^\"]+)\">(?P<title>[^<]+)</a>", menu)
        good_links=[]
        for l in links:
            if ('/archivio.html?' in l[0]) and not ('&amp;' in l[0]):
                printDBG("{'title': '%s', 'url' : '%s'}" % (l[1],l[0]))
                good_links.append({'title': l[1], 'url' : l[0]})
        
        good_links.append({'title': 'Altri sport', 'url' : '/archivio.html?tematica=altri-sport'})
        
        # open any single page in list and grab search keys
        
        for l in good_links:
            sts, data = self.getPage(self.RAISPORT_MAIN_URL + l['url'])
            if sts:
                dataDominio= re.findall("data-dominio=\"(.*?)\"", data)
                dataTematica = re.findall("data-tematica=\"(.*?)\"", data)
                if dataTematica:
                    del(dataTematica[0])
                    #printDBG(str(dataDominio))
                    #printDBG(str(dataTematica))
                    title=dataTematica[0].split('|')[0]
                    title = HTMLParser.HTMLParser().unescape(title).encode('utf-8')

                    params={'title': title, 'dominio': dataDominio[0], 'sub_keys' : dataTematica}
                    printDBG(str(params))
                    self.RaiSportKeys.append(params)
                
    def listRaiSportMain(self, cItem):
        printDBG("Raiplay.listRaiSportMain")
        
        if not self.RaiSportKeys:
            self.fillRaiSportKeys()
        
        for k in self.RaiSportKeys:
            params=dict(cItem)
            params.update({'category': 'raisport_item', 'title': k['title'], 'dominio': k['dominio'], 'sub_keys': k['sub_keys']})
            self.addDir(params)
    
    def listRaiSportItems(self, cItem):
        printDBG("Raiplay.listRaiSportItem %s" % cItem['title'])
        dominio = cItem.get('dominio','')
        sub_keys = cItem.get('sub_keys',[])
        
        for k in sub_keys:
            title = k.split("|")[0]
            title = HTMLParser.HTMLParser().unescape(title).encode('utf-8')

            if title == cItem['title']:
                title = "Tutto su " + title
            
            params = {'category': 'raisport_subitem', 'title': title, 'dominio': dominio, 'key': k}
            self.addDir(params)
    
    def listRaiSportVideos(self, cItem):
        printDBG("Raiplay.listRaiSportItem %s" % cItem['title'])
        key= cItem.get('key','')
        dominio = cItem.get('dominio','')
        page = int(cItem.get('page',0))
        
        header = {
                  'Accept': 'application/json, text/javascript, */*; q=0.01' ,
                  'Content-Type': 'application/json; charset=UTF-8',
                  'Origin': 'https://www.raisport.rai.it',
                  'Referer': 'https://www.raisport.rai.it/archivio.html',
                  'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36',
                  'X-Requested-With': 'XMLHttpRequest',
                 }
        pageSize = 50
        
        payload = {
            "page": page,
            "pageSize": pageSize,
            "filters":{
                "tematica":[key],
                "dominio": dominio
            }
        }
        postData=json_dumps(payload)
        
        sts, data = self.getPage(self.RAISPORT_SEARCH_URL, {'header' : header, 'raw_post_data':1}, post_data= postData) 
        
        if sts:
            j = json_loads(data)
            if 'hits' in j:
                h = j['hits']
                printDBG(str(h))
                if 'hits' in h:
                    for hh in h['hits']:
                        if '_source' in hh:
                            news_type = hh['_source']['tipo']
                            if news_type == 'Video' and 'media' in hh['_source']:
                                relinker_url = hh['_source']['media']['mediapolis']
                                
                                if 'durata' in hh['_source']['media']:
                                    duration = " - " + _("Duration") + ": " + hh['_source']['media']['durata']
                                else:
                                    duration = ""
                                    
                                icon = hh['_source']['immagini']['default']
                                title = hh['_source']['titolo']
                                creation_date = hh['_source']['data_creazione']
                                if 'sommario' in hh['_source']: 
                                    desc = creation_date + duration + '\n' + hh['_source']['sommario']
                                else:
                                    desc = creation_date + duration
                                
                                params= {'category':'raisport_video', 'title': title, 'desc': desc, 'url': relinker_url, 'icon': icon}
                                printDBG(str(params))
                                self.addVideo(params)
         
                if h['total'] > (page + pageSize):
                    page += pageSize
                    params=dict(cItem)
                    params['title']=_("Next page")
                    params['page'] = page
                    self.addMore(params)
                
        
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('Raiplay - handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        self.informAboutGeoBlockingIfNeeded('IT')

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        subtype  = self.currItem.get("sub-type",'')
        
        printDBG( "handleService: >> name[%s], category[%s] " % (name, category) )
        self.currList = []
        
        #MAIN MENU
        if name == None:
            self.listMainMenu({'name':'category'})
        elif category == 'live_tv':
            self.listLiveTvChannels(self.currItem)
        elif category == 'live_radio':
            self.listLiveRadioChannels(self.currItem)       
        elif category == 'replay':
            self.listReplayDate(self.currItem)
        elif category == 'replay_date':
            self.listReplayChannels(self.currItem)
        elif category == 'replay_channel':
            self.listEPG(self.currItem)
        elif category == 'ondemand':
            self.listOnDemandMain(self.currItem)
        elif category == 'ondemand_items':
            if subtype == "RaiPlay Tipologia Page" or subtype == "RaiPlay Genere Page" or subtype == "RaiPlay Tipologia Editoriale Page":
                self.listOnDemandCategory(self.currItem)
            elif subtype == "Raiplay Tipologia Item":
                self.listOnDemandAZ(self.currItem)
            elif subtype == "PLR programma Page":
                self.listOnDemandProgram(self.currItem)
            else:
                printDBG("Raiplay - item '%s' - Sub-type not handled '%s' " % (name, subtype))
        elif category == 'ondemand_list':
            self.listOnDemandIndex(self.currItem)
        elif category == 'ondemand_program':
            self.listOnDemandProgramItems(self.currItem)
        elif category == 'tg':
            self.listTg(self.currItem)
        elif category == 'tgr' or category == 'tgr-root':
            self.listTgr(self.currItem)
        elif category in ['tg1','tg2','tg3']:
            self.searchLastTg(self.currItem)
        elif category == 'nop':
            printDBG('raiplay no link')
        elif category == 'raisport_main':
            self.listRaiSportMain(self.currItem)
        elif category == 'raisport_item':
            self.listRaiSportItems(self.currItem)
        elif category == 'raisport_subitem':
            self.listRaiSportVideos(self.currItem)
        else:
            printExc()
        
        CBaseHostClass.endHandleService(self, index, refresh)


class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, Raiplay(), True, [])
    
