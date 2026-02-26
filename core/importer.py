import csv
import os
from colorama import Fore, Style
from datetime import datetime

def import_from_csv(file_path, vault_manager, secret_key, master_password):
    """
    Imports passwords from a CSV file with Conflict Reporting.
    Explicitly lists which entries were skipped due to duplication.
    """
    imported_count = 0
    skipped_details = [] 
    
    try:
        current_data = vault_manager.load_vault(master_password, secret_key)
        entries = current_data.get('entries', [])
        existing_signatures = set()
        for e in entries:
            sig = f"{e['title'].strip().lower()}|{e['username'].strip().lower()}"
            existing_signatures.add(sig)
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            field_map = {k.lower(): k for k in reader.fieldnames}

            col_name = field_map.get('name') or field_map.get('login_name') or field_map.get('title')
            col_url = field_map.get('url') or field_map.get('login_uri')
            col_user = field_map.get('username') or field_map.get('login_username')
            col_pass = field_map.get('password') or field_map.get('login_password')
            col_note = field_map.get('notes') or field_map.get('note')
            
            if not (col_name and col_user and col_pass):
                return 0, Fore.RED + "Unrecognized CSV format. Missing standard headers."

            new_entries_buffer = []

            for row in reader:
                title = row[col_name]
                user = row[col_user]
                password = row[col_pass]
                url = row.get(col_url, '')
                notes = row.get(col_note, '')

                if not title or not password:
                    continue

                incoming_sig = f"{title.strip().lower()}|{user.strip().lower()}"
                
                if incoming_sig in existing_signatures:
                    skipped_details.append(f"{title} ({user})")
                else:
                    new_entry = {
                        "title": title,
                        "username": user,
                        "password": password,
                        "url": url,
                        "notes": notes,
                        "created_at": datetime.now().isoformat()
                    }
                    new_entries_buffer.append(new_entry)
                    existing_signatures.add(incoming_sig)

        if new_entries_buffer:
            entries.extend(new_entries_buffer)
            current_data['entries'] = entries

            if 'logs' in current_data:
                log_msg = f"Imported {len(new_entries_buffer)} items. Conflicts: {len(skipped_details)}"
                current_data['logs'].insert(0, {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "action": "IMPORT_CSV",
                    "details": log_msg
                })

            vault_manager.save_vault(current_data, master_password, secret_key)
            imported_count = len(new_entries_buffer)

        msg = f"{Fore.GREEN}[✓] Import finished.{Style.RESET_ALL}\n"
        msg += f"    - New entries added: {imported_count}\n"
        
        if skipped_details:
            msg += f"\n{Fore.YELLOW}[!] Skipped {len(skipped_details)} duplicates (already in your vault):{Style.RESET_ALL}\n"
            msg += Fore.RED + "-" * 50 + "\n"
            for item in skipped_details:
                msg += f"    [X] {item}\n"
            msg += "-" * 50 + Style.RESET_ALL
            msg += f"\n{Fore.CYAN}NOTE: If you wanted the CSV version of these duplicates,\ndelete the old entry in Harpocrates and import again.{Style.RESET_ALL}"
        
        return imported_count, msg

    except Exception as e:
        return 0, f"Critical import error: {str(e)}"