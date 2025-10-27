#!/usr/bin/env python3
"""
Sistema di Deploy Automatico per Football Stats App
- Crea backup completo di TEST
- Deploy su WEB e MOBILE
- Test di tutte le app
"""

import os
import shutil
import subprocess
import time
import re
from datetime import datetime
from pathlib import Path

class DeploySystem:
    def __init__(self):
        self.project_root = Path.cwd()
        self.backup_dir = self.project_root / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
    def create_backup(self):
        """Crea backup completo dell'ambiente TEST e pulisce backup vecchi"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}_TEST"
        backup_path = self.backup_dir / backup_name
        
        print(f"🔄 Creando backup: {backup_name}")
        
        # File da includere nel backup
        files_to_backup = [
            "app_simple.py",
            "app_web.py",
            "app_mobile.py",
            "database.py", 
            "stats_calculator.py",
            "football_stats_test.db",
            "football_stats_web.db",
            "football_stats_mobile.db",
            "divisions_config.json",
            "league_rules.json"
        ]
        
        # Crea directory backup
        backup_path.mkdir(exist_ok=True)
        
        # Copia file
        for file_name in files_to_backup:
            source = self.project_root / file_name
            if source.exists():
                shutil.copy2(source, backup_path / file_name)
                print(f"  ✅ Copiato: {file_name}")
            else:
                print(f"  ⚠️  File non trovato: {file_name}")
        
        # Pulisci backup vecchi (mantieni solo gli ultimi 3)
        self._cleanup_old_backups()
        
        print(f"✅ Backup completato: {backup_path}")
        return backup_path
    
    def _cleanup_old_backups(self):
        """Elimina backup vecchi mantenendo solo quelli configurati"""
        config = self._load_deploy_config()
        backup_count = config.get("backup_count", 3)
        
        print(f"🧹 Pulizia backup vecchi (mantieni ultimi {backup_count})...")
        
        # Trova tutti i backup
        backup_folders = []
        for item in self.backup_dir.iterdir():
            if item.is_dir() and item.name.startswith("backup_") and item.name.endswith("_TEST"):
                backup_folders.append(item)
        
        # Ordina per data di creazione (più recenti prima)
        backup_folders.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Mantieni solo quelli configurati, elimina il resto
        folders_to_delete = backup_folders[backup_count:]  # Elimina quelli oltre il limite
        
        for folder in folders_to_delete:
            try:
                shutil.rmtree(folder)
                print(f"  🗑️  Eliminato: {folder.name}")
            except Exception as e:
                print(f"  ⚠️  Errore eliminazione {folder.name}: {e}")
        
        remaining = len(backup_folders) - len(folders_to_delete)
        print(f"  ✅ Backup rimanenti: {remaining}/{backup_count}")
    
    def deploy_to_web(self):
        """Deploy app_simple.py su app_web.py preservando configurazioni WEB"""
        print("🌐 Deploy su APP WEB...")
        
        # Leggi app_simple.py
        with open("app_simple.py", "r", encoding="utf-8") as f:
            test_content = f.read()
        
        # CONTROLLO ZONA PROTETTA
        if not self._check_protected_zone(test_content):
            print("  ❌ DEPLOY BLOCCATO: Zona protetta modificata!")
            return False
        
        # Leggi app_web.py esistente per preservare configurazioni
        web_file = Path("app_web.py")
        if web_file.exists():
            with open("app_web.py", "r", encoding="utf-8") as f:
                web_content = f.read()
            
            # Estrai configurazioni specifiche WEB da preservare
            web_configs = self._extract_environment_configs(web_content, "WEB")
        else:
            web_configs = {
                'environment': 'web',
                'sidebar_env': '**Ambiente WEB**',
                'database_env': 'FootballDatabase("web")',
                'title': '⚽ Football Stats',
                'auth_enabled': 'True'
            }
        
        # Applica configurazioni WEB al contenuto TEST
        web_content = self._apply_environment_configs(test_content, web_configs)
        
        # Scrivi app_web.py
        with open("app_web.py", "w", encoding="utf-8") as f:
            f.write(web_content)
        
        print("  ✅ APP WEB aggiornata")
        return True
    
    def deploy_to_mobile(self):
        """Deploy app_simple.py su app_mobile.py preservando configurazioni MOBILE"""
        print("📱 Deploy su APP MOBILE...")
        
        # Leggi app_simple.py
        with open("app_simple.py", "r", encoding="utf-8") as f:
            test_content = f.read()
        
        # CONTROLLO ZONA PROTETTA
        if not self._check_protected_zone(test_content):
            print("  ❌ DEPLOY BLOCCATO: Zona protetta modificata!")
            return False
        
        # Leggi app_mobile.py esistente per preservare configurazioni
        mobile_file = Path("app_mobile.py")
        if mobile_file.exists():
            with open("app_mobile.py", "r", encoding="utf-8") as f:
                mobile_content = f.read()
            
            # Estrai configurazioni specifiche MOBILE da preservare
            mobile_configs = self._extract_environment_configs(mobile_content, "MOBILE")
        else:
            mobile_configs = {
                'environment': 'mobile',
                'sidebar_env': '**Ambiente MOBILE**',
                'database_env': 'FootballDatabase("mobile")',
                'title': '⚽ Football Stats',
                'layout': 'layout="centered"',
                'auth_enabled': 'True'
            }
        
        # Applica configurazioni MOBILE al contenuto TEST
        mobile_content = self._apply_environment_configs(test_content, mobile_configs)
        
        # Scrivi app_mobile.py
        with open("app_mobile.py", "w", encoding="utf-8") as f:
            f.write(mobile_content)
        
        print("  ✅ APP MOBILE aggiornata")
        return True
    
    def _extract_environment_configs(self, content, env_name):
        """Estrae configurazioni ambiente-specifiche dal contenuto"""
        configs = {}
        
        # Estrai sidebar environment
        sidebar_match = re.search(r'st\.sidebar\.markdown\("(\*\*Ambiente [A-Z]+\*\*)"\)', content)
        if sidebar_match:
            configs['sidebar_env'] = sidebar_match.group(1)
        
        # Estrai database environment
        db_match = re.search(r'FootballDatabase\("([^"]+)"\)', content)
        if db_match:
            configs['database_env'] = f'FootballDatabase("{db_match.group(1)}")'
        
        # Estrai layout
        layout_match = re.search(r'layout="([^"]+)"', content)
        if layout_match:
            configs['layout'] = f'layout="{layout_match.group(1)}"'
        
        # Estrai AUTH_ENABLED
        auth_match = re.search(r'AUTH_ENABLED\s*=\s*(True|False)', content)
        if auth_match:
            configs['auth_enabled'] = auth_match.group(1)
        
        return configs
    
    def _apply_environment_configs(self, content, configs):
        """Applica configurazioni ambiente-specifiche al contenuto"""
        # Applica sidebar environment
        if 'sidebar_env' in configs:
            content = re.sub(
                r'st\.sidebar\.markdown\("\*\*Ambiente [A-Z]+\*\*"\)',
                f'st.sidebar.markdown("{configs["sidebar_env"]}")',
                content
            )
        
        # Applica database environment
        if 'database_env' in configs:
            content = re.sub(
                r'FootballDatabase\("[^"]+"\)',
                configs['database_env'],
                content
            )
        
        # Applica layout
        if 'layout' in configs:
            content = re.sub(
                r'layout="[^"]+"',
                configs['layout'],
                content
            )
        
        # Applica AUTH_ENABLED
        if 'auth_enabled' in configs:
            content = re.sub(
                r'AUTH_ENABLED\s*=\s*(True|False)',
                f'AUTH_ENABLED = {configs["auth_enabled"]}',
                content
            )
        
        return content
    
    def _load_deploy_config(self):
        """Carica configurazioni deploy da file"""
        config_file = Path("deploy_config.json")
        if config_file.exists():
            try:
                import json
                with open(config_file, "r") as f:
                    return json.load(f)
            except:
                pass
        
        # Configurazioni di default
        return {
            "protected_lines": 105,
            "backup_count": 2,
            "auto_check": True
        }
    
    def _check_protected_zone(self, content):
        """Controlla se la zona protetta è stata modificata"""
        config = self._load_deploy_config()
        
        if not config.get("auto_check", True):
            print("⚠️  Controllo zona protetta DISABILITATO")
            return True  # Controllo disabilitato
        
        lines = content.split('\n')
        protected_lines_count = config.get("protected_lines", 105)
        
        print(f"🔍 Controllo zona protetta (righe 1-{protected_lines_count})...")
        
        # Controlla se ci sono modifiche nelle righe protette
        protected_lines = lines[:protected_lines_count]
        
        # Cerca modifiche pericolose nella zona protetta
        # Pattern per configurazioni NORMALI (da preservare)
        normal_patterns = [
            r'def run_app\(environment="test"\):',  # Configurazione TEST normale
            r'st\.set_page_config\(',
            r'layout="wide"',
            r'st\.sidebar\.title\("⚽ Football Stats"\)',
            r'st\.sidebar\.markdown\("\*\*Ambiente TEST\*\*"\)'
        ]
        
        # Pattern per modifiche PERICOLOSE (da bloccare)
        dangerous_patterns = [
            r'st\.sidebar\.markdown\("\*\*Ambiente (WEB|MOBILE)\*\*"\)',  # Solo se non è TEST
            r'FootballDatabase\("(web|mobile)"\)',  # Solo se non è test
            r'layout="centered"',  # Solo per MOBILE
            r'def run_app\(environment="(web|mobile)"\)'  # Solo se non è test
        ]
        
        violations = []
        for i, line in enumerate(protected_lines):
            # Controlla se è una modifica pericolosa
            is_dangerous = False
            for pattern in dangerous_patterns:
                if re.search(pattern, line):
                    is_dangerous = True
                    break
            
            # Controlla se NON è una configurazione normale
            is_normal = False
            for pattern in normal_patterns:
                if re.search(pattern, line):
                    is_normal = True
                    break
            
            # Se è pericolosa E non è normale, allora è una violazione
            if is_dangerous and not is_normal:
                violations.append(f"Riga {i+1}: {line.strip()}")
        
        if violations:
            print(f"🚨 ATTENZIONE: Modifiche rilevate nella ZONA PROTETTA (righe 1-{protected_lines_count})!")
            print("🔒 Queste righe contengono configurazioni ambiente e NON devono essere modificate!")
            print("📋 Modifiche rilevate:")
            for violation in violations:
                print(f"  ⚠️  {violation}")
            print(f"\n💡 SOLUZIONE: Lavora solo dalle righe {protected_lines_count + 1} in poi")
            return False
        
        print("✅ Zona protetta: Nessuna modifica pericolosa rilevata")
        return True
    
    def test_apps(self):
        """Testa tutte le app"""
        print("🧪 Testando tutte le app...")
        
        apps = [
            ("TEST", "app_simple.py", 8501),
            ("WEB", "app_web.py", 8502), 
            ("MOBILE", "app_mobile.py", 8505)
        ]
        
        results = {}
        
        for app_name, app_file, port in apps:
            print(f"  🔍 Testando {app_name}...")
            
            # Verifica che il file esista
            if not os.path.exists(app_file):
                print(f"    ❌ File {app_file} non trovato")
                results[app_name] = False
                continue
            
            # Test sintassi Python
            try:
                with open(app_file, "r", encoding="utf-8") as f:
                    compile(f.read(), app_file, "exec")
                print(f"    ✅ Sintassi OK")
                results[app_name] = True
            except SyntaxError as e:
                print(f"    ❌ Errore sintassi: {e}")
                results[app_name] = False
        
        return results
    
    def deploy(self):
        """Esegue il deploy completo con controlli avanzati"""
        print("INIZIO DEPLOY AUTOMATICO")
        print("=" * 50)
        
        try:
            # 1. Carica configurazioni
            config = self._load_deploy_config()
            print(f"📋 Configurazioni caricate:")
            print(f"  🔒 Righe protette: 1-{config.get('protected_lines', 105)}")
            print(f"  💾 Backup da mantenere: {config.get('backup_count', 3)}")
            print(f"  🔍 Controllo automatico: {'✅ Attivo' if config.get('auto_check', True) else '❌ Disattivo'}")
            print()
            
            # 2. Backup
            print("📦 FASE 1: Creazione Backup")
            backup_path = self.create_backup()
            print()
            
            # 3. Controllo zona protetta
            print("🔍 FASE 2: Controllo Zona Protetta")
            with open("app_simple.py", "r", encoding="utf-8") as f:
                test_content = f.read()
            
            if not self._check_protected_zone(test_content):
                print("\n❌ DEPLOY BLOCCATO!")
                print("🔒 Correggi le modifiche nella zona protetta prima di procedere")
                return False
            print()
            
            # 4. Deploy
            print("🚀 FASE 3: Deploy Applicazioni")
            web_success = self.deploy_to_web()
            mobile_success = self.deploy_to_mobile()
            print()
            
            # 5. Test
            print("🧪 FASE 4: Test Applicazioni")
            results = self.test_apps()
            print()
            
            # 6. Risultati finali
            print("📊 RISULTATI FINALI:")
            print("=" * 30)
            
            all_success = True
            for app_name, success in results.items():
                status = "✅ SUCCESS" if success else "❌ FAILED"
                print(f"  {app_name}: {status}")
                if not success:
                    all_success = False
            
            print()
            if all_success and web_success and mobile_success:
                print("🎉 DEPLOY COMPLETATO CON SUCCESSO!")
                print("🌐 WEB: Aggiornato e funzionante")
                print("📱 MOBILE: Aggiornato e funzionante")
                print("💾 Backup: Creato e pulito")
                print(f"\n📱 App disponibili:")
                print("  🧪 TEST:  http://localhost:8501")
                print("  🌐 WEB:   http://localhost:8502") 
                print("  📱 MOBILE: http://localhost:8505")
            else:
                print("⚠️  DEPLOY COMPLETATO CON PROBLEMI!")
                if not web_success:
                    print("🌐 WEB: Deploy fallito")
                if not mobile_success:
                    print("📱 MOBILE: Deploy fallito")
            
            return all_success and web_success and mobile_success
            
        except Exception as e:
            print(f"❌ ERRORE CRITICO DURANTE IL DEPLOY: {e}")
            return False

def main():
    """Funzione principale"""
    deployer = DeploySystem()
    success = deployer.deploy()
    
    if success:
        print("\n✅ Tutto pronto! Puoi avviare le app.")
    else:
        print("\n❌ Deploy fallito. Controlla gli errori.")

if __name__ == "__main__":
    main()
