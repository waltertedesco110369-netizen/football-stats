#!/bin/bash

# Crea il database se non esiste
python -c "
from database import FootballDatabase
import os

# Crea database mobile
db_mobile = FootballDatabase(environment='mobile')
print('✅ Database mobile inizializzato')

# Crea database web se serve
if not os.path.exists('football_stats_web.db'):
    db_web = FootballDatabase(environment='web')
    print('✅ Database web inizializzato')

print('✅ Setup completato')
"

