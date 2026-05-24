import requests, time

class OSINTEngine:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'JARVIS/3.0'})

    def lookup_ip(self, ip: str) -> dict:
        try:
            r = self.session.get(f"http://ip-api.com/json/{ip}", timeout=5)
            d = r.json()
            return {"ip": ip, "country": d.get("country"), "city": d.get("city"),
                    "isp": d.get("isp"), "summary": f"{ip} → {d.get('city')}, {d.get('country')} | {d.get('isp')}"}
        except Exception as e:
            return {"error": str(e)}

    def search_username(self, username: str) -> dict:
        platforms = {
            "GitHub": f"https://github.com/{username}",
            "Twitter": f"https://twitter.com/{username}",
            "Instagram": f"https://www.instagram.com/{username}",
            "Reddit": f"https://www.reddit.com/user/{username}",
            "TikTok": f"https://www.tiktok.com/@{username}",
        }
        found = []
        for platform, url in platforms.items():
            try:
                r = self.session.head(url, timeout=3, allow_redirects=True)
                if r.status_code == 200:
                    found.append({"platform": platform, "url": url})
                time.sleep(0.2)
            except:
                pass
        return {"username": username, "found_on": found,
                "summary": f"'{username}' trouvé sur: {', '.join(p['platform'] for p in found)}" if found else f"'{username}' non trouvé"}

    def whois_domain(self, domain: str) -> dict:
        try:
            import whois
            w = whois.whois(domain)
            return {"domain": domain, "registrar": str(w.registrar),
                    "created": str(w.creation_date), "summary": f"{domain} | Registrar: {w.registrar}"}
        except ImportError:
            return {"error": "pip install python-whois"}
        except Exception as e:
            return {"error": str(e)}

    def dns_lookup(self, domain: str) -> dict:
        try:
            import socket
            ip = socket.gethostbyname(domain)
            return {"domain": domain, "ip": ip, "summary": f"{domain} → {ip}"}
        except Exception as e:
            return {"error": str(e)}

    def port_scan(self, host: str, ports: list = None) -> dict:
        import socket
        if not ports:
            ports = [80, 443, 22, 21, 3306, 8080]
        open_ports = []
        for port in ports:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.5)
                if s.connect_ex((host, port)) == 0:
                    open_ports.append(port)
                s.close()
            except:
                pass
        return {"host": host, "open_ports": open_ports,
                "summary": f"{host} — Ports ouverts: {', '.join(map(str, open_ports)) if open_ports else 'aucun'}"}

osint = OSINTEngine()
