import PMS
from PMS import Plugin, Log, DB, Thread, XML, HTTP, JSON, Utils
from PMS.MediaXML import MediaContainer, DirectoryItem, WebVideoItem, VideoItem, SearchDirectoryItem, MessageContainer
from PMS.Shorthand import _L, _R

CNN_PLUGIN_PREFIX   = "/video/CNN"
CNN_VIDEO_URL       = "http://www.cnn.com/video/"
CNN_FLV_URL 		= "http://ht.cdn.turner.com/cnn/big/%s_youtube_640x360.flv"
CNN_XML_URL         = "http://www.cnn.com/.element/ssi/www/auto/2.0/video/xml/%s.xml"
CNN_JSON_URL        = "http://www.cnn.com/video/data/2.0/%s"
CNN_SEARCH_URL      = "http://search.cnn.com/search?type=video&query=%s&currentPage=%s"
CNN_THUMB_PATH      = "/video/CNN/thumbs/i2.cdn.turner.com/cnn/video/%s.576x324.jpg"
LIVE_STREAM_BASE_URL = 'http://www.cnn.com/CNNLiveFlash/StreamStatus/metadata/stream_dvr_%s.xml'
LIVE_STREAMS = ['1','2','3','4']
items = ()

XPATH_SECTIONS      = '//div[@id="By_Section_Nav"]/div/a'

####################################################################################################

def Start():
  Plugin.AddRequestHandler(CNN_PLUGIN_PREFIX, HandleVideoRequest, "CNN", "icon-default.png", "art-default.png")
  Plugin.AddViewGroup("InfoList", viewMode="InfoList", contentType="items")

####################################################################################################
  
def CreateTables():
  # video_key, title, summary, date, length
  DB.Exec('CREATE TABLE videos ("video_key" varchar(255) DEFAULT NULL, "title" varchar(255) DEFAULT NULL, "summary" varchar(255) DEFAULT NULL, "date" varchar(255) DEFAULT NULL, "length" integer DEFAULT NULL)')
  
####################################################################################################

def HandleVideoRequest(pathNouns, count):
  if count == 0:
    # TODO: Proper thumbnails for directories
    dir = MediaContainer('art-default.png', title1="CNN")
    dir.AppendItem(DirectoryItem("live", "Live News", Plugin.ExposedResourcePath("icon-default.png")))
    dir.AppendItem(DirectoryItem("top", "Top Stories", Plugin.ExposedResourcePath("icon-default.png")))
    dir.AppendItem(DirectoryItem("popular", "Most Popular", Plugin.ExposedResourcePath("icon-default.png")))
    dir.AppendItem(DirectoryItem("picks", "Staff Picks", Plugin.ExposedResourcePath("icon-default.png")))
    dir.AppendItem(DirectoryItem("tv", "CNN TV", Plugin.ExposedResourcePath("icon-default.png")))
    dir.AppendItem(DirectoryItem("ireports", "I-Reports", Plugin.ExposedResourcePath("icon-default.png")))
    dir.AppendItem(DirectoryItem("sections", "By Section", Plugin.ExposedResourcePath("icon-default.png")))
    dir.AppendItem(SearchDirectoryItem("%s/search/1" % CNN_PLUGIN_PREFIX, "Search CNN", "CNN Video Search", Plugin.ExposedResourcePath("search.png")))
    return dir.ToXML()
      
  elif pathNouns[0] == "top" and count == 1: return ContainerFromURL(_L(pathNouns[0]), CNN_XML_URL % "top_stories")
  elif pathNouns[0] == "popular" and count == 1: return ContainerFromURL(_L(pathNouns[0]), CNN_XML_URL % "most_popular")
  elif pathNouns[0] == "picks" and count == 1: return ContainerFromURL(_L(pathNouns[0]), CNN_XML_URL % "staff_picks")
  elif pathNouns[0] == "tv" and count == 1: return ContainerFromURL(_L(pathNouns[0]), CNN_XML_URL % "cnn_tv")
  #elif pathNouns[0] == "live" and count == 1: return ContainerFromURL(_L(pathNouns[0]), CNN_XML_URL % "pipeline")
  elif pathNouns[0] == "ireports" and count == 1: return ContainerFromURL(_L(pathNouns[0]), CNN_XML_URL % "by_section_ireports")
      
  elif pathNouns[0] == "sections":
    if count == 1:
      dir = MediaContainer('art-default.png', None, 'CNN', 'By Section')
      sections = XML.ElementFromURL(CNN_VIDEO_URL, True).xpath(XPATH_SECTIONS)
      for section in sections:
        # TODO: Proper thumbnails for directories
        hrefNouns = section.get("href").split("/")
        key = hrefNouns[len(hrefNouns)-1].partition(".xml")[0].replace("by_section_", "")
        name = section.find("b").text
        dir.AppendItem(DirectoryItem(key, name, ""))
      return dir.ToXML()
      
    elif count == 2: return ContainerFromURL(pathNouns[1], CNN_XML_URL % ("by_section_" + pathNouns[1]))
    
  elif pathNouns[0] == "thumbs":
    pathNouns.pop(0)
    thumb_url = HTTP.BuildURL("http://", pathNouns)
    Plugin.Response["Content-Type"] = "image/jpeg"
    return HTTP.Get(thumb_url)
    
  elif pathNouns[0] == "search":
    if count > 2:
      search = pathNouns[2]
      resultPage = pathNouns[1]
      pathNouns.pop(0)
      pathNouns.pop(0)
      query = Utils.BuildPath(pathNouns)
      if query is None: return None
      url = CNN_SEARCH_URL % (HTTP.Quote(query), resultPage)
      page = XML.ElementFromURL(url, True)
      if page is None: return None
        
      dir = MediaContainer('art-default.png', title1="Search", title2=search)
      results = page.xpath("//div[@class='cnnSearchResultsContent']")
      for result in results:
        # Get key
        key = result.xpath(".//a/@href")[0][33:-17].strip()
        # Get title & summary
        titleParts = result.xpath(".//a")[1].itertext()
        title = ""
        for t in titleParts: title += t
        summaryParts = result.xpath(".//div[@id='cnnSearchResultsDescriptionPhoto']")[0].itertext()
        summary = ""
        for s in summaryParts: summary += s
        # Try to calculate the video duration as milliseconds
        vid_duration = result.xpath(".//span[@class='cnnVideoRunningTime']/text()")[0]
        duration = ""
        try:
          duration_parts = vid_duration.partition(":")
          if duration_parts[0] == "" or duration_parts[0] == " ": mins = 0
          else: mins = int(duration_parts[0])
          duration = str(((mins * 60) + int(duration_parts[2])) * 1000)
        except: pass
        dir.AppendItem(VideoItem(CNN_FLV_URL % key, title, summary, duration, CNN_THUMB_PATH % key))
      
      # If there's an active "Next" link, add a "More Results" item to the list
      try:
        next = page.xpath("//a[text()='Next ']")[0]
        if next.get("href") != "#":
          more = DirectoryItem("%s/search/%d/%s" % (CNN_PLUGIN_PREFIX, int(resultPage)+1, query), "More Results...", "")
          dir.AppendItem(more)
      except: pass
      return dir.ToXML()

####################################################################################################
  elif pathNouns[0] == "live":
    dir = MediaContainer('art-default.png', title1="CNN", title2="Live Streams", viewGroup="InfoList" )
    foundLiveStream = False
    for streamID in LIVE_STREAMS:
      Log.Add("URL is " + (LIVE_STREAM_BASE_URL % streamID))
      streamXML = XML.ElementFromString(HTTP.GetCached(LIVE_STREAM_BASE_URL % streamID, cacheTime=0))

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
        Log.Add("Stream URL is " + streamUrl)
        index = streamUrl.find('cnn_stream')
        player = streamUrl[0:index-1]
        clip = streamUrl[index:]
        vidUrl = "http://www.plexapp.com/player/player.php?url=%s&clip=%s&live=true" % (player, clip)
        vidItem = WebVideoItem(vidUrl, title, summary, '', '')
        dir.AppendItem(vidItem)
        
        #dir.AppendItem(WebVideoItem('http://www.cnn.com/video/flashLive/live.html?stream=' + streamID, title, summary, '', ''))
        #vidItem.SetAttr('subtitle', live)
        #dir.AppendItem(vidItem)
    if foundLiveStream:
      return dir.ToXML()
    else:
      # Return a Message Container
      return (MessageContainer(header="CNN Live Streams", message="No streams available at present", title1="CNN streams")).ToXML()


####################################################################################################

def ContainerFromURL(title, url):
  # Create a new MediaContainer
  dir = MediaContainer('art-default.png', title1="CNN", title2=title)
  
  # Fetch the video content list from CNN
  video_content = XML.ElementFromURL(url)
  if video_content is None: return None
  
  # Add each content item to the MediaContainer
  for video in video_content:
    video_id = XML.TextFromElement(video.find("video_id"))
    if url.count("pipeline.xml") == 1: key = XML.TextFromElement(video.find("video_url"))
    else: key = video_id[7:]
    
    # Look up the correct URL for "Now in the News" bulletins
    if video_id == "/nitn/latest/nitn":
      nitn = JSON.DictFromURL(CNN_JSON_URL % XML.TextFromElement(video.find("video_url")), "Latin-1")
      key = nitn["location"].lstrip("/")
    
    title = XML.TextFromElement(video.find("tease_txt"))
    
    # Try to calculate the video duration as milliseconds
    vid_duration = XML.TextFromElement(video.find("vid_duration"))
    duration = ""
    try:
      duration_parts = vid_duration.partition(":")
      if duration_parts[0] == "" or duration_parts[0] == " ": mins = 0
      else: mins = int(duration_parts[0])
      duration = str(((mins * 60) + int(duration_parts[2])) * 1000)
    except: pass
    
    summary = ""  # TODO: Add caching for summaries
    Log.Add("URL is " + (CNN_FLV_URL % key))
    item = VideoItem(CNN_FLV_URL % key, title, summary, duration, None)
    item.SetAttr("year", str(Utils.Today().year))
    
    # Get the highest quality thumbnail available
    thumb = XML.TextFromElement(video.find("splash_image_url"))
    if thumb is None:
      thumb = XML.TextFromElement(video.find("image_url"))
      if thumb is None:
        thumb = XML.TextFromElement(video.find("tz_image_url"))
    
    if thumb is not None:
      item.SetAttr("thumb", CNN_PLUGIN_PREFIX + "/thumbs/" + thumb.lstrip("http://"))
    
    # Don't add untitled items (indicating inactive streams)
    if title is not None:
      dir.AppendItem(item)

  return dir.ToXML()

####################################################################################################

def Update():
  # TODO: Expand this method to support proper caching of metadata
  
  # Iterate through each section to get video lists
  sections = XML.ElementFromURL(CNN_VIDEO_URL, True).xpath(XPATH_SECTIONS)
  for section in sections:
    hrefNouns = section.get("href").split("/")
    section_xml = CNN_XML_URL % hrefNouns[len(hrefNouns)-1].partition(".xml")[0]
    section_name = section.find("b").text
    
    # Iterate through each video item in the section
    videos = XML.ElementFromURL(section_xml)
    for video in videos:
    
      # Get the video metadata
      metadata = JSON.DictFromString(HTTP.Get(CNN_JSON_URL % video.find("video_url").text), "Latin-1")
      
####################################################################################################
