import csv
from colorama import Fore, Style

def import_from_csv(file_path, vault_manager):
    """Imports passwords securely using a rollback-safe transaction."""
    imported_count = 0
    skipped_details = [] 
    buffer_entries = []
    
    try:
        entries = vault_manager.get_entries()
        existing_signatures = {f"{e['title'].strip().lower()}|{e['username'].strip().lower()}" for e in entries}
            
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            field_map = {k.lower(): k for k in reader.fieldnames}

            col_name = field_map.get('name') or field_map.get('login_name') or field_map.get('title')
            col_url = field_map.get('url') or field_map.get('login_uri')
            col_user = field_map.get('username') or field_map.get('login_username')
            col_pass = field_map.get('password') or field_map.get('login_password')
            col_note = field_map.get('notes') or field_map.get('note')
            
            if not (col_name and col_user and col_pass):
                return 0, f"{Fore.RED}Unrecognized CSV format. Missing headers.{Style.RESET_ALL}"

            for row in reader:
                title = row.get(col_name, '').strip()
                user = row.get(col_user, '').strip()
                password = row.get(col_pass, '')

                if not title or not password:
                    continue

                incoming_sig = f"{title.lower()}|{user.lower()}"
                
                if incoming_sig in existing_signatures:
                    skipped_details.append(f"{title} ({user})")
                else:
                    buffer_entries.append({
                        'title': title, 'username': user, 'password': password,
                        'url': row.get(col_url, ''), 'notes': row.get(col_note, '')
                    })
                    existing_signatures.add(incoming_sig)

        if buffer_entries:
            vault_manager.add_entries_bulk(buffer_entries)
            imported_count = len(buffer_entries)

        msg = f"{Fore.GREEN}[✓] Import finished.{Style.RESET_ALL}\n"
        msg += f"    - New entries added: {imported_count}\n"
        
        if skipped_details:
            msg += f"\n{Fore.YELLOW}[!] Skipped {len(skipped_details)} duplicates:{Style.RESET_ALL}\n"
            for item in skipped_details:
                msg += f"    [X] {item}\n"
        
        return imported_count, msg

    except Exception as e:
        return 0, f"Critical error importing: {str(e)}"