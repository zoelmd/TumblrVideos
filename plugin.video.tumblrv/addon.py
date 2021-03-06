# -*- coding: utf-8 -*-
import os, sys, ssl, time, datetime, json
from kodiswift import Plugin, ListItem, xbmc, xbmcgui, xbmcvfs, xbmcaddon, xbmcplugin, xbmcmixin
from resources.lib import getoauth, TUMBLRAUTH, TumblrRestClient, tumblrsearch
try:
    from xbmcutil import viewModes
except:
    pass
tclient = TumblrRestClient
viewmode = 20
APIOK = False
plugin = Plugin(name="TumblrV", addon_id="plugin.video.tumblrv", plugin_file="addon.py", info_type="video")
__addondir__ = xbmc.translatePath(plugin.addon.getAddonInfo('path'))
__resdir__ = os.path.join(__addondir__, 'resources')
__imgdir__ = os.path.join(__resdir__, 'images')
__imgsearch__ = os.path.join(__imgdir__, 'search.png')
__imgnext__ = os.path.join(__imgdir__, 'next.png')
__imgtumblr__ = os.path.join(__imgdir__, 'tumblr.png')
tagpath = os.path.join(xbmc.translatePath('special://profile/addon_data/'), 'plugin.video.tumblrv', 'tagslist.json')
weekdelta = datetime.timedelta(days=7)


@plugin.route('/')
def index():
    #setview_list()
    litems = []
    itemdashvids = {}
    itemliked = {}
    itemfollowing = {}
    itemtagbrowse = {}
    itemtagged = {}
    itemsearch = {}
    tstamp = str(time.mktime((datetime.datetime.now() - weekdelta).timetuple())).split('.', 1)[0]
    try:
        itemdashvids = {
            'label': 'Dashboard Videos',
            'thumbnail': __imgtumblr__,
            'path': plugin.url_for(endpoint=dashboard, offset=0, lastid=0),
            'is_playable': False}
        itemliked = {
            'label': 'Liked Videos',
            'thumbnail': __imgtumblr__,
            'path': plugin.url_for(endpoint=liked, offset=0),
            'is_playable': False}
        itemfollowing = {
            'label': 'Following',
            'thumbnail': __imgtumblr__,
             'path': plugin.url_for(endpoint=following, offset=0),
             'is_playable': False}
        itemtagbrowse = {
            'label': 'Browse Tags',
            'thumbnail': __imgtumblr__,
            'path': plugin.url_for(endpoint=taglist, timestamp=str(tstamp)),
            'is_playable': False}
        itemtagged = {
            'label': 'Search Tags',
            'thumbnail': __imgtumblr__,
            'path': plugin.url_for(endpoint=tags, tagname='0', timestamp=str(tstamp)),
            'is_playable': False}
        itemsearch = {
            'label': 'Search Tumblr',
            'thumbnail': __imgsearch__,
            'path': plugin.url_for(endpoint=search),
            'is_playable': False}
        litems.append(itemdashvids)
        litems.append(itemliked)
        litems.append(itemfollowing)
        litems.append(itemtagbrowse)
        litems.append(itemtagged)
        litems.append(itemsearch)
    except Exception, e:
        plugin.notify(msg=e.message, delay=10000)
    if not APIOK:
        itemappkey = {
            'label': "Consumer KEY:\n{0}".format(TUMBLRAUTH['consumer_key']),
            'path': plugin.url_for(endpoint=setup)}
        itemappsecret = {
            'label': "Consumer SECRET:\n{0}".format(TUMBLRAUTH['consumer_secret']),
            'path': plugin.url_for(endpoint=setup)
        }
        itemurl = {
            'label': 'https://api.tumblr.com/console/calls/user/info\nenter Key and Secret from this screen',
            'path': plugin.url_for(endpoint=setup)
        }
        litems.append(itemurl)
        litems.append(itemappkey)
        litems.append(itemappsecret)
    return litems


@plugin.route('/setup')
def setup():
    litems = []
    itemappkey = {
        'label': "Consumer KEY: {0}".format(TUMBLRAUTH['consumer_key']),
        'path': plugin.keyboard(default=TUMBLRAUTH['consumer_key'], heading=TUMBLRAUTH['consumer_key'])}
    itemappsecret = {
        'label': "Consumer SECRET: {0}".format(TUMBLRAUTH['consumer_secret']),
        'path': plugin.keyboard(default=TUMBLRAUTH['consumer_secret'], heading=TUMBLRAUTH['consumer_secret'])
    }
    itemurl = {
        'label': 'Visit: https://api.tumblr.com/console/calls/user/info\nenter Key and Secret from this screen',
        'path': plugin.url_for(endpoint=setup)
    }
    litems.append(itemurl)
    litems.append(itemappkey)
    litems.append(itemappsecret)
    return litems


@plugin.route('/setup/get')
def setup_get():
    token = plugin.keyboard(heading="OAUTH TOKEN")
    secret = plugin.keyboard(heading="OAUTH SECRET")
    plugin.set_setting('oauth_token', token)
    plugin.set_setting('oauth_secret', secret)
    TUMBLRAUTH['oauth_secret'] = secret
    TUMBLRAUTH['oauth_token'] = token
    try:
        client = TumblrRestClient(**TUMBLRAUTH)
        APIOK = True
    except:
        plugin.notify("Problem with the Tumblr OAUTH details", "Tumblr Login Failed")


@plugin.route('/liked/<offset>')
def liked(offset=0):
    #setview_thumb()
    likes = {}
    alltags = []
    litems = []
    listlikes = []
    strpage = str(((int(offset) + 20) / 20))
    nextitem = ListItem(label="Next Page -> #{0}".format(int(strpage) + 1), label2="Liked Videos", icon=__imgnext__,
                        thumbnail=__imgnext__, path=plugin.url_for(liked, offset=int(20 + int(offset))))
    nextitem.set_art({'poster': __imgnext__, 'thumbnail': __imgnext__, 'fanart': __imgnext__})
    nextitem.is_folder = True
    #litems = [nextitem]
    results = tclient.likes(limit=20, offset=int(offset))
    if results is not None:
        if results.get('liked_posts', '') is not None:
            listlikes = results.get('liked_posts', '')
        else:
            listlikes = results.get(results.keys()[-1])
    for item in listlikes:
        if item.get('type', '') == 'video':
            b = {}
            b.update(item)
            lbl = ""
            lbl2 = ""
            img = __imgtumblr__
            alltags.extend(item.get('tags', []))
            if 'thumb' in str(item.keys()[:]):
                if item.get('thumbnail_url', '') is not None:
                    img = item.get('thumbnail_url', '')  # .replace('https', 'http') #item.get('thumbnail_url','')
            elif 'image' in str(item.keys()[:]):
                if item.get('image_permalink', ""):
                    img = item.get('image_permalink', "")
            try:
                plugin.log.debug(msg=item.get('thumbnail_url', ''))
                if len(b.get('slug', '')) > 0:
                    lbl = b.get('slug', '')
                elif len(b.get('title', '')) > 0:
                    lbl = b.get('title', '')
                elif len(b.get('caption', '')) > 0:
                    lbl = Strip(b.get('caption', ''))
                elif len(b.get('summary', '')) > 0:
                    lbl = b.get('summary', '')
                elif len(b.get('source_title', '')) > 0:
                    lbl = b.get('source_title', '')
                else:
                    lbl = b.get('short_url', '')
                if len(item.get('summary', '')) > 0:
                    lbl2 = item.get('summary', '')
                else:
                    lbl2 = item.get('blog_name', "") + " / " + item.get('source_title', '') + "(" + item.get(
                        'slug_name', '') + ")"
            except:
                lbl = b.get(b.keys()[0], "")
                lbl2 = b.get(b.keys()[-1], "")
            vidurl = item.get('video_url', "")
            if vidurl is not None and len(vidurl) > 10:
                litem = ListItem(label=lbl, label2=lbl2, icon=img, thumbnail=img, path=vidurl)
                litem.playable = True
                litem.is_folder = False
                if item.get('date', '') is not None:
                    rdate = str(item.get('date', '')).split(' ', 1)[0].strip()
                litem.set_info(info_type='video', info_labels={'Date': rdate})
                litem.set_art({'poster': img, 'thumbnail': img, 'fanart': img})
                pathdl = plugin.url_for(endpoint=download, urlvideo=vidurl)
                litem.add_context_menu_items([('Download', 'RunPlugin({0})'.format(pathdl)), ])
                litems.append(litem)
    savetags(alltags)
    litems.append(nextitem)
    return litems


@plugin.route('/taglist/<timestamp>')
def taglist(timestamp=0):
    #setview_list()
    if not os.path.exists(tagpath):
        json.dump([], fp=open(tagpath, mode='w'))
    litems = []
    alltags = json.load(open(tagpath))
    for tag in alltags:
        turl = plugin.url_for(tags, tagname=tag, timestamp=str(timestamp))
        li = ListItem(label=tag, label2=tag, icon=__imgtumblr__, thumbnail=__imgtumblr__, path=turl)
        li.is_folder = True
        litems.append(li)
    return litems


def setview_list():
    plugin.notify(msg="{0} View: {1} / L{2} / T{3}".format(str(plugin.request.path), str(plugin.get_setting('viewmode')),
                                                           str(plugin.get_setting('viewmodelist')),
                                                           str(plugin.get_setting('viewmodethumb'))))
    try:
        if int(plugin.get_setting('viewmodelist')) == 0:
            viewselector = viewModes.Selector(20)
            viewmode = viewselector.currentMode
            plugin.set_setting('viewmodelist', viewmode)
    except:
        plugin.set_setting('viewmodelist', 20)
    plugin.notify(msg="{0} View: {1} / L{2} / T{3}".format(str(plugin.request.path), str(plugin.get_setting('viewmode')),
                                                           str(plugin.get_setting('viewmodelist')),
                                                           str(plugin.get_setting('viewmodethumb'))))

def setview_thumb():
    plugin.notify(msg="{0} View: {1} / L{2} / T{3}".format(str(plugin.request.path), str(plugin.get_setting('viewmode')),
                                                           str(plugin.get_setting('viewmodelist')),
                                                           str(plugin.get_setting('viewmodethumb'))))
    try:
        if int(plugin.get_setting('viewmodethumb')) == 0:
            viewselector = viewModes.Selector(500)
            viewmode = viewselector.currentMode
            plugin.set_setting('viewmodethumb', viewmode)
    except:
        plugin.set_setting('viewmodethumb', 500)
    plugin.notify(msg="{0} View: {1} / L{2} / T{3}".format(str(plugin.request.path), str(plugin.get_setting('viewmode')),
                                                           str(plugin.get_setting('viewmodelist')),
                                                           str(plugin.get_setting('viewmodethumb'))))


@plugin.route('/tags/<tagname>/<timestamp>')
def tags(tagname='', timestamp=0):
    atags = {}
    taglist = []
    litems = []
    if tagname == '0':
        tagname = plugin.keyboard(plugin.get_setting('lastsearch'), 'Search for tags')
        plugin.set_setting('lastsearch', tagname)
    nextstamp = time.mktime((datetime.datetime.fromtimestamp(float(timestamp)) - weekdelta).timetuple())
    nstamp = str(nextstamp).split('.', 1)[0]
    nextitem = ListItem(label="Next -> {0}".format(time.ctime(nextstamp)), label2="Tagged Videos", icon=__imgnext__,
                        thumbnail=__imgnext__, path=plugin.url_for(tags, tagname=tagname, timestamp=nstamp))
    nextitem.set_art({'poster': __imgnext__, 'thumbnail': __imgnext__, 'fanart': __imgnext__})
    nextitem.is_folder = True
    #litems = [nextitem]
    if tagname is not None and len(tagname) > 0:
        results = tclient.tagged(tagname, filter='text') #), before=float(timestamp))
        if results is not None:
            for res in results:
                if res.get('type', '') == 'video': taglist.append(res)
        for item in taglist:
            b = {}
            b.update(item)
            lbl = ""
            lbl2 = ""
            img = __imgtumblr__
            if 'thumb' in str(item.keys()[:]):
                if item.get('thumbnail_url', '') is not None:
                    img = item.get('thumbnail_url', '')  # .replace('https', 'http') #item.get('thumbnail_url','')
            elif 'image' in str(item.keys()[:]):
                if item.get('image_permalink', ""):
                    img = item.get('image_permalink', "")
            try:
                plugin.log.debug(msg=item.get('thumbnail_url', ''))
                if len(b.get('slug', '')) > 0:
                    lbl = b.get('slug', '')
                elif len(b.get('title', '')) > 0:
                    lbl = b.get('title', '')
                elif len(b.get('caption', '')) > 0:
                    lbl = Strip(b.get('caption', ''))
                elif len(b.get('summary', '')) > 0:
                    lbl = b.get('summary', '')
                elif len(b.get('source_title', '')) > 0:
                    lbl = b.get('source_title', '')
                else:
                    lbl = b.get('short_url', '')
                if len(item.get('summary', '')) > 0:
                    lbl2 = item.get('summary', '')
                else:
                    lbl2 = item.get('blog_name', "") + " / " + item.get('source_title', '') + "(" + item.get(
                        'slug_name', '') + ")"
            except:
                lbl = b.get(b.keys()[0], "")
                lbl2 = b.get(b.keys()[-1], "")
            vidurl = item.get('video_url', "")
            if vidurl is not None and len(vidurl) > 10:
                litem = ListItem(label=lbl, label2=lbl2, icon=img, thumbnail=img, path=vidurl)
                litem.playable = True
                litem.is_folder = False
                if item.get('date', '') is not None:
                    rdate = str(item.get('date', '')).split(' ', 1)[0].strip()
                litem.set_info(info_type='video', info_labels={'Date': rdate})
                litem.set_art({'poster': img, 'thumbnail': img, 'fanart': img})
                litems.append(litem)
    litems = [nextitem]
    return litems


@plugin.route('/dashboard/<lastid>/<offset>')
def dashboard(lastid=0, offset=0):
    #setview_thumb()
    likes = {}
    listlikes = []
    litems = []
    strpage = str(((int(offset) + 20) / 20))
    # results = tclient.dashboard(offset=offset, limit=100)
    lastid = plugin.get_setting('lastid', int)
    if lastid == 0:
        lastid = 10000000000
    if lastid is None or lastid < 1000000:
        lastid = 10000000000
    results = tclient.dashboard(limit=20, offset=offset, type='video', since_id=lastid)
    nextitem = ListItem(label="Next Page -> #{0}".format(int(strpage)+1), label2="Liked Videos", icon=__imgnext__, thumbnail=__imgnext__, path=plugin.url_for(dashboard, offset=int(20+int(offset)), lastid=lastid))
    nextitem.set_art({'poster': __imgnext__, 'thumbnail': __imgnext__, 'fanart': __imgnext__})
    nextitem.is_folder = True
    # litems = [nextitem]
    litems = []
    alltags = []
    if results is not None:
        if results.get('posts', '') is not None:
            if results.get('posts', ''):
                results = results.get('posts', '')
            try:
                if isinstance(results, list):
                    listlikes = results
                else:
                    listlikes = results.get(results.keys()[0])
            except:
                listlikes = []
        else:
            listlikes = results.get(results.keys()[-1])
    for item in listlikes:
        if item.get('type', '') == 'video':
            b = item
            img = __imgtumblr__
            alltags.extend(item.get('tags', []))
            if 'thumb' in str(item.keys()[:]):
                if item.get('thumbnail_url', '') is not None:
                    img = item.get('thumbnail_url', '')  # .replace('https', 'http') #item.get('thumbnail_url','')
            elif 'image' in str(item.keys()[:]):
                if item.get('image_permalink', ""):
                    img = item.get('image_permalink', "")
            try:
                if len(b.get('slug', '')) > 0:
                    lbl = b.get('slug', '')
                elif len(b.get('title', '')) > 0:
                    lbl = b.get('title', '')
                elif len(b.get('caption', '')) > 0:
                    lbl = Strip(b.get('caption', ''))
                elif len(b.get('summary', '')) > 0:
                    lbl = b.get('summary', '')
                elif len(b.get('source_title', '')) > 0:
                    lbl = b.get('source_title', '')
                else:
                    lbl = b.get('short_url', '')
                if len(item.get('summary', '')) > 0:
                    lbl2 = item.get('summary', '')
                else:
                    lbl2 = item.get('blog_name', '') + " / " + item.get('source_title', '') + "(" + item.get(
                        'slug_name', '') + ")"
            except:
                lbl = b.get('blog_name', '')
                lbl2 = b.get('short_url', '')
            img = item.get('thumbnail_url', '')
            vidurl = item.get('video_url', '')
            if vidurl is not None and len(vidurl) > 10:
                if len(b.get('caption', '')) > 0:
                    lbl = Strip(b.get('caption', ''))
                litem = ListItem(label=lbl, label2=lbl2, icon=img, thumbnail=img, path=vidurl)
                litem.playable = True
                litem.is_folder = False
                if item.get('date', '') is not None:
                    rdate = str(item.get('date', '')).split(' ', 1)[0].strip()
                litem.set_info(info_type='video', info_labels={'Date': rdate})
                litem.set_art({'poster': img, 'thumbnail': img, 'fanart': img})
                pathdl = plugin.url_for(endpoint=download, urlvideo=vidurl)
                pathaddlike = plugin.url_for(endpoint=addlike, id=item.get('id', ''))
                litem.add_context_menu_items([('Download', 'RunPlugin({0})'.format(pathdl)), ('Like', 'RunPlugin({0})'.format(pathaddlike)),])
                litems.append(litem)
    item = listlikes[-1]
    plugin.set_setting('lastid', str(item.get('id', lastid)))
    savetags(alltags)
    litems.append(nextitem)
    return litems


@plugin.route('/addlike/<id>')
def addlike(id=0):
    try:
        tclient.like(None, id)
        plugin.notify(msg="LIKED: {0}".format(str(id)))
    except:
        plugin.notify(msg="Failed to add like: {0}".format(str(id)))


@plugin.route('/download/<urlvideo>')
def download(urlvideo):
    try:
        from YDStreamExtractor import getVideoInfo
        from YDStreamExtractor import handleDownload
        info = getVideoInfo(urlvideo, resolve_redirects=True)
        dlpath = plugin.get_setting('downloadpath')
        if not os.path.exists(dlpath):
            dlpath = xbmc.translatePath("home://")
        handleDownload(info, bg=True, path=dlpath)
    except:
        plugin.notify(urlvideo, "Download Failed")


def following_list(offset=0, max=0):
    litems = []
    offset = 0
    total = 0
    resp = tclient.following(offset=offset, limit=20)  # tclient.dashboard(type='videos')
    if max == 0:
        total = int(resp.get('total_blogs', 0))
        if total > 150: total = 150
    else:
        total = 20 + max
    results = resp.get('response', {})
    if results is not None:
        blogres = results.get('blogs', [])
        for blog in blogres:
            blog['updated'] = datetime.datetime.fromtimestamp(blog.get('updated'), 0).isoformat()
            litems.append(blog)
        try:
            for offnum in range(len(blogres), total, 20):
                newblogs = []
                newres = tclient.following(offset=offnum, limit=20)
                newblogs = newres.get('blogs', [])
                if len(newblogs) > 0:
                    for blog in newblogs:
                        blog['updated'] = datetime.datetime.fromtimestamp(blog['updated']).isoformat()
                        litems.append(blog)
        except:
            pass
    items = sorted(litems, key=lambda litems: litems['updated'])
    #plugin.notify(msg="Following: {0} Total: {1} Len: {2}".format(str(len(resp.get('blogs',[]))), str(total), str(len(litems))))
    return items


@plugin.route('/following/<offset>')
def following(offset=0):
    blogs = {}
    litems = []
    blogres = []
    listblogs = []
    litems = []
    name = ''
    updated = ''
    url = ''
    desc = ''
    strpage = str(((int(offset) + 50) / 50))
    nextitem = ListItem(label="Next Page -> #{0}".format(int(strpage) + 1), label2="More", icon=__imgnext__,
                        thumbnail=__imgnext__, path=plugin.url_for(following, offset=int(50 + int(offset))))
    nextitem.set_art({'poster': __imgnext__, 'thumbnail': __imgnext__, 'fanart': __imgnext__})
    nextitem.is_folder = True
    #litems = [nextitem]
    results = following_list(offset=offset) # max not working right now, max=50)
    for b in results:
        thumb = __imgtumblr__
        try:
            thumbd = {}
            name = b.get('name', '')
            title = b.get('title', '')
            desc = b.get('description', '')
            url = b.get('url', "http://{0}.tumblr.com".format(name))
            updated = b.get('updated', '')
            thumbd = tclient.avatar(name, 128)
            if len(thumbd.keys()) > 0:
                thumb = thumbd[thumbd.keys()[0]]
            if len(thumb) < 1:
                if len(b.get('theme', '{}')) > 0:
                    theme = b.get('theme', '{}')
                    if len(theme.get('header_image_scaled', '')) > 0: thumb = theme.get('header_image_scaled', '')
            iurl = plugin.url_for(endpoint=blogposts, blogname=name, offset=0)
            lbl = "{0}\n{1}".format(name, title.encode('latin-1', 'ignore'))
            lbl2 = desc.encode('latin-1', 'ignore')
            litem = ListItem(label=lbl, label2=lbl2, icon=thumb, thumbnail=thumb, path=iurl)
            litem.set_art({'poster': thumb, 'thumbnail': thumb, 'fanart': thumb})
            litem.is_folder = True
            litem.playable = False
            litems.append(litem)
        except:
            pass
    #items = sorted(litems, key=lambda litems: litems.label2)
    # litems.append(nextitem) NO NEXT PAGE TODO: Make max work and paginate results as this is slow
    return litems


@plugin.route('/blogposts/<blogname>/<offset>')
def blogposts(blogname, offset=0):
    listposts = []
    lbl = ''
    lbl2 = ''
    vidurl = ''
    results = []
    alltags = []
    litems = []
    if blogname.find('.') != -1:
        shortname = blogname.split('.', 1)[-1]
        if shortname.find('.') != -1:
            blogname = shortname.lsplit('.')[0]
    strpage = str((20 + int(offset)) / 20)
    nextitem = ListItem(label="Next Page -> #{0}".format(strpage), label2=blogname, icon=__imgnext__,
                        thumbnail=__imgnext__,
                        path=plugin.url_for(blogposts, blogname=blogname, offset=int(20 + int(offset))))
    nextitem.set_art({'poster': __imgnext__, 'thumbnail': __imgnext__, 'fanart': __imgnext__})
    nextitem.is_folder = True
    #litems = [nextitem]
    results = tclient.posts(blogname=blogname, limit=20, offset=int(offset), type='video')
    if results is not None:
        if len(results.get('posts', '')) > 1:
            results = results.get('posts', '')
        for post in results:
            lbl2 = post.get('blog_name', '')
            lbl = post.get('slug', '').replace('-', ' ')
            img = post.get('thumbnail_url', __imgtumblr__)
            alltags.extend(post.get('tags', []))
            try:
                if post.get('slug', '') is not None:
                    lbl = post.get('slug', '').replace('-', ' ')
                if len(post.get('caption', '')) > 0:
                    lbl = Strip(post.get('caption', ''))
                elif len(post.get('summary', '')) > 0:
                    lbl = post.get('summary', '')
                elif len(post.get('source_title', '')) > 0:
                    lbl = post.get('source_title', '')
                else:
                    lbl = post.get('short_url', '')
                if post.get('thumbnail_url', ''):
                    img = post.get('thumbnail_url', '')
                if post.get('video_url', '') is not None:
                    vidurl = post.get('video_url', '')
            except:
                plugin.notify(str(repr(post)))
            litem = ListItem(label=lbl, label2=lbl2, icon=img, thumbnail=img, path=vidurl)
            litem.playable = True
            litem.is_folder = False
            if len(post.get('date', '')) > 0:
                rdate = str(post.get('date', '')).split(' ', 1)[0].strip()
            litem.set_info(info_type='video', info_labels={'Date': rdate, 'Duration': post.get('duration', '')})
            litem.set_art({'poster': img, 'thumbnail': img, 'fanart': img})
            pathdl = plugin.url_for(endpoint=download, urlvideo=vidurl)
            pathaddlike = plugin.url_for(endpoint=addlike, id=post.get('id',''))
            litem.add_context_menu_items([('Download', 'RunPlugin({0})'.format(pathdl)), ('Like', 'RunPlugin({0})'.format(pathaddlike)), ])
            litems.append(litem)
    else:
        litems = []
        backurl = ''
        if offset == 0:
            backurl = plugin.url_for(endpoint=following, offset=0)
        else:
            backurl = plugin.url_for(blogposts, blogname=blogname, offset=(int(offset) - 20))
        nextitem = ListItem(label="No Results - GO BACK".format(strpage), label2=blogname, icon=__imgtumblr__,
                            thumbnail=__imgtumblr__, path=backurl)
        nextitem.set_art({'poster': __imgtumblr__, 'thumbnail': __imgtumblr__, 'fanart': __imgtumblr__})
        nextitem.is_folder = True
        litems = [nextitem]
    savetags(alltags)
    litems.append(nextitem)
    return litems


@plugin.route('/search')
def search():
    # plugin.log.debug(TUMBLRAUTH)
    # client = TumblrRestClient(**TUMBLRAUTH)
    # info = client.info()
    litems = []
    searchtxt = ''
    searchquery = ''
    offsetnum = 0
    searchtxt = plugin.get_setting('lastsearch')
    searchtxt = plugin.keyboard(searchtxt, 'Search All Sites', False)
    searchquery = searchtxt.replace(' ', '+')
    plugin.set_setting(key='lastsearch', val=searchtxt)
    results = following_list(offset=offsetnum)
    listmatch = []
    max = 20
    #if len(results) < 20:
    #    max = len(results) - 1
    for blog in results:
        name = blog.get('name', '')
        posts = tclient.posts(name, type='video')
        for post in posts.get('posts', []):
            for k,v in post.items():
                try:
                    if searchquery.lower() in str(v.encode('latin-1', 'ignore')).lower():
                        listmatch.append(post)
                        break
                except:
                    pass
    plugin.notify(msg="Matches: {0}".format(str(len(listmatch))))
    alltags = []
    for post in listmatch:
        lbl2 = post.get('blog_name', '')
        lbl = post.get('slug', '').replace('-', ' ')
        img = post.get('thumbnail_url', __imgtumblr__)
        alltags.extend(post.get('tags', []))
        try:
            if post.get('slug', '') is not None:
                lbl = post.get('slug', '').replace('-', ' ')
            if len(post.get('caption', '')) > 0:
                lbl = Strip(post.get('caption', ''))
            elif len(post.get('summary', '')) > 0:
                lbl = post.get('summary', '')
            elif len(post.get('source_title', '')) > 0:
                lbl = post.get('source_title', '')
            else:
                lbl = post.get('short_url', '')
            if post.get('thumbnail_url', ''):
                img = post.get('thumbnail_url', '')
            if post.get('video_url', '') is not None:
                vidurl = post.get('video_url', '')
        except:
            plugin.notify(str(repr(post)))
        litem = ListItem(label=lbl, label2=lbl2, icon=img, thumbnail=img, path=vidurl)
        litem.playable = True
        litem.is_folder = False
        if len(post.get('date', '')) > 0:
            rdate = str(post.get('date', '')).split(' ', 1)[0].strip()
        litem.set_info(info_type='video', info_labels={'Date': rdate, 'Duration': post.get('duration', '')})
        litem.set_art({'poster': img, 'thumbnail': img, 'fanart': img})
        pathdl = plugin.url_for(endpoint=download, urlvideo=vidurl)
        pathaddlike = plugin.url_for(endpoint=addlike, id=post.get('id', ''))
        litem.add_context_menu_items(
            [('Download', 'RunPlugin({0})'.format(pathdl)), ('Like', 'RunPlugin({0})'.format(pathaddlike)), ])
        litems.append(litem)
    savetags(alltags)
    return litems


def savetags(taglist=[]):
    if not os.path.exists(tagpath):
        json.dump([], fp=open(tagpath, mode='w'))
    taglist.extend(json.load(open(tagpath, mode='r')))
    alltags = sorted(set(taglist))
    json.dump(alltags, fp=open(tagpath, mode='w'))


def Strip(text):
    import re
    notagre = re.compile(r'<.+?>')
    return notagre.sub(' ', text).strip()


if __name__ == '__main__':
    try:
        otoken = plugin.get_setting('oauth_token')
        osecret = plugin.get_setting('oauth_secret')
        TUMBLRAUTH.update({'oauth_token': otoken, 'oauth_secret': osecret})
        tclient = TumblrRestClient(**TUMBLRAUTH)
        info = tclient.info()
        if info is not None and 'user' in info.keys():
            APIOK = True
        else:
            APIOK = False
    except:
        APIOK = False
        try:
            TUMBLRAUTH = getoauth()
            tclient = TumblrRestClient(**TUMBLRAUTH)
            info = tclient.info()
            if info is not None and info.get('user', None) is not None:
                APIOK = True
            else:
                APIOK = False
        except:
            plugin.notify(
                msg="Required Tumblr OAUTH token missing..Backup plan!",
                title="Tumblr Login Failed", delay=10000)
            plugin.log.error(msg="Tumblr API OAuth settings invalid. This addon requires you to authorize this Addon in your Tumblr account and in turn in the settings you must provide the TOKEN and SECRET that Tumblr returns.\nhttps://api.tumblr.com/console/calls/user/info\n\tUse the Consumer Key and Secret from the addon settings to authorize this addon and the OAUTH Token and Secret the website returns must be put into the settings.")
            try:  # Try an old style API key from off github as a backup so some functionality is provided?
                TUMBLRAUTH = dict(consumer_key='5wEwFCF0rbiHXYZQQeQnNetuwZMmIyrUxIePLqUMcZlheVXwc4',
                     consumer_secret='GCLMI2LnMZqO2b5QheRvUSYY51Ujk7nWG2sYroqozW06x4hWch',
                     oauth_token='RBesLWIhoxC1StezFBQ5EZf7A9EkdHvvuQQWyLpyy8vdj8aqvU',
                     oauth_secret='GQAEtLIJuPojQ8fojZrh0CFBzUbqQu8cFH5ejnChQBl4ljJB4a')
                TUMBLRAUTH.update({'api_key', 'fuiKNFp9vQFvjLNvx4sUwti4Yb5yGutBN4Xh10LXZhhRKjWlV4'})
                tclient = TumblrRestClient(**TUMBLRAUTH)
            except:
                plugin.notify(msg="Read Settings for instructions", title="COULDN'T AUTH TO TUMBLR")
    viewmode = int(plugin.get_setting('viewmode'))
    plugin.run()
    plugin.set_content(content='movies')
    viewmodel = 51
    viewmodet = 500
    if str(plugin.request.path).startswith('/taglist/') or plugin.request.path == '/':
        viewmodel = int(plugin.get_setting('viewmodelist'))
        if viewmodel == 0: viewmodel = 51
        plugin.set_view_mode(viewmodel)
    else:
        viewmodet = int(plugin.get_setting('viewmodethumb'))
        if viewmodet == 0: viewmodet = 500
        plugin.set_view_mode(viewmodet)
