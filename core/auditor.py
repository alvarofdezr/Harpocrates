import hashlib
import requests

class PasswordAuditor:
    @staticmethod
    def check_pwned(password):
        """
        Verifica si una contraseña ha sido expuesta en brechas de datos.
        Usa K-Anonymity (API Range) para privacidad total.
        
        Retorna:
            int: Número de veces que se ha filtrado.
            -1: Error de conexión.
        """

        sha1_password = hashlib.sha1(password.encode('utf-8')).hexdigest().upper() #nosec
        prefix, suffix = sha1_password[:5], sha1_password[5:]
        
        url = f"https://api.pwnedpasswords.com/range/{prefix}"
        
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            hashes = (line.split(':') for line in response.text.splitlines())
            
            for h, count in hashes:
                if h == suffix:
                    return int(count)
            
            return 0 
            
        except requests.RequestException:
            return -1 