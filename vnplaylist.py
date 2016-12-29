#!/usr/bin/python
#coding=utf-8
import httplib2, json, re, urllib, os, uuid, contextlib, zipfile,random
# Tham khảo xbmcswift2 framework cho kodi addon tại
# http://xbmcswift2.readthedocs.io/en/latest/
from xbmcswift2 import Plugin, xbmc, xbmcaddon, xbmcgui, actions
path          = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path') ).decode("utf-8")
cache         = xbmc.translatePath(os.path.join(path,".cache"))
tmp           = xbmc.translatePath('special://temp')
addons_folder = xbmc.translatePath('special://home/addons')
image         = xbmc.translatePath(os.path.join(path, "icon.png"))

plugin         = Plugin()
addon          = xbmcaddon.Addon("plugin.video.thongld.vnplaylist")
pluginrootpath = "plugin://plugin.video.thongld.vnplaylist"
http           = httplib2.Http(cache, disable_ssl_certificate_validation=True)
query_url      = "https://docs.google.com/spreadsheets/d/{sid}/gviz/tq?gid={gid}&headers=1&tq={tq}"
sheet_headers  = {
	"User-Agent"      : "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.3; WOW64; Trident/7.0)",
	"Accept-Encoding" : "gzip, deflate, sdch, br"
}

def GetSheetIDFromSettings():
	'''
	Hàm lấy url chuyển tiếp
	Parameters
	----------
	url_path : string
		link chứa nội dung m3u playlist
	'''
	sid = "1zL6Kw4ZGoNcIuW9TAlHWZrNIJbDU5xHTtz-o8vpoJss"
	resp, content = http.request(plugin.get_setting("GSheetURL"),"HEAD")
	try:
		sid = re.compile("/d/(.+?)/").findall(resp["content-location"])[0]
	except: pass
	return sid

def M3UToItems(url_path=""):
	'''
	Hàm chuyển đổi m3u playlist sang xbmcswift2 items
	Parameters
	----------
	url_path : string
		link chứa nội dung m3u playlist
	'''
	item_re = '\#EXTINF(.*?,)(.*?)\n(.*?)\n'
	(resp, content) = http.request(
		url_path, "GET",
		headers=sheet_headers
	)
	items = []
	matchs = re.compile(item_re).findall(content)
	for info,label,path in matchs:
		thumb = ""
		label2 = ""
		if "tvg-logo" in info:
			thumb = re.compile('tvg-logo=\"?(.*?)\"?,').findall(info)[0]
		if "group-title" in info:
			label2 = re.compile('group-title="(.*?)"').findall(info)[0]
		if label2 != "": label2 = "[%s] " % label2.strip()
		label = "%s%s" % (label2, label.strip())
		item  = {
			"label"      : label,
			"thumbnail"  : thumb.strip(),
			"path"       : path.strip(),
		}
		
		# Nếu là playable link
		if "://" in item["path"]:
			# Kiểu link plugin://
			if item["path"].startswith("plugin://"):
				item["is_playable"] = True
			# Kiểu link .ts
			elif ".ts" in item["path"]: 
				item["path"] = "plugin://plugin.video.f4mTester/?url=%s&streamtype=TSDOWNLOADER&use_proxy_for_chunks=True&name=%s" % (
					urllib.quote(item["path"]),
					urllib.quote_plus(item["label"])
				)
				item["path"] = pluginrootpath + "/executebuiltin/" + urllib.quote_plus(item["path"])
			# Kiểu direct link
			else:
				item["path"] = pluginrootpath + "/play/%s" % urllib.quote_plus(item["path"])
				item["is_playable"] = True
		else:
			# Nếu không phải...
			item["is_playable"] = False

		# Hack xbmcswift2 item to set both is_playable and is_folder to False
		# Required for f4mTester
		if "f4mTester" in item["path"]: item["is_playable"] = False
		items += [item]
	return items

@plugin.cached(TTL = 525600)
def getCachedItems(url_path="0"):
	return AddTracking(getItems(url_path))

def getItems(url_path="0"):
	'''
	Tạo items theo chuẩn xbmcswift2 từ Google Spreadsheet
	Parameters
	----------
	url_path : string
		Nếu truyền "gid" của Repositories sheet:
			Cài tự động toàn bộ repo trong Repositories sheet
		Nếu truyền link download zip repo
			Download và cài zip repo đó
	tracking_string : string
		 Tên dễ đọc của view
	'''
	# Default VN Open Playlist Sheet ID

	sheet_id = GetSheetIDFromSettings()
	gid     = url_path
	if "@" in url_path:
		path_split = url_path.split("@")
		gid = path_split[0]
		sheet_id = path_split[1]
	url = query_url.format(
		sid = sheet_id,
		tq  = urllib.quote("select A,B,C,D,E"),
		gid = gid
	)
	(resp, content) = http.request(
		url, "GET",
		headers=sheet_headers
	)
	_re = "google.visualization.Query.setResponse\((.+?)\);"
	_json = json.loads(re.compile(_re).findall(content)[0])

	items = []
	for row in _json["table"]["rows"]:
		item = {}
		item["label"]     = getValue(row["c"][0]).encode("utf-8")
		item["label2"]    = getValue(row["c"][4])
		# Nếu phát hiện spreadsheet khác với VNOpenPlaylist
		new_path = getValue(row["c"][1])
		if "@" in url_path and "@" not in new_path and "section/" in new_path:
			gid = re.compile("section/(\d+)").findall(new_path)[0]
			new_path = re.sub(
				'section/\d+',
				'section/%s@%s' % (gid,sheet_id),
				new_path,
				flags=re.IGNORECASE
			)
		item["path"]      = new_path

		item["thumbnail"] = getValue(row["c"][2])
		item["info"]      = {"plot": getValue(row["c"][3])}
		if "plugin://" in item["path"]:
			if "install-repo" in item["path"]:
				item["is_playable"] = False
			elif item["path"].startswith("plugin://plugin.video.f4mTester"):
				item["is_playable"] = False
				item["path"] = pluginrootpath + "/executebuiltin/" + urllib.quote_plus(item["path"])
			elif "/play/" in item["path"]:
				item["is_playable"] = True
		elif item["path"] == "":
			item["label"] = "[I]%s[/I]" % item["label"]
			item["is_playable"] = False
			item["path"] = pluginrootpath + "/executebuiltin/-"
		else:
			if "spreadsheets/d/" in item["path"]:
				# https://docs.google.com/spreadsheets/d/1zL6Kw4ZGoNcIuW9TAlHWZrNIJbDU5xHTtz-o8vpoJss/edit#gid=0
				match = re.compile('&cache=(.+?)($|&)').findall(item["path"])
				sheet_id = re.compile("/d/(.+?)/").findall(item["path"])[0]
				try:
					gid = re.compile("gid=(\d+)").findall(item["path"])[0]
				except:
					gid = "0"
				item["path"] = pluginrootpath + "/section/%s@%s" % (gid,sheet_id)
				if match:
					cache_version = match[0][0]
					item["path"] = pluginrootpath + "/cached-section/%s@%s@%s" % (gid,sheet_id,cache_version)
			elif any(service in item["path"] for service in ["fshare.vn/folder"]):
				item["path"] = pluginrootpath + "/fshare/" + urllib.quote_plus(item["path"])
				# item["path"] = "plugin://plugin.video.xshare/?mode=90&page=0&url=" + urllib.quote_plus(item["path"])
			elif any(service in item["path"] for service in ["4share.vn/d/"]):
				item["path"] = "plugin://plugin.video.xshare/?mode=38&page=0&url=" + urllib.quote_plus(item["path"])
			elif any(service in item["path"] for service in ["4share.vn/f/"]):
			# elif any(service in item["path"] for service in ["4share.vn/f/", "fshare.vn/file"]):
				item["path"] = "plugin://plugin.video.xshare/?mode=3&page=0&url=" + urllib.quote_plus(item["path"])
				item["is_playable"] = True
				item["path"] = pluginrootpath + "/play/" + urllib.quote_plus(item["path"])
			elif "youtube.com/channel" in item["path"]:
				# https://www.youtube.com/channel/UC-9-kyTW8ZkZNDHQJ6FgpwQ
				yt_route = "ytcp" if "playlists" in item["path"] else "ytc"
				yt_cid = re.compile("youtube.com/channel/(.+?)$").findall(item["path"])[0]
				item["path"] = "plugin://plugin.video.kodi4vn.launcher/%s/%s/" % (yt_route, yt_cid)
				item["path"] = item["path"].replace("/playlists","")
			elif "youtube.com/playlist" in item["path"]:
				# https://www.youtube.com/playlist?list=PLFgquLnL59alCl_2TQvOiD5Vgm1hCaGSI
				yt_pid = re.compile("list=(.+?)$").findall(item["path"])[0]
				item["path"] = "plugin://plugin.video.kodi4vn.launcher/ytp/%s/" % yt_pid
			else:		
				# Nếu là direct link thì route đến hàm play_url
				item["is_playable"] = True
				item["path"] = pluginrootpath + "/play/" + urllib.quote_plus(item["path"])
		items += [item]
	if url_path == "0":
		add_playlist_item  = [{
			"context_menu": [
				ClearPlaylists(""),
			],
			"label":"[COLOR yellow]*** Thêm Playlist***[/COLOR]",
			"path": "%s/add-playlist" % (pluginrootpath),
			"thumbnail": "http://1.bp.blogspot.com/-gc1x9VtxIg0/VbggLVxszWI/AAAAAAAAANo/Msz5Wu0wN4E/s1600/playlist-advertorial.png"
		}]
		items += add_playlist_item
		playlists = plugin.get_storage('playlists')
		if 'sections' in playlists:
			for section in playlists['sections']:
				item = {
					"context_menu": [
						ClearPlaylists(section),
					]
				}
				item["label"] = section
				item["path"]  = "%s/section/%s" % (
					pluginrootpath,
					section.split("] ")[-1]
				)
				item["thumbnail"] = "http://1.bp.blogspot.com/-gc1x9VtxIg0/VbggLVxszWI/AAAAAAAAANo/Msz5Wu0wN4E/s1600/playlist-advertorial.png"
				items.append(item)
	return items

@plugin.route('/remove-playlists/', name="remove_all")
@plugin.route('/remove-playlists/<item>')
def RemovePlaylists(item=""):
	item = urllib.unquote_plus(item)
	if item is not "":
		playlists = plugin.get_storage('playlists')
		if 'sections' in playlists:
			new_playlists = []
			for section in playlists["sections"]:
				if section != item:
					new_playlists += [section]
			playlists["sections"] = new_playlists
	else:
		plugin.get_storage('playlists').clear()
	xbmc.executebuiltin('Container.Refresh')

def ClearPlaylists(item=""):
	if item == "":
		label = '[COLOR yellow]Xóa hết Playlists[/COLOR]'
	else:
		label = '[COLOR yellow]Xóa "%s"[/COLOR]' % item.encode("utf8")

	return (label, actions.background(
		"%s/remove-playlists/%s" % (pluginrootpath,urllib.quote_plus(item))
	))


def getValue(colid):
	'''
	Hàm lấy giá trị theo cột của của mỗi dòng sheet
	Parameters
	----------
	colid : string
		Số thự tự của cột
	'''
	if colid is not None: return colid["v"]
	else: return ""

@plugin.route('/')
def Home():
	'''	Main Menu
	'''
	GA() # tracking
	Section("0")

@plugin.route('/cached-section/<path>/<tracking_string>')
def CachedSection(path = "0", tracking_string = "Home"):
	GA( # tracking
		"Section - %s" % tracking_string,
		"/section/%s" % path
	)
	return plugin.finish(getCachedItems(path))

@plugin.route('/section/<path>/<tracking_string>')
def Section(path = "0", tracking_string = "Home"):
	'''
	Liệt kê danh sách các item của một sheet
	Parameters
	----------
	path : string
		"gid" của sheet
	tracking_string : string
		 Tên dễ đọc của view
	'''
	GA( # tracking
		"Section - %s" % tracking_string,
		"/section/%s" % path
	)
	items = AddTracking(getItems(path))
	return plugin.finish(items)

@plugin.route('/add-playlist/<tracking_string>')
def AddPlaylist(tracking_string = "Add Playlist"):
	sheet_url = plugin.keyboard(heading='Nhập URL của Google Spreadsheet (có hỗ trợ link rút gọn như bit.ly, goo.gl)')
	if sheet_url:
		try:
			resp, content = http.request(sheet_url,"HEAD")
			sid, gid = re.compile("/d/(.+?)/.+?gid=(\d+)").findall(resp["content-location"])[0]

			playlists = plugin.get_storage('playlists')
			name = plugin.keyboard(heading='Đặt tên cho Playlist')
			if 'sections' in playlists:
				playlists["sections"] = ["[[COLOR yellow]%s[/COLOR]] %s@%s" % (name,gid,sid)] + playlists["sections"]
			else:
				playlists["sections"] = ["[[COLOR yellow]%s[/COLOR]] %s@%s" % (name,gid,sid)]
			xbmc.executebuiltin('Container.Refresh')
		except: 
			line1 = "Vui lòng nhập URL hợp lệ. Ví dụ dạng đầy đủ:"
			line2 = "http://docs.google.com/spreadsheets/d/xxx/edit#gid=###"
			line3 = "Hoặc rút gọn: http://bit.ly/xxxxxx hoặc http://goo.gl/xxxxx"
			dlg = xbmcgui.Dialog()
			dlg.ok("URL không hợp lệ!!!", line1, line2, line3)

@plugin.route('/fshare/<path>/<tracking_string>')
def FShare(path = "0", tracking_string = "FShare"):
	(resp, content) = http.request(
		path, "GET",
		headers=sheet_headers
	)
	items = []
	filelist = re.compile('(?s)<ul class="filelist table table-striped" id="filelist">.+?</ul>').findall(content)[0]
	for folder, fid, title, size in re.compile('(?s)<a[^>]*class="(filename.*?)" data-id="(.+?)"[^>]*title="(.+?)">.+?<div class="pull-left file_size align-right"[^>]*>(.+?)</div>').findall(filelist):
		item={}
		if "folder" in folder:
			item["path"] = "%s/fshare/%s/%s" % (
				pluginrootpath,
				urllib.quote_plus("https://www.fshare.vn/folder/" + fid),
				urllib.quote_plus("[FShare] %s (%s)" % (title, size))
			)
			item["label"] = "[FShare] %s (%s)" % (title, size)
		else:
			item["path"] = "%s/play/%s/%s" % (
				pluginrootpath,
				urllib.quote_plus("https://www.fshare.vn/file/" + fid),
				urllib.quote_plus("[FShare] %s (%s)" % (title, size))
			)
			item["label"] = "[FShare] %s (%s)" % (title, size)
			item["is_playable"] = True
		items += [item]
	return plugin.finish(items)

@plugin.route('/m3u-section/<path>/<tracking_string>')
def M3USection(path = "0", tracking_string = "M3U"):
	'''
	Liệt kê danh sách các item của sheet M3U Playlist
	Parameters
	----------
	path : string
		"gid" của sheet M3U Playlist
	tracking_string : string
		 Tên dễ đọc của view
	'''
	GA( # tracking
		"M3U Section - %s" % tracking_string,
		"/m3u-section/%s" % path
	)
	items = getItems(path)
	for item in items:
		# Chỉnh lại thành m3u item
		item["path"] = item["path"].replace("/play/","/m3u/")
		if "is_playable" in item:
			del item["is_playable"]
		if "playable" in item:
			del item["playable"]
	return plugin.finish(AddTracking(items))

@plugin.route('/m3u/<path>', name = "m3u_default")
@plugin.route('/m3u/<path>/<tracking_string>')
def M3U(path = "0", tracking_string = "M3U"):
	'''
	Liệt kê danh sách các item của sheet M3U Playlist
	Parameters
	----------
	path : string
		Link chưa nội dung playlist m3u
	tracking_string : string
		 Tên dễ đọc của view
	'''
	GA( # tracking
		"M3U - %s" % tracking_string,
		"/m3u/%s" % path
	)

	items = M3UToItems(path)
	return plugin.finish(AddTracking(items))

@plugin.route('/install-repo/<path>/<tracking_string>')
def InstallRepo(path = "0", tracking_string = ""):
	'''
	Cài đặt repo
	Parameters
	----------
	path : string
		Nếu truyền "gid" của Repositories sheet:
			Cài tự động toàn bộ repo trong Repositories sheet
		Nếu truyền link download zip repo
			Download và cài zip repo đó
	tracking_string : string
		 Tên dễ đọc của view
	'''
	GA( # tracking
		"Install Repo - %s" % tracking_string,
		"/install-repo/%s" % path
	)
	if path.isdigit(): # xác định GID
		pDialog = xbmcgui.DialogProgress()
		pDialog.create('Vui lòng đợi','Bắt đầu cài repo','Đang tải...')
		items = getItems(path)
		total = len(items)
		i = 0
		failed = []
		for item in items:
			done = int(100 * i / total)
			pDialog.update(done,'Đang tải', item["label2"] + '...')
			try:
				item["path"] = "http" + item["path"].split("http")[-1]
				download(urllib.unquote_plus(item["path"]), item["label2"])
			except:
				failed += [item["label"].encode("utf-8")]
			if pDialog.iscanceled():
				break
			i+=1
		pDialog.close()
		if len(failed) > 0:
			dlg = xbmcgui.Dialog()
			s = "Không thể cài các rep sau:\n[COLOR orange]%s[/COLOR]" % "\n".join(failed)
			dlg.ok('Chú ý: Không cài đủ repo!', s)
		else:
			dlg = xbmcgui.Dialog()
			s = "Tất cả repo đã được cài thành công"
			dlg.ok('Cài Repo thành công!', s)

	else: # cài repo riêng lẻ
		try:
			download(path, "")
			dlg = xbmcgui.Dialog()
			s = "Repo %s đã được cài thành công" % tracking_string
			dlg.ok('Cài Repo thành công!', s)
		except:
			dlg = xbmcgui.Dialog()
			s = "Vùi lòng thử cài lại lần sau"
			dlg.ok('Cài repo thất bại!', s)

	xbmc.executebuiltin("XBMC.UpdateLocalAddons()")
	xbmc.executebuiltin("XBMC.UpdateAddonRepos()")

@plugin.route('/repo-section/<path>/<tracking_string>')
def RepoSection(path = "0", tracking_string = ""):
	'''
	Liệt kê các repo
	Parameters
	----------
	path : string
		Link download zip repo.
	tracking_string : string
		Tên dễ đọc của view
	'''
	GA( # tracking
		"Repo Section - %s" % tracking_string,
		"/repo-section/%s" % path
	)

	items = getItems(path)
	for item in items:
		if "/play/" in item["path"]:
			item["path"] = item["path"].replace("/play/","/install-repo/")
		# hack xbmcswift2 item to set both is_playable and is_folder to False
		item["is_playable"] = False
	items = AddTracking(items)

	install_all_item = {
		"label"      : "[COLOR green]Tự động cài tất cả Repo dưới (khuyên dùng)[/COLOR]".decode("utf-8"),
		"path"       : pluginrootpath + "/install-repo/%s/%s" % (path,urllib.quote_plus("Install all repo")),
		"is_playable": False,
		"info"       : {"plot": "Bạn nên cài tất cả repo để sử dụng đầy đủ tính năng của [VN Open Playlist]"}
	}
	items = [install_all_item] + items
	return plugin.finish(items)

def download(path,reponame):
	'''
	Parameters
	----------
	path : string
		Link download zip repo.
	reponame : string
		Tên thư mục của repo để kiểm tra đã cài chưa.
		Mặc định được gán cho item["label2"].
		Truyền "" để bỏ qua Kiểm tra đã cài
	'''
	if reponame == "":
		reponame = "temp"
		repo_zip = xbmc.translatePath(os.path.join(tmp,"%s.zip" % reponame))
		urllib.urlretrieve(path,repo_zip)
		with contextlib.closing(zipfile.ZipFile(repo_zip, "r")) as z:
			z.extractall(addons_folder)
	else:
		repo_path = xbmc.translatePath('special://home/addons/%s' % reponame)
		if not os.path.isdir(repo_path):
			if reponame == "": reponame = "temp"
			repo_zip = xbmc.translatePath(os.path.join(tmp,"%s.zip" % reponame))
			urllib.urlretrieve(path,repo_zip)
			with contextlib.closing(zipfile.ZipFile(repo_zip, "r")) as z:
				z.extractall(addons_folder)

def AddTracking(items):
	'''
	Hàm thêm chuỗi tracking cho các item
	Parameters
	----------
	items : list
		Danh sách các item theo chuẩn xbmcswift2.
	'''
	for item in items:
		if "plugin.video.thongld.vnplaylist" in item["path"]:
			item["path"] = "%s/%s" % (item["path"], urllib.quote_plus(item["label"]))
	return items

@plugin.route('/executebuiltin/<path>/<tracking_string>')
def execbuiltin(path,tracking_string=""):
	GA( # tracking
		"Execute Builtin - %s" % tracking_string,
		"/repo-execbuiltin/%s" % path
	)
	try:
		xbmc.executebuiltin('XBMC.RunPlugin(%s)' % urllib.unquote_plus(path))
	except: pass

@plugin.route('/play/<url>/<title>')
def play_url(url, title=""):
	GA("Play [%s]" % title, "/play/%s/%s" % (title,url))
	plugin.set_resolved_url(get_playable_url(url))

def get_playable_url(url):
	if "youtube" in url:
		match = re.compile('(youtu\.be\/|youtube-nocookie\.com\/|youtube\.com\/(watch\?(.*&)?v=|(embed|v|user)\/))([^\?&"\'>]+)').findall(url)
		yid   = match[0][len(match[0])-1].replace('v/','')
		url = 'plugin://plugin.video.youtube/play/?video_id=%s' % yid
	elif "google.com" in url:
		url = getGDriveHighestQuality(url)
	elif "fshare.vn/file" in url:
		http.follow_redirects = False
		get_fshare = "https://docs.google.com/spreadsheets/d/13VzQebjGYac5hxe1I-z1pIvMiNB0gSG7oWJlFHWnqsA/export?format=tsv&gid=0"
		try:
			(resp, content) = http.request(
				get_fshare, "GET"
			)
		except:
			header  = "Server quá tải!"
			message = "Xin vui lòng thử lại sau"
			xbmc.executebuiltin('Notification("%s", "%s", "%d", "%s")' % (header, message, 10000, ''))
			return ""

		tmps = content.split('\n')
		random.shuffle(tmps)
		for tmp in tmps:
			try:
				fshare_headers = {
					'User-Agent':'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.3; WOW64; Trident/7.0)',
					'Cookie':'session_id=%s' % tmp
				}

				(resp, content) = http.request(
					url, "GET", headers = fshare_headers
				)
				if "Tập tin quý khách yêu cầu không tồn tại" in content:
					header  = "Không lấy được link FShare VIP!"
					message = "Link không tồn tại hoặc file đã bị xóa"
					xbmc.executebuiltin('Notification("%s", "%s", "%d", "%s")' % (header, message, 10000, ''))

					h = {
						"Accept-Encoding" : "gzip, deflate, sdch, br",
						"Content-Type": "application/x-www-form-urlencoded"
					}
					(resp, content) = http.request(
						"aHR0cHM6Ly9kb2NzLmdvb2dsZS5jb20vZm9ybXMvZC9lLzFGQUlwUUxTZndkWU5zdzZxZG80NzhEYlRNRU9helRkMEVMR056Sm9KcFV3SlBEZlBoc0NaV2RBL2Zvcm1SZXNwb25zZQ==".decode("base64"),
						"POST", headers = h,
						body=urllib.urlencode({"entry.955186172": url})
					)
					return ""
				else:
					return resp["location"]
			except: pass
	else:
		if "://" not in url: url = None
	return url

def GetPlayLinkFromDriveID(drive_id):
	play_url = "https://drive.google.com/uc?export=mp4&id=%s" % drive_id
	(resp, content) = http.request(
		play_url, "HEAD",
		headers=sheet_headers
	)
	confirm = ""
	try: confirm = re.compile('download_warning_.+?=(.+?);').findall(resp['set-cookie'])[0]
	except: return play_url
	tail = "|User-Agent=%s&Cookie=%s" % (urllib.quote(sheet_headers["User-Agent"]),urllib.quote(resp['set-cookie']))
	play_url = "%s&confirm=%s" % (play_url,confirm) + tail
	return play_url

def GA(title="Home",page="/"):
	'''
	Hàm thống kê lượt sử dụng bằng Google Analytics (GA)
	Parameters
	----------
	title : string
		Tên dễ đọc của view.
	page : string
		Đường dẫn của view.
	'''
	try:
		ga_url    = "http://www.google-analytics.com/collect"
		client_id = open(cid_path).read()
		data      = {
			'v'   : '1',
			'tid' : 'UA-52209804-5', #Thay GA id của bạn ở đây
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

def getGDriveHighestQuality(url):
	(resp, content) = http.request(
		url, "GET",
		headers=sheet_headers
	)
	match = re.compile('(\["fmt_stream_map".+?\])').findall(content)[0]
	prefer_quality = ["38","37","46","22","45","18","43"]
	stream_map = json.loads(match)[1].split(",")
	for q in prefer_quality:
		for stream in stream_map:
			if stream.startswith(q+"|"):
				url = stream.split("|")[1]
				tail = "|User-Agent=%s&Cookie=%s" % (urllib.quote(sheet_headers["User-Agent"]),urllib.quote(resp['set-cookie']))
				return url + tail

# Tạo client id cho GA tracking
# Tham khảo client id tại https://support.google.com/analytics/answer/6205850?hl=vi
device_path = xbmc.translatePath('special://userdata')
if os.path.exists(device_path)==False:
	os.mkdir(device_path)
cid_path = os.path.join(device_path, 'cid')
if os.path.exists(cid_path)==False:
	with open(cid_path,"w") as f:
		f.write(str(uuid.uuid1()))

if __name__ == '__main__':
	plugin.run()