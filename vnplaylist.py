import httplib2, json, re, urllib
from kodiswift import Plugin, xbmc, xbmcgui, xbmcaddon
plugin        = Plugin()
http          = httplib2.Http(".cache")
query_url     = "https://docs.google.com/spreadsheets/d/1zL6Kw4ZGoNcIuW9TAlHWZrNIJbDU5xHTtz-o8vpoJss/gviz/tq?gid={gid}&headers=1&tq={tq}"
sheet_headers = {
	"User-Agent"      : "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.3; WOW64; Trident/7.0)",
	"Accept-Encoding" : "gzip, deflate",
}

@plugin.route('/')
def Home():
	Section("0")

@plugin.route('/section/<path>')
def Section(path="0"):
	return getItems("0")

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
