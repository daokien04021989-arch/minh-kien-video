#!/usr/bin/env python3
"""Lấy số liệu video đã đăng + bài lỗi từ Buffer API (miễn phí), ghi lich/thong_ke.json."""
import json, os, sys, datetime as dt, urllib.request
KEY = os.environ.get("BUFFER_API_KEY", "").strip()
if not KEY: sys.exit("Thiếu secret BUFFER_API_KEY")
def gql(q, v=None):
    req = urllib.request.Request("https://api.buffer.com", data=json.dumps({"query": q, "variables": v or {}}).encode(),
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r: out = json.load(r)
    if out.get("errors"): raise RuntimeError(json.dumps(out["errors"], ensure_ascii=False)[:800])
    return out["data"]
org = gql("query{account{organizations{id}}}")["account"]["organizations"][0]["id"]
chans = gql("query($i:ChannelsInput!){channels(input:$i){id name service}}", {"i": {"organizationId": org}})["channels"]
cmap = {c["id"]: c for c in chans}
Q = """query($i:PostsInput!,$a:String){posts(input:$i,first:50,after:$a){
 edges{node{id text dueAt status channelId metrics{name value unit}}} pageInfo{endCursor hasNextPage}}}"""
start = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=60)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
res = {"cap_nhat": dt.datetime.now(dt.timezone.utc).isoformat(), "bai": [], "loi": []}
for st in (["sent"], ["error"], ["scheduled"]):
    after = None
    for _ in range(10):
        d = gql(Q, {"i": {"organizationId": org, "filter": {"status": st, "channelIds": list(cmap)}}, "a": after})["posts"]
        for e in d["edges"]:
            n = e["node"]; c = cmap.get(n["channelId"], {})
            row = {"kenh": c.get("service"), "gio": n.get("dueAt"), "trang_thai": n.get("status"),
                   "noi_dung": (n.get("text") or "")[:90],
                   "so_lieu": {m["name"]: m["value"] for m in (n.get("metrics") or [])}}
            (res["loi"] if st == ["error"] else res["bai"]).append(row)
        if not d["pageInfo"]["hasNextPage"]: break
        after = d["pageInfo"]["endCursor"]
os.makedirs("lich", exist_ok=True)
json.dump(res, open("lich/thong_ke.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("Bài:", len(res["bai"]), "Lỗi:", len(res["loi"]))
