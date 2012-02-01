ICON                = "icon-default.png"
ART                 = "art-default.png"

CNN_PLUGIN_PREFIX   = "/video/CNN"
CNN_BASE_URL        = "http://www.cnn.com"
CNN_VIDEO_URL       = "http://www.cnn.com/video/#"
CNN_XML_URL         = "http://www.cnn.com/.element/ssi/www/auto/2.0/video/xml/%s.xml"
CNN_JSON_URL        = "http://www.cnn.com/video/data/2.0/%s"

LIVE_URL        = "cnn://%s"
LIVE_STREAM_BASE_URL = 'http://www.cnn.com/CNNLiveFlash/StreamStatus/metadata/stream_dvr_%s.xml'
LIVE_STREAMS = ['1','2','3','4']

CNN_SECTIONS = [('Top Stories', 'top_stories'),
                ('Most Popular', 'most_popular'),
                ('CNN TV', 'cnn_tv'),
                ('I-Reports', 'by_section_ireports'),
                ('World', 'by_section_world'),
                ('Politics', 'by_section_politics'),
                ('Entertainment', 'by_section_showbiz'),
                ('Justice', 'by_section_crime'),
                ('Tech', 'by_section_tech'),
                ('Living', 'by_section_living'),
                ('Health', 'by_section_health'),
                ('Student News', 'by_section_student'),
                ('Business', 'by_section_business'),
                ('Sports', 'by_section_sports'),
                ('Weather', 'by_section_weather'),
                ('Staff Picks', 'staff_picks')]

####################################################################################################

def Start():
  Plugin.AddPrefixHandler(CNN_PLUGIN_PREFIX, MainMenu, "CNN", ICON, ART)
  Plugin.AddViewGroup("InfoList", viewMode = "InfoList", mediaType = "items")
  Plugin.AddViewGroup("List", viewMode = "List", mediaType = "items")

  ObjectContainer.title1 = "CNN"
  ObjectContainer.art = R(ART)
  ObjectContainer.view_group = 'List'

  DirectoryObject.thumb = R(ICON)
  DirectoryObject.art = R(ART)
  VideoClipObject.thumb = R(ICON)

####################################################################################################
  
def MainMenu():
  oc = ObjectContainer()
  oc.add(DirectoryObject(key = Callback(LiveStreamMenu), title = 'Live News'))

  for (title, video_group) in CNN_SECTIONS:
    oc.add(DirectoryObject(
      key = Callback(VideosMenu, title = title, video_group = video_group), 
      title = title))

  return oc

####################################################################################################

def LiveStreamMenu():  
  oc = ObjectContainer(title2 = "Live Streams", view_group= "InfoList")

  for stream_id in LIVE_STREAMS:

    stream_xml = XML.ElementFromURL(LIVE_STREAM_BASE_URL % stream_id, cacheTime = 0)
    stream = stream_xml.xpath("//streams/stream")[0]
    if stream.get('command') == 'start':

      title = stream.xpath("./title/text()")[0]
      summary = stream.xpath("./description/text()")[0]
          
      oc.add(VideoClipObject(
        url = LIVE_URL % stream_id,
        title = title,
        summary = summary))

  if len(oc) == 0:
    return MessageContainer(
      title1="CNN streams",
      header = "CNN Live Streams", 
      message = "No streams available at present")   

  return oc
      
####################################################################################################

def VideosMenu(title, video_group):
  oc = ObjectContainer(title2 = title)

  video_details = XML.ElementFromURL(CNN_XML_URL % video_group)
  if video_details is None: return oc
  
  for video in video_details.xpath("//video"):

    # Obtain the actual URL and the associated title.
    video_url = CNN_VIDEO_URL + video.xpath("./video_id/text()")[0]
    title = video.xpath(".//tease_txt/text()")[0]

    # Obtain the highest quality video available.
    thumb = None
    thumb_paths = ["splash_image_url", "image_url", "tz_image_url"]
    for path in thumb_paths:
      thumb = video.xpath(".//%s/text()" % path)[0]
      if thumb != None:
        break
    if thumb is None:
      thumb = R(ICON)

    # Determine the duration of the video
    duration = None
    duration_text = video.xpath('.//vid_duration/text()')[0]
    try:
      duration_parts = duration_text.partition(":")
      if duration_parts[0] == "" or duration_parts[0] == " ": mins = 0
      else: mins = int(duration_parts[0])
      duration = ((mins * 60) + int(duration_parts[2])) * 1000
    except: pass

    if title is not None:
      oc.add(VideoClipObject(
        url = video_url,
        title = title,
        thumb = thumb,
        duration = duration))

  return oc