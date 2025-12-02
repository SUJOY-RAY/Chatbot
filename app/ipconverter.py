import requests

def ip_to_location(ip: str = None):
    try:
        url = f"http://ip-api.com/json/{ip or ''}"  # empty query uses caller's IP
        params = {"fields": "status,message,country,city,zip,lat,lon"}  # limit data
        resp = requests.get(url, params=params, timeout=5)
        data = resp.json()

        if data.get("status") == "success":
            return {
                "lat": data.get("lat"),
                "lon": data.get("lon"),
                "country": data.get("country"),
                "city": data.get("city"),
                "zip": data.get("zip")
            }
        else:
            print("IP lookup failed:", data.get("message"))
            return None
    except Exception as e:
        print("IP lookup exception:", e)
        return None
