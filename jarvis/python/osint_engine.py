"""
Module OSINT pour JARVIS.
Outils de recherche en sources ouvertes — légaux et éthiques.
Sources : start.me/p/L1rEYQ/osint4all
"""
import requests
import json
import os
import re
import time
from typing import Optional

class OSINTEngine:

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (JARVIS Research Agent)'
        })

    # ===== RECHERCHE IP =====
    def lookup_ip(self, ip: str) -> dict:
        """Géolocalisation et infos d'une IP (gratuit, aucune clé)"""
        try:
            r = self.session.get(f"http://ip-api.com/json/{ip}", timeout=5)
            data = r.json()
            return {
                "ip": ip,
                "country": data.get("country"),
                "city": data.get("city"),
                "isp": data.get("isp"),
                "lat": data.get("lat"),
                "lon": data.get("lon"),
                "org": data.get("org"),
                "summary": f"{ip} → {data.get('city')}, {data.get('country')} | FAI: {data.get('isp')}"
            }
        except Exception as e:
            return {"error": str(e)}

    # ===== WHOIS DOMAINE =====
    def whois_domain(self, domain: str) -> dict:
        """Infos WHOIS sur un domaine (gratuit)"""
        try:
            import whois
            w = whois.whois(domain)
            return {
                "domain": domain,
                "registrar": str(w.registrar),
                "creation_date": str(w.creation_date),
                "expiration_date": str(w.expiration_date),
                "name_servers": str(w.name_servers),
                "summary": f"{domain} | Registrar: {w.registrar} | Créé: {str(w.creation_date)[:10]}"
            }
        except ImportError:
            return {"error": "pip install python-whois"}
        except Exception as e:
            return {"error": str(e)}

    # ===== RECHERCHE EMAIL (vérification existence) =====
    def check_email_breach(self, email: str) -> dict:
        """Vérifie si un email a été compromis (HaveIBeenPwned)"""
        try:
            headers = {"hibp-api-key": os.environ.get("HIBP_API_KEY", ""),
                       "User-Agent": "JARVIS"}
            r = self.session.get(
                f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}",
                headers=headers, timeout=5
            )
            if r.status_code == 200:
                breaches = r.json()
                names = [b['Name'] for b in breaches]
                return {"email": email, "breached": True, "services": names,
                        "summary": f"COMPROMIS dans {len(names)} services: {', '.join(names[:5])}"}
            elif r.status_code == 404:
                return {"email": email, "breached": False,
                        "summary": f"{email} n'est pas dans les bases de données compromises connues."}
            return {"error": f"HTTP {r.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    # ===== RECHERCHE IMAGE INVERSÉE =====
    def reverse_image_search(self, image_path: str) -> dict:
        """Prépare une recherche d'image inversée (génère les URLs)"""
        # Ouvre TinEye et Google Images avec l'image uploadée
        return {
            "summary": "Pour recherche inversée, utiliser : TinEye (tineye.com) ou Google Images (images.google.com)",
            "action": {"type": "open_url", "url": "https://images.google.com"},
            "note": "Uploader l'image manuellement sur ces services"
        }

    # ===== INFORMATIONS SUR UN USERNAME =====
    def search_username(self, username: str) -> dict:
        """Recherche un pseudo sur les plateformes principales"""
        platforms = {
            "GitHub": f"https://github.com/{username}",
            "Twitter/X": f"https://twitter.com/{username}",
            "Instagram": f"https://www.instagram.com/{username}",
            "Reddit": f"https://www.reddit.com/user/{username}",
            "TikTok": f"https://www.tiktok.com/@{username}",
            "YouTube": f"https://www.youtube.com/@{username}",
            "LinkedIn": f"https://www.linkedin.com/in/{username}",
        }
        found = []
        for platform, url in platforms.items():
            try:
                r = self.session.head(url, timeout=3, allow_redirects=True)
                if r.status_code == 200:
                    found.append({"platform": platform, "url": url, "exists": True})
                time.sleep(0.3)
            except:
                pass
        return {
            "username": username,
            "found_on": found,
            "summary": f"'{username}' trouvé sur: {', '.join(p['platform'] for p in found)}" if found else f"'{username}' non trouvé"
        }

    # ===== DNS LOOKUP =====
    def dns_lookup(self, domain: str) -> dict:
        """Résolution DNS d'un domaine"""
        try:
            import socket
            import dns.resolver
            ip = socket.gethostbyname(domain)
            try:
                mx = [str(r.exchange) for r in dns.resolver.resolve(domain, 'MX')]
            except:
                mx = []
            return {
                "domain": domain, "ip": ip, "mx_records": mx,
                "summary": f"{domain} → {ip} | MX: {', '.join(mx[:2]) if mx else 'aucun'}"
            }
        except ImportError:
            import socket
            ip = socket.gethostbyname(domain)
            return {"domain": domain, "ip": ip, "summary": f"{domain} → {ip}"}
        except Exception as e:
            return {"error": str(e)}

    # ===== ANALYSE DE MÉTADONNÉES FICHIER =====
    def analyze_file_metadata(self, file_path: str) -> dict:
        """Extrait les métadonnées d'un fichier (EXIF images, PDF, etc.)"""
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS
            img = Image.open(file_path)
            exif_data = img._getexif()
            if exif_data:
                readable = {}
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    readable[tag] = str(value)
                gps = readable.get('GPSInfo', {})
                return {"file": file_path, "metadata": readable,
                        "has_gps": bool(gps),
                        "summary": f"Métadonnées extraites: {len(readable)} champs. GPS: {'OUI' if gps else 'NON'}"}
            return {"file": file_path, "summary": "Pas de métadonnées EXIF"}
        except Exception as e:
            return {"error": str(e)}

    # ===== SHODAN-LIKE : scan de ports simple =====
    def port_scan(self, host: str, ports: list = None) -> dict:
        """Scan des ports ouverts sur un hôte"""
        import socket
        if ports is None:
            ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 3306, 5432, 8080, 8443]
        open_ports = []
        for port in ports:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.5)
                result = s.connect_ex((host, port))
                if result == 0:
                    open_ports.append(port)
                s.close()
            except:
                pass
        return {
            "host": host,
            "open_ports": open_ports,
            "summary": f"{host} — Ports ouverts: {', '.join(map(str, open_ports)) if open_ports else 'aucun'}"
        }

osint = OSINTEngine()
