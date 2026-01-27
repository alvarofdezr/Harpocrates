import csv
import os

def import_from_csv(file_path, vault_instance, secret_key, master_password):
    if not os.path.exists(file_path):
        return 0, "El archivo no existe."

    count = 0
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                app_name = row.get('name') or row.get('Title') or 'Imported'
                username = row.get('login_username') or row.get('username') or ''
                password = row.get('login_password') or row.get('password')
                url = row.get('login_uri') or row.get('url') or ''
                
                raw_notes = row.get('notes') or row.get('Notes') or ''
                folder = row.get('folder') or ''
                totp = row.get('login_totp') or ''
                
                final_notes = raw_notes
                if folder:
                    final_notes = f"[Folder: {folder}]\n" + final_notes
                if totp:
                    final_notes += f"\n[TOTP Secret: {totp}]"

                if password: 
                    vault_instance.add_entry(
                        master_password,
                        secret_key,
                        app_name,
                        username,
                        password,
                        url,
                        final_notes  
                    )
                    count += 1
                    
        return count, f"Éxito. Se importaron {count} entradas (con notas)."
    
    except Exception as e:
        return count, f"Error importando: {str(e)}"