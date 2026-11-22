#!/usr/bin/env python3
"""Hẹn đăng video Cơ Khí Minh Kiên lên TikTok / YouTube / Facebook qua Buffer API (miễn phí).
Đọc lich/*.json, đăng kênh nào chưa xong, ghi kết quả vào lich/da_dang/<tên>.json.
Mỗi file lich: {"video_url","due_at":"YYYY-MM-DDTHH:MM:00+07:00","caption","caption_tiktok"?,
"yt_title","fb_title"?,"platforms":["tiktok","youtube","facebook"]}"""
import json, os, sys, glob, datetime as dt, urllib.request

API = "https://api.buffer.com"
KEY = os.environ.get("BUFFER_API_KEY", "").strip()
if not KEY:
    sys.exit("Thiếu secret BUFFER_API_KEY")

def gql(query, variables=None):
    req = urllib.request.Request(API, data=json.dumps({"query": query, "variables": variables or {}}).encode(),
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.load(r)
    if out.get("errors"):
        raise RuntimeError(json.dumps(out["errors"], ensure_ascii=False))
    return out["data"]

orgs = gql("query{account{organizations{id name}}}")["account"]["organizations"]
org = os.environ.get("BUFFER_ORG_ID") or orgs[0]["id"]
chans = gql("query($i:ChannelsInput!){channels(input:$i){id name service}}", {"i": {"organizationId": org}})["channels"]
by_service = {}
for c in chans:
    by_service.setdefault(c["service"].lower(), c)
print("Kênh Buffer:", [(c["service"], c["name"]) for c in chans])

MUT = """mutation($input: CreatePostInput!){ createPost(input:$input){
 ... on PostActionSuccess { post { id dueAt } } ... on MutationError { message } } }"""

def create(inp):
    res = gql(MUT, {"input": inp})["createPost"]
    if "post" in res and res["post"]:
        return res["post"]
    raise RuntimeError(res.get("message", str(res)))

now = dt.datetime.now(dt.timezone.utc)
os.makedirs("lich/da_dang", exist_ok=True)
loi = 0
for f in sorted(glob.glob("lich/*.json")):
    name = os.path.basename(f)
    done_path = f"lich/da_dang/{name}"
    job = json.load(open(f, encoding="utf-8"))
    done = json.load(open(done_path, encoding="utf-8")) if os.path.exists(done_path) else {}
    due = dt.datetime.fromisoformat(job["due_at"]).astimezone(dt.timezone.utc)
    if due < now + dt.timedelta(minutes=10):
        due = now + dt.timedelta(minutes=15)   # quá giờ thì đăng ngay sau 15 phút
    due_s = due.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    for p in job.get("platforms", ["tiktok", "youtube", "facebook"]):
        if done.get(p, {}).get("id"):
            continue
        ch = by_service.get(p)
        if not ch:
            done[p] = {"loi": f"Buffer chưa kết nối kênh {p}"}; print(name, p, "→ chưa có kênh"); loi += 1; continue
        text = job.get("caption_tiktok") if p == "tiktok" and job.get("caption_tiktok") else job["caption"]
        inp = {"channelId": ch["id"], "text": text, "schedulingType": "automatic", "mode": "customScheduled",
               "dueAt": due_s, "assets": [{"video": {"url": job["video_url"], "metadata": {"thumbnailOffset": 500}}}]}
        if p == "youtube":
            inp["metadata"] = {"youtube": {"title": job["yt_title"][:100], "categoryId": "26", "privacy": "public",
                               "license": "youtube", "madeForKids": False, "notifySubscribers": True}}
        tries = [None]
        if p == "facebook":
            tries = ["reel", "post"]
        last = None
        for t in tries:
            if t:
                inp["metadata"] = {"facebook": {"type": t}}
            try:
                post = create(inp); done[p] = {"id": post["id"], "dueAt": post.get("dueAt")}
                print(name, p, "→ hẹn", post.get("dueAt")); last = None; break
            except Exception as e:
                last = str(e)
        if last:
            done[p] = {"loi": last[:500]}; print(name, p, "→ LỖI", last[:300]); loi += 1
    json.dump(done, open(done_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
sys.exit(1 if loi else 0)
