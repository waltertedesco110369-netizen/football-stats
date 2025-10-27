#!/usr/bin/env python3
"""
Sistema di Ripristino Backup per Football Stats App
"""

import os
import shutil
import glob
from pathlib import Path
from datetime import datetime

class RestoreSystem:
    def __init__(self):
        self.project_root = Path.cwd()
        self.backup_dir = self.project_root / "backups"
        
    def list_backups(self):
        """Lista tutti i backup disponibili"""
        if not self.backup_dir.exists():
            return []
        
        backups = []
        for backup_path in self.backup_dir.glob("backup_*_TEST"):
            if backup_path.is_dir():
                # Estrai timestamp dal nome
                name = backup_path.name
                timestamp_str = name.replace("backup_", "").replace("_TEST", "")
                
                try:
                    timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    backups.append((backup_path, timestamp, timestamp_str))
                except ValueError:
                    continue
        
        # Ordina per data (più recente prima)
        backups.sort(key=lambda x: x[1], reverse=True)
        return backups
    
    def restore_backup(self, backup_path):
        """Ripristina da un backup specifico"""
        print(f"🔄 Ripristinando da: {backup_path.name}")
        
        # File da ripristinare
        files_to_restore = [
            "app_simple.py",
            "database.py", 
            "stats_calculator.py",
            "football_stats_test.db",
            "divisions_config.json"
        ]
        
        restored_count = 0
        for file_name in files_to_restore:
            source = backup_path / file_name
            destination = self.project_root / file_name
            
            if source.exists():
                shutil.copy2(source, destination)
                print(f"  ✅ Ripristinato: {file_name}")
                restored_count += 1
            else:
                print(f"  ⚠️  File non trovato nel backup: {file_name}")
        
        print(f"✅ Ripristino completato: {restored_count} file ripristinati")
        return restored_count > 0
    
    def interactive_restore(self):
        """Ripristino interattivo"""
        backups = self.list_backups()
        
        if not backups:
            print("❌ Nessun backup trovato!")
            return False
        
        print("📁 Backup disponibili:")
        print("=" * 50)
        
        for i, (backup_path, timestamp, timestamp_str) in enumerate(backups, 1):
            print(f"{i:2d}. {timestamp.strftime('%d/%m/%Y %H:%M:%S')} - {backup_path.name}")
        
        print("\n0. Annulla")
        
        try:
            choice = int(input("\nSeleziona backup da ripristinare (numero): "))
            
            if choice == 0:
                print("❌ Ripristino annullato")
                return False
            
            if 1 <= choice <= len(backups):
                backup_path, _, _ = backups[choice - 1]
                
                confirm = input(f"\n⚠️  Confermi il ripristino da {backup_path.name}? (s/N): ")
                if confirm.lower() in ['s', 'si', 'y', 'yes']:
                    return self.restore_backup(backup_path)
                else:
                    print("❌ Ripristino annullato")
                    return False
            else:
                print("❌ Scelta non valida")
                return False
                
        except ValueError:
            print("❌ Inserisci un numero valido")
            return False
        except KeyboardInterrupt:
            print("\n❌ Ripristino annullato")
            return False
    
    def restore_latest(self):
        """Ripristina l'ultimo backup"""
        backups = self.list_backups()
        
        if not backups:
            print("❌ Nessun backup trovato!")
            return False
        
        latest_backup = backups[0][0]
        print(f"🔄 Ripristinando ultimo backup: {latest_backup.name}")
        return self.restore_backup(latest_backup)

def main():
    """Funzione principale"""
    restorer = RestoreSystem()
    
    print("🔄 SISTEMA DI RIPRISTINO BACKUP")
    print("=" * 40)
    
    # Verifica se ci sono argomenti da linea di comando
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--latest":
        success = restorer.restore_latest()
    else:
        success = restorer.interactive_restore()
    
    if success:
        print("\n✅ Ripristino completato!")
        print("🔄 Riavvia le app per applicare le modifiche.")
    else:
        print("\n❌ Ripristino fallito o annullato.")

if __name__ == "__main__":
    main()
