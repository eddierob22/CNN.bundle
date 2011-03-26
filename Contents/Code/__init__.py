
CNN_PLUGIN_PREFIX   = "/video/CNN"
CNN_VIDEO_URL       = "http://www.cnn.com/video/"
CNN_FLV_URL 	    = "http://ht.cdn.turner.com/cnn/big/%s_youtube_640x360.flv"
CNN_XML_URL         = "http://www.cnn.com/.element/ssi/www/auto/2.0/video/xml/%s.xml"
CNN_JSON_URL        = "http://www.cnn.com/video/data/2.0/%s"
CNN_SEARCH_URL      = "http://www.cnn.com/search/?query=%s&primaryType=video&sortBy=date&intl=false"
CNN_THUMB_PATH      = "/video/CNN/thumbs/i2.cdn.turner.com/cnn/video/%s.576x324.jpg"
LIVE_STREAM_BASE_URL = 'http://www.cnn.com/CNNLiveFlash/StreamStatus/metadata/stream_dvr_%s.xml'
LIVE_STREAMS = ['1','2','3','4']
items = ()

XPATH_SECTIONS      = '//div[@id="By_Section_Nav"]/div/a'

ICON                = "icon-default.png"
ART                 = "art-default.png"

####################################################################################################

def Start():
  Plugin.AddPrefixHandler(CNN_PLUGIN_PREFIX, MainMenu, "CNN", ICON, ART)
  Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
  Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
  
  MediaContainer.title1 = "CNN"
  MediaContainer.art = R(ART)
  MediaContainer.thumb = R(ICON)

####################################################################################################
  
def MainMenu():
  dir = MediaContainer(viewGroup = "List")
  dir.Append(Function(DirectoryItem(LiveStreamMenu, "Live News", thumb=R(ICON), art=R(ART))))
  dir.Append(Function(DirectoryItem(VideosMenu, "Top Stories", thumb=R(ICON), art=R(ART)), videoGroup="top_stories"))
  dir.Append(Function(DirectoryItem(VideosMenu, "Most Popular", thumb=R(ICON), art=R(ART)), videoGroup="most_popular"))
  dir.Append(Function(DirectoryItem(VideosMenu, "CNN TV", thumb=R(ICON), art=R(ART)), videoGroup= "cnn_tv"))
  dir.Append(Function(DirectoryItem(VideosMenu, "I-Reports", thumb=R(ICON), art=R(ART)), videoGroup= "by_section_ireports"))
  dir.Append(Function(DirectoryItem(VideosMenu, "World", thumb=R(ICON), art=R(ART)), videoGroup="by_section_world"))
  dir.Append(Function(DirectoryItem(VideosMenu, "Politics", thumb=R(ICON), art=R(ART)), videoGroup="by_section_politics"))
  dir.Append(Function(DirectoryItem(VideosMenu, "Entertainment", thumb=R(ICON), art=R(ART)), videoGroup="by_section_showbiz"))
  dir.Append(Function(DirectoryItem(VideosMenu, "Justice", thumb=R(ICON), art=R(ART)), videoGroup="by_section_crime"))
  #dir.Append(Function(DirectoryItem(VideosMenu, "Offbeat", thumb=R(ICON), art=R(ART)), videoGroup="by_section_offbeat"))
  dir.Append(Function(DirectoryItem(VideosMenu, "Tech", thumb=R(ICON), art=R(ART)), videoGroup="by_section_tech"))
  dir.Append(Function(DirectoryItem(VideosMenu, "Living", thumb=R(ICON), art=R(ART)), videoGroup="by_section_living"))
  dir.Append(Function(DirectoryItem(VideosMenu, "Health", thumb=R(ICON), art=R(ART)), videoGroup="by_section_health"))
  dir.Append(Function(DirectoryItem(VideosMenu, "Student News", thumb=R(ICON), art=R(ART)), videoGroup="by_section_student"))
  dir.Append(Function(DirectoryItem(VideosMenu, "Business", thumb=R(ICON), art=R(ART)), videoGroup="by_section_business"))
  dir.Append(Function(DirectoryItem(VideosMenu, "Sports", thumb=R(ICON), art=R(ART)), videoGroup="by_section_sports"))
  dir.Append(Function(DirectoryItem(VideosMenu, "Weather", thumb=R(ICON), art=R(ART)), videoGroup="by_section_weather"))
  dir.Append(Function(DirectoryItem(VideosMenu, "Staff Picks", thumb=R(ICON), art=R(ART)), videoGroup= "staff_picks"))
  #dir.Append(Function(DirectoryItem(SectionsMenu, "By Section", thumb=R(ICON), art=R(ART))))
  #dir.Append(Function(InputDirectoryItem(Search, "Search CNN", "CNN Video Search", thumb=R("search.png"), art=R(ART))))
  return dir

####################################################################################################

def LiveStreamMenu(sender):  
  dir = MediaContainer(title2="Live Streams", viewGroup="InfoList" )
  foundLiveStream = False
  for streamID in LIVE_STREAMS:
    Log("URL is " + (LIVE_STREAM_BASE_URL % streamID))
    streamXML = XML.ElementFromURL(LIVE_STREAM_BASE_URL % streamID, cacheTime=0)

    # Get first element
    stream = streamXML.xpath("//streams/stream")[0]

    # See if it is live
    if stream.get('command') == 'start':
      foundLiveStream = True
      # Stream is live make a WebVideoItem
      title = stream.xpath("./title/text()")[0]
      summary = stream.xpath("./description/text()")[0]
      live = ""
      if stream.get('isLive') == 'true':
        live = "Live"    
      # etc for other meta data
      asxUrl = "http://www.cnn.com/video/live/cnnlive_%s_flash.xml" % streamID
      streamUrl =  XML.ElementFromURL(asxUrl).xpath('/asx/entry/ref')[1].get('href')
      Log("Stream URL is " + streamUrl)
      index = streamUrl.find('cnn_stream')
      player = streamUrl[0:index-1]
      clip = streamUrl[index:]
      #vidUrl = "http://www.plexapp.com/player/player.php?url=%s&clip=%s&live=true" % (player, clip)
      dir.Append(RTMPVideoItem(url=player, clip=clip, live=True, title=title, summary=summary, thumb=R(ICON), art=R(ART)))

  if foundLiveStream:
    return dir
  else:
    return MessageContainer(header="CNN Live Streams", message="No streams available at present", title1="CNN streams")
      
####################################################################################################

def VideosMenu(sender, videoGroup=''):
  dir = MediaContainer(title2=sender.itemTitle, viewGroup='List')
  
  # Fetch the video content list from CNN
  url = CNN_XML_URL % videoGroup
  video_content = XML.ElementFromURL(url)
  if video_content is None: return None
  
  # Add each content item to the MediaContainer
  for video in video_content:
    video_id = video.xpath('.//video_id')[0].text #XML.TextFromElement(video.find("video_id"))
    if url.count("pipeline.xml") == 1: key = video.xpath('.//video_url')[0].text #XML.TextFromElement(video.find("video_url"))
    else: key = video_id[7:]
    
    # Look up the correct URL for "Now in the News" bulletins
    if video_id == "/nitn/latest/nitn":
      nitn = JSON.DictFromURL(CNN_JSON_URL % video.xpath('.//video_url')[0].text, "Latin-1")
      key = nitn["location"].lstrip("/")
    
    title = video.xpath('.//tease_txt')[0].text #XML.TextFromElement(video.find("tease_txt"))
    
    # Try to calculate the video duration as milliseconds
    vid_duration = video.xpath('.//vid_duration')[0].text #XML.TextFromElement(video.find("vid_duration"))
    duration = ""
    try:
      duration_parts = vid_duration.partition(":")
      if duration_parts[0] == "" or duration_parts[0] == " ": mins = 0
      else: mins = int(duration_parts[0])
      duration = str(((mins * 60) + int(duration_parts[2])) * 1000)
    except: pass
    
    summary = ""  # TODO: Add caching for summaries
    Log("URL is " + (CNN_FLV_URL % key))
    #item = VideoItem(CNN_FLV_URL % key, title, summary, duration, None)
    #item.SetAttr("year", str(Utils.Today().year))
    
  # Get the highest quality thumbnail available
    thumb = video.xpath(".//splash_image_url")[0].text
    if thumb is None:
      thumb = video.xpath(".//image_url")[0].text
      if thumb is None:
        thumb = video.xpath(".//tz_image_url")[0].text
      
    if thumb is None:
      thumb = R(ICON)   
    
    # Don't add untitled items (indicating inactive streams)
    if title is not None:
      #dir.Append(item)
      dir.Append(VideoItem(CNN_FLV_URL % key, title=title, summary=summary, duration=duration, thumb=thumb, art=R(ART)))

  return dir

####################################################################################################

def Search(sender, query):
  dir = MediaContainer(title2='Search Results')
  return
  
####################################################################################################

def SectionsMenu(sender):
  '''currently not implemented'''
  dir = MediaContainer(title2='By Section')
  #sections = HTML.ElementFromURL(CNN_VIDEO_URL).xpath(XPATH_SECTIONS)
  for section in HTML.ElementFromURL(CNN_VIDEO_URL).xpath('//div[@id="By_Section_Nav"]/div/a'):
  # TODO: Proper thumbnails for directories
    hrefNouns = section.get("href").split("/")
    key = hrefNouns[len(hrefNouns)-1].partition(".xml")[0].replace("by_section_", "")
    name = section.find("b").text
    dir.Append(Function(DirectoryItem(VideosMenu, title=name, thumb=R(ICON),art=R(ART)), videoGroup='by_section_'+name))
  return dir