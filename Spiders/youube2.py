#!/usr/bin/python

import urllib2
import bleach
from bs4 import BeautifulSoup
import gdata.youtube
import gdata.youtube.service


def __init__(videoid):
  
  # GOOGLE STUFF NOT NECESSARY
  yt_service = gdata.youtube.service.YouTubeService()
  yt_service.ssl = True
  yt_service.developer_key = 'AIzaSyBwWvdRZ-M5X51aizixHYk00_tu71f70WY'
  entry = yt_service.GetYouTubeVideoEntry(video_id = videoid)
  PrintEntryDetails(entry)

  # Transcipt hack
  url = 'http://www.serpsite.com/transcript.php?videoid=http://www.youtube.com/watch?v=' + videoid
  
  try:
    # parse = urllib.urlopen(cc_url).read()
    # print "parse = " + parse
    html = urllib2.urlopen(url)
    soup = BeautifulSoup(html.read())

    srt = soup.find_all('textarea')[1]
    cleanSrt = bleach.clean(srt, tags=[], strip=True)
    decodedString = cleanSrt.decode("utf-8").replace("&gt;", ">").encode("utf-8")
    
    # print cleanSrt
    # print "type is : "
    # print type(cleanSrt)

    try:
      f = open(entry.media.title.text + '-' + videoid + '.srt', 'w') #format the same as youtube-dl formats .mp4 file
      f.write(decodedString.encode('UTF-8'))
      f.close()
      print '...made srt file!!!'
    
    except:
      print '...file NOT saved'

  except:
    print "Problem loading in URL"


def PrintEntryDetails(entry):
  print '-- Video title: %s' % entry.media.title.text
  print '-- Video description: %s' % entry.media.description.text
  print '-- Video watch page: %s' % entry.media.player.url
  print '-- Video duration: %f' % (float(entry.media.duration.seconds) / 60) + ' minutes'

  # show alternate formats
  for alternate_format in entry.media.content:
      if 'isDefault' not in alternate_format.extension_attributes:
          print '-- Alternate format: %s | url: %s ' % (alternate_format.type, alternate_format.url)

  # show thumbnails
  for thumbnail in entry.media.thumbnail:
      print '-- Thumbnail url: %s' % thumbnail.url


if __name__ == "__main__":
    import sys
    videoid = "oswUssXzFlY"
    print "-- Video ID = " + videoid
    __init__(videoid)
