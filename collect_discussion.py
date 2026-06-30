import urllib.request,urllib.error,urllib.parse,time,re,html,csv
import xml.etree.ElementTree as ET
ATOM={"a":"http://www.w3.org/2005/Atom"}; UA="macos:wsb-classifier:0.1 (academic project)"
print("cooldown 30s...",flush=True); time.sleep(30)
def fetch(url,tries=6):
    for i in range(tries):
        try: return urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":UA}),timeout=30).read().decode("utf-8","replace")
        except urllib.error.HTTPError as e:
            if e.code==429: w=min(60,12*(i+1)); print(f"   429 {w}s",flush=True); time.sleep(w); continue
            return None
        except Exception: time.sleep(8); continue
    return None
def body(h):
    if not h: return ""
    m=re.search(r"<!-- SC_OFF -->(.*?)<!-- SC_ON -->",h,re.S); b=m.group(1) if m else ""
    return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",b))).strip()[:4000]
MEGA=re.compile(r"daily discussion|what are your moves|weekend|megathread|pajama|hearing|moves tomorrow|rate my|subreddit of the day",re.I)
existing=set(r["id"] for r in csv.DictReader(open("data/raw_posts.csv")))
seen={}; base="https://www.reddit.com/r/wallstreetbets"
OUT="data/raw_discussion_extra.csv"
def flush_csv():
    with open(OUT,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["id","flair","title","selftext","text","link"]); w.writeheader()
        for r in seen.values(): w.writerow(r)
feeds=[]
for fl in ["Discussion","Question"]:
    q=urllib.parse.quote(f'flair:"{fl}"')
    for sort in ["top","relevance","comments"]:
        for t in (["month","year","all"] if fl=="Discussion" else ["year","all"]):
            feeds.append((fl,f"{base}/search.rss?q={q}&restrict_sr=1&sort={sort}&t={t}&limit=25"))
for fl,url in feeds:
    x=fetch(url); added=0
    if x:
        try: root=ET.fromstring(x)
        except ET.ParseError: root=None
        if root is not None:
            for e in root.findall("a:entry",ATOM):
                pid=(e.findtext("a:id",default="",namespaces=ATOM) or "").replace("t3_","")
                title=(e.findtext("a:title",default="",namespaces=ATOM) or "").strip()
                if not pid or not title or pid in existing or pid in seen or MEGA.search(title): continue
                c=e.find("a:content",ATOM); bd=body(c.text if c is not None else "")
                lk=e.find("a:link",ATOM)
                seen[pid]={"id":pid,"flair":fl,"title":title,"selftext":bd,"text":(title+"\n\n"+bd).strip(),"link":lk.get("href") if lk is not None else ""}
                added+=1
    flush_csv()
    print(f"[{fl:10s} {url.split('sort=')[1].split('&')[0]:10s}] +{added} total={len(seen)} (saved)",flush=True)
    time.sleep(9)
print("WROTE",len(seen),"->",OUT,flush=True)
