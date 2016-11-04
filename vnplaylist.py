#!/usr/bin/python
#coding=utf-8
import httplib2, json, re, urllib, os, uuid
from kodiswift import Plugin, xbmc, xbmcgui, xbmcaddon

plugin         = Plugin()
addon          = xbmcaddon.Addon("plugin.video.kodi4vn.vnplaylist")
pluginrootpath = "plugin://plugin.video.kodi4vn.vnplaylist"
http           = httplib2.Http(".cache", disable_ssl_certificate_validation=True)
query_url      = "https://docs.google.com/spreadsheets/d/1zL6Kw4ZGoNcIuW9TAlHWZrNIJbDU5xHTtz-o8vpoJss/gviz/tq?gid={gid}&headers=1&tq={tq}"
sheet_headers  = {
	"User-Agent"      : "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.3; WOW64; Trident/7.0)",
	"Accept-Encoding" : "gzip, deflate",
}

def getItems(url_path="0"):
	query_url.format(
		tq  = "select Title, GID, Thumbnail, Description",
		gid = url_path
	),
	(resp, content) = http.request(
		query_url.format(
			tq  = urllib.quote_plus("select A, B, C, D"),
			gid = urllib.quote_plus(url_path)
		), "GET",
		headers=sheet_headers
	)
	_re = "google.visualization.Query.setResponse\((.+?)\);"
	_json = json.loads(re.compile(_re).findall(content)[0])

	items = []
	for row in _json["table"]["rows"]:
		item = {}
		item["label"]     = row["c"][0]["v"]
		item["path"]      = row["c"][1]["v"]
		item["thumbnail"] = row["c"][2]["v"]
		item["info"]      = {"plot": row["c"][3]["v"]}
		items += [item]

	return items

@plugin.route('/')
def Home():
	GA()
	Section("0")

@plugin.route('/section/<path>')
def Section(path="0"):
	return plugin.finish(getItems("0"))

def GA(title="Home",page="/"):
	try:
		ga_url    = "http://www.google-analytics.com/collect"
		client_id = open(cid_path).read()
		data      = {
			'v'   : '1',
			'tid' : 'UA-52209804-5',
			'cid' : client_id,
			't'   : 'pageview',
			'dp'  : "VNPlaylist%s" % page,
			'dt'  : "[VNPlaylist] - %s" % title
		}
		http.request(
			ga_url, "POST",
			body=urllib.urlencode(data)
		)
	except:
		pass

device_path = xbmc.translatePath('special://userdata')
if os.path.exists(device_path)==False:
	os.mkdir(device_path)
cid_path = os.path.join(device_path, 'cid')
search_history_path = os.path.join(device_path, 'search.p')

if os.path.exists(cid_path)==False:
	with open(cid_path,"w") as f:
		f.write(str(uuid.uuid1()))

if __name__ == '__main__':
	plugin.run()