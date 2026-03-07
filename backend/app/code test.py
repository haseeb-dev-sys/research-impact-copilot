import httpx
r = httpx.get("https://api.openalex.org/authors?search=Yoshua+Bengio&per_page=1")
print(r.status_code)
data = r.json()
if data["results"]:
    print(data["results"][0]["display_name"])
    print(data["results"][0]["cited_by_count"])