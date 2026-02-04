import requests
import threading
import hashlib
import re
import json
import random
import os
import time
from datetime import datetime
from urllib.parse import quote_plus, unquote
from colorama import Fore, Style

class OsintScanner:
    def __init__(self):
        self.SHERLOCK_DB_URL = "https://raw.githubusercontent.com/sherlock-project/sherlock/master/sherlock_project/resources/data.json"
        self.results = []
        self.lock = threading.Lock()
        
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
        ]
        
        self.fallback_sites = {
            "GitHub": {"url": "https://github.com/{}", "errorType": "status_code"},
            "Twitter": {"url": "https://twitter.com/{}", "errorType": "status_code"},
            "Instagram": {"url": "https://www.instagram.com/{}", "errorType": "status_code"},
            "Facebook": {"url": "https://www.facebook.com/{}", "errorType": "status_code"},
            "Reddit": {"url": "https://www.reddit.com/user/{}", "errorType": "status_code"},
            "Twitch": {"url": "https://m.twitch.tv/{}", "errorType": "status_code"},
            "Pinterest": {"url": "https://www.pinterest.com/{}", "errorType": "status_code"},
            "Flickr": {"url": "https://www.flickr.com/people/{}", "errorType": "status_code"},
            "Steam": {"url": "https://steamcommunity.com/id/{}", "errorType": "status_code"},
            "Vimeo": {"url": "https://vimeo.com/{}", "errorType": "status_code"},
            "SoundCloud": {"url": "https://soundcloud.com/{}", "errorType": "status_code"},
            "Disqus": {"url": "https://disqus.com/by/{}", "errorType": "status_code"},
            "Medium": {"url": "https://medium.com/@{}", "errorType": "status_code"},
            "Dev.to": {"url": "https://dev.to/{}", "errorType": "status_code"},
            "GitLab": {"url": "https://gitlab.com/{}", "errorType": "status_code"},
            "BitBucket": {"url": "https://bitbucket.org/{}", "errorType": "status_code"},
            "About.me": {"url": "https://about.me/{}", "errorType": "status_code"},
            "Patreon": {"url": "https://www.patreon.com/{}", "errorType": "status_code"},
            "Freelancer": {"url": "https://www.freelancer.com/u/{}", "errorType": "status_code"},
            "Pastebin": {"url": "https://pastebin.com/u/{}", "errorType": "status_code"}
        }

    def _get_random_header(self):
        return {'User-Agent': random.choice(self.user_agents)}

    def _fetch_database(self):
        print(f"{Fore.YELLOW}[*] Actualizando base de datos OSINT...{Style.RESET_ALL}", end=" ")
        try:
            resp = requests.get(self.SHERLOCK_DB_URL, timeout=10) 
            if resp.status_code == 200:
                data = resp.json()
                print(f"{Fore.GREEN}[OK] ({len(data)} sitios cargados){Style.RESET_ALL}")
                return data
            else:
                print(f"{Fore.RED}[Error HTTP {resp.status_code}]{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}[FAIL: {str(e)}]{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}[i] Usando lista local de respaldo (20 sitios).{Style.RESET_ALL}")
        
        return self.fallback_sites

    def _check_site(self, site_name, site_data, username):
        if not isinstance(site_data, dict):
            return
        url_template = site_data.get('url')
        if not url_template:
            return

        url = url_template.replace("{}", username)
        
        if site_data.get("errorType") != "status_code": 
            return

        # --- SISTEMA DE PROXIES ---
        # proxy_list = [
        #    "http://10.10.1.10:3128",
        #    "http://12.12.12.12:8080",
        # ]
        # proxies = {
        #    "http": random.choice(proxy_list),
        #    "https": random.choice(proxy_list)
        # }
        # -------------------------------------

        try:
            response = requests.get(
                url, 
                headers=self._get_random_header(), 
                timeout=10, 
                allow_redirects=False
                # proxies=proxies
            )
            
            if response.status_code == 200:
                with self.lock:
                    self.results.append({"site": site_name, "url": url})
                    print(f"\r{Fore.GREEN}[+] {site_name:<20}: {url}{Style.RESET_ALL}          ")
                    
        except Exception:
            pass

    def _check_gravatar(self, email):
        """Busca perfil público en Gravatar usando hash MD5."""
        print(f"\n{Fore.CYAN}[*] Detectado Email. Buscando huella en Gravatar...{Style.RESET_ALL}")
        email_hash = hashlib.md5(email.strip().lower().encode('utf-8')).hexdigest() # nosec
        url = f"https://www.gravatar.com/avatar/{email_hash}?d=404"
        
        try:
            if requests.get(url, timeout=5).status_code == 200:
                print(f"{Fore.GREEN}[+] GRAVATAR ENCONTRADO: {url}{Style.RESET_ALL}")
                self.results.append({"site": "Gravatar", "url": url, "note": "Profile Picture Found"})
            else:
                print(f"{Fore.YELLOW}[-] Sin perfil Gravatar.{Style.RESET_ALL}")
        except: pass

    def _search_duckduckgo(self, email):
        """Realiza Dorking en DuckDuckGo para encontrar menciones públicas del correo."""
        print(f"\n{Fore.CYAN}[*] Realizando 'Dorking' en DuckDuckGo (Búsqueda profunda)...{Style.RESET_ALL}")
        
        query = quote_plus(f'"{email}"')
        url = f"https://html.duckduckgo.com/html/?q={query}"
        
        try:
            resp = requests.get(url, headers=self._get_random_header(), timeout=10)
            
            if resp.status_code == 200:
                links = re.findall(r'<a class="result__url" href="(.*?)">', resp.text)
                
                if links:
                    print(f"{Fore.GREEN}[!] El correo aparece públicamente en {len(links)} sitios:{Style.RESET_ALL}")
                    found_count = 0
                    for link in links:
                        if found_count >= 10: break 
                        
                        clean_link = link.replace("/l/?kh=-1&uddg=", "")
                        clean_link = unquote(clean_link)
                        
                        if "duckduckgo" not in clean_link:
                            print(f"    - {clean_link}")
                            self.results.append({"site": "Public Index", "url": clean_link})
                            found_count += 1
                else:
                    print(f"{Fore.YELLOW}[i] No se encontraron resultados públicos indexados.{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}[Error Buscador] {e}{Style.RESET_ALL}")

    def save_report(self, target):
        """Genera un archivo JSON con todos los hallazgos."""
        if not self.results:
            return None
            
        safe_target = target.replace("@", "_").replace(".", "_")
        filename = f"osint_report_{safe_target}_{int(datetime.now().timestamp())}.json"
        
        report_data = {
            "target": target,
            "scan_date": datetime.now().isoformat(),
            "total_hits": len(self.results),
            "findings": self.results
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=4, ensure_ascii=False)
            return filename
        except Exception as e:
            print(f"{Fore.RED}Error guardando reporte: {e}{Style.RESET_ALL}")
            return None

    def scan_target(self, target):
        self.results = []
        
        if re.match(r"[^@]+@[^@]+\.[^@]+", target):
            print(f"\n{Fore.CYAN}[*] Objetivo tipo EMAIL detectado.{Style.RESET_ALL}")
            
            self._check_gravatar(target)
            self._search_duckduckgo(target)
            
            derived_username = target.split('@')[0]
            
            print(f"\n{Fore.YELLOW}[?] Sugerencia Inteligente:{Style.RESET_ALL}")
            print(f"    Muchas personas usan el prefijo de su correo como usuario en redes.")
            print(f"    ¿Quieres escanear también el usuario '{Fore.CYAN}{derived_username}{Style.RESET_ALL}'?")
            
            if input(f"    (s/n) > ").lower() == 's':
                return self.scan_target(derived_username)
            
            return self.results
        
        sites_db = self._fetch_database()
        print(f"\n{Fore.CYAN}[*] Iniciando rastreo de PERFIL: '{target}'{Style.RESET_ALL}")
        
        target_sites = list(sites_db.items()) 
        total_sites = len(target_sites)
        
        print(f"[*] Objetivo: {total_sites} plataformas.")
        print(f"[*] Modo: {Fore.YELLOW}STEALTH (Lento pero seguro){Style.RESET_ALL}...\n")
        
        threads = []
        batch_size = 8 
        processed = 0
        
        for i in range(0, total_sites, batch_size):
            batch = target_sites[i : i + batch_size]
            batch_threads = []
            
            for name, data in batch:
                t = threading.Thread(target=self._check_site, args=(name, data, target))
                batch_threads.append(t)
                t.start()
            
            for t in batch_threads:
                t.join()
            
            processed += len(batch)
            print(f"\r    Progreso: {processed}/{total_sites} sitios analizados...", end="")
            
            time.sleep(random.uniform(0.5, 1.5))

        print("\n") 
        return self.results