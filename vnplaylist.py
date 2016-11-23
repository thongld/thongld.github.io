#!/usr/bin/python
#coding=utf-8
import urllib,requests,re,json,HTMLParser,os,uuid
from xbmcswift2 import Plugin, xbmc, xbmcgui, xbmcaddon
requests.packages.urllib3.disable_warnings()
plugin         = Plugin()
h              = HTMLParser.HTMLParser()
pluginrootpath = "plugin://plugin.video.kodi4vn.fptplay"

live_url       = "https://fptplay.net/show/getlinklivetv"
token_url      = "https://fptplay.net/tro-giup/bao-loi"
vod_url        = "https://fptplay.net/show/getlink"
items_per_page = 30

headers = {
	"User-Agent"      : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36",
	"Content-Type"    : "application/x-www-form-urlencoded; charset=UTF-8",
	"Accept"          : "application/json, text/javascript, */*; q=0.01",
	"X-Requested-With": "XMLHttpRequest",
	"Referer"         : "https://fptplay.net/livetv",
	"Accept-Encoding" : "gzip, deflate"
}

def cleanHTML(s):
	s = ''.join(s.splitlines()).replace('\'','"')
	s = s.replace('\n','')
	s = s.replace('\t','')
	s = re.sub('  +',' ',s)
	s = s.replace('> <','><')
	return h.unescape(s)

@plugin.route('/eps/<sid>')
def eps(sid):
	GA("Browse eps by id %s" % sid, "/eps/%s" % sid)
	res = requests.get("https://fptplay.net/xem-video/-%s.html" % sid, headers=headers)
	res.encoding = "utf-8"
	s = cleanHTML(res.text).encode("utf8")
	so_tap = 1
	match = re.compile('Số tập\: </span>(\d+) tập</p>').findall(s)
	items = []
	if len(match) > 0:
		so_tap = int(match[0])
	title = re.compile('<title>FPT Play - Xem video (.+?)</title>').findall(s)[0]
	if so_tap == 1:
		item = {}
		item["label"]     = "Xem %s" % title
		item["path"]      = "%s/play/%s/%s" % (pluginrootpath,sid,"1")
		item["is_playable"] = True
		items.append(item)
	else:
		for i in range(1, so_tap + 1):
			item = {}
			item["label"]     = "Xem %s - Tập %s" % (title, i)
			item["path"]      = "%s/play/%s/%s" % (pluginrootpath,sid,i)
			item["is_playable"] = True
			items.append(item)
	return plugin.finish(items)

@plugin.route('/list/<order>/<s_id>/<page>')
def list(order="new",s_id="",page="1"):
	GA("Browse new videos by id %s" % s_id, "/list/%s/%s/%s" % (order,s_id,page))
	sess = requests.Session()
	payload = {
		'type'        : order,
		'stucture_id' : s_id,
		'page'        : page,
		'keyword'     : 'undefined'
	}
	res = sess.post("https://fptplay.net/show/more", headers = headers, data = payload)
	res.encoding = "utf-8"
	s = cleanHTML(res.text).encode("utf8")
	match = re.compile('<a href=".+?-(\w+).html" ><img[^>]*src="(.+?)"[^>]*alt="(.+?)"').findall(s)
	items = []
	for sid, thumb, title in match:
		item = {}
		item["label"]     = title
		item["path"]      = "%s/eps/%s" % (pluginrootpath,sid)
		item["thumbnail"] = thumb
		items.append(item)
	if len(items) == items_per_page:
		item = {}
		item["label"]     = "Next >>"
		item["path"]      = "%s/list/%s/%s/%s" % (pluginrootpath,order,s_id,int(page)+1)
		item["thumbnail"] = "http://icons.iconarchive.com/icons/rafiqul-hassan/blogger/128/Arrow-Next-icon.png"
		items.append(item)
	if plugin.get_setting('thumbview', bool):
		if xbmc.getSkinDir() in ('skin.confluence','skin.eminence'):
			return plugin.finish(items, view_mode = 500)
		elif xbmc.getSkinDir() == 'skin.xeebo':
			return plugin.finish(items, view_mode = 52)
		else:
			return plugin.finish(items)
	else:
		return plugin.finish(items)

@plugin.route('/live')
def live():
	GA("Browse Live Channels", "/live")
	url = "https://fptplay.net/livetv"
	res          = requests.get(url, headers=headers)
	res.encoding = "utf-8"
	s            = cleanHTML(res.text)
	match        = re.compile('onclick="getLivetv\(\$\(this\)\)" data-href="(.+?)"[^>]*>(.*?)<img class="lazy" data-original="(.+?)"[^>]*title="(.+?)"').findall(s)
	items = []
	for live_url, locked, thumb, title in match:
		if "livetv_lock" not in locked:
			item = {}
			item["label"]       = title
			item["path"]        = "%s/play/%s" % (pluginrootpath,urllib.quote_plus(live_url.encode("utf8")))
			item["is_playable"] = True
			item["thumbnail"]   = thumb
			items.append(item)
	if plugin.get_setting('thumbview', bool):
		if xbmc.getSkinDir() in ('skin.confluence','skin.eminence'):
			return plugin.finish(items, view_mode = 500)
		elif xbmc.getSkinDir() == 'skin.xeebo':
			return plugin.finish(items, view_mode = 52)
		else:
			return plugin.finish(items)
	else:
		return plugin.finish(items)

@plugin.route('/play/<url>', name="play_firsteps")
@plugin.route('/play/<url>/<eps>')
def play(url,eps="1"):
	GA("Play %s" % url, "/play/%s/%s" % (url,eps))
	# sess = requests.Session()
	# payload = {
	# 	"country_code" : plugin.get_setting('code'),
	# 	"phone"        : plugin.get_setting('phone'),
	# 	"password"     : plugin.get_setting('password'),
	# 	"submit"       : ""
	# }
	# res = sess.post("https://fptplay.net/user/login", headers = headers, data = payload)

	dialogWait = xbmcgui.DialogProgress()
	dialogWait.create('FPTPlay.net', 'Loading video. Please wait...')
	tail = "|User-Agent=Mozilla%2F5.0%20%28Windows%20NT%2010.0%3B%20Win64%3B%20x64%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F53.0.2785.143%20Safari%2F537.36&Referer=https%3A%2F%2Ffptplay.net%2Flivetv%2F"
	plugin.set_resolved_url(get_playable_url(url,eps) + tail, subtitles="https://docs.google.com/spreadsheets/d/16l-nMNyOvrtu4FKLm-ctGDNClCjI09XKp3lcOKPOXMk/export?format=tsv&gid=0")
	dialogWait.close()
	del dialogWait

def get_playable_url(url,ep_id="1"):
	sess = requests.Session()
	if "/livetv" in url or "/event" in url:
		res = sess.get(url,headers=headers)
		res.encoding = "utf-8"
		s     = cleanHTML(res.text).encode("utf8")
		v_id  = re.compile('showAlert\("(.+?)"').findall(s)[0]
		x_key = re.compile('"X-KEY", ?"(.+?)"').findall(s)[0]
		headers["X-Key"] = x_key
		payload = {
			'id'      : v_id,
			'type'    : 'newchannel',
			'quality' : '3',
			'mobile'  : 'web'
		}
		j = sess.post(live_url,headers=headers,data=payload).json()
		return j["stream"]
	else:
		res = sess.get(
			"https://fptplay.net/xem-video/-%s.html" % url,
			headers = headers)
		res.encoding = "utf-8"
		s     = cleanHTML(res.text).encode("utf8")
		x_key = re.compile('"X-KEY", ?"(.+?)"').findall(s)[0]
		headers["X-Key"] = x_key
		payload = {
			'id'      : url,
			'type'    : 'newchannel',
			'quality' : '3',
			'mobile'  : 'web',
			'episode' : ep_id
		}
		return sess.post(vod_url,headers=headers,data=payload).json()["stream"]

def GA(title="Home",page="/"):
	ga_url    = "http://www.google-analytics.com/collect"
	client_id = open(cid_path).read()
	data      = {
		'v'   : '1',
		'tid' : 'UA-52209804-5',
		'cid' : client_id,
		't'   : 'pageview',
		'dp'  : "FPTPlay" + page,
		'dt'  : title
	}
	requests.post(ga_url,data=urllib.urlencode(data))

device_path = xbmc.translatePath('special://userdata')
if os.path.exists(device_path)==False:
	os.mkdir(device_path)
cid_path = os.path.join(device_path, 'cid')

if os.path.exists(cid_path)==False:
	with open(cid_path,"w") as txtfile:
		txtfile.write(str(uuid.uuid1()))

if __name__ == '__main__':
	plugin.run()
