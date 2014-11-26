#!/usr/bin/python

import urllib2
import bleach
from bs4 import BeautifulSoup
import gdata.youtube
import gdata.youtube.service
import time

def __init__(videoid):
  
    yt_service = gdata.youtube.service.YouTubeService()
    yt_service.ssl = True
    yt_service.developer_key = 'AIzaSyBwWvdRZ-M5X51aizixHYk00_tu71f70WY'
    entry = yt_service.GetYouTubeVideoEntry(video_id = videoid)

    # Transcipt hack
    url = 'http://www.serpsite.com/transcript.php?videoid=http://www.youtube.com/watch?v=' + videoid
  
    for i in range(20):
        try:
            html = urllib2.urlopen(url)
            soup = BeautifulSoup(html.read())
    
            srt = soup.find_all('textarea')[1]
            cleanSrt = bleach.clean(srt, tags=[], strip=True)
            decodedString = cleanSrt.decode("utf-8").replace("&gt;", ">").encode("utf-8")
    
            try:
                print decodedString.encode('UTF-8')
            
            except Exception:
                print 'Failed'
            
            break # if successfull do not try again
    
        except IndexError:
            print "Can't find transcription."
            break
        except Exception:
            time.sleep(3)



if __name__ == "__main__":
    import sys
    videoid = sys.argv[1]

    if "?v=" in videoid: # handle full youtube link
        videoid = videoid.split("?v=")[1]
        videoid = videoid.split("&")[0]
        
    __init__(videoid)
