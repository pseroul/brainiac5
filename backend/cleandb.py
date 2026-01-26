import sqlite3

def fix_and_clean_database(db_name):
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # 1. Désactiver les contraintes pour manipuler les structures
        cursor.execute("PRAGMA foreign_keys = OFF;")

        # --- NETTOYAGE DES TABLES PRINCIPALES ---
        # On utilise OR REPLACE au cas où "Tag " et "Tag" existent déjà tous les deux
        tables_to_clean = {
            "tags": ["name"],
            "data": ["name", "description", "tags"]
        }

        for table, columns in tables_to_clean.items():
            cols_sql = ", ".join([f"{c} = TRIM({c})" for c in columns])
            try:
                cursor.execute(f"UPDATE OR REPLACE {table} SET {cols_sql};")
            except sqlite3.Error as e:
                print(f"Note sur {table}: {e}")

        # --- NETTOYAGE DE LA TABLE RELATION (Celle qui bloque) ---
        # Stratégie : Créer une table temporaire propre, puis remplacer l'ancienne
        print("Nettoyage et fusion des doublons dans la table 'relation'...")
        
        cursor.execute("CREATE TABLE relation_backup AS SELECT * FROM relation WHERE 1=0;") # Copie structure
        
        # On insère les données en appliquant TRIM et en ignorant les doublons créés
        cursor.execute("""
            INSERT OR IGNORE INTO relation_backup (data_name, tag_name)
            SELECT TRIM(data_name), TRIM(tag_name) FROM relation;
        """)

        # On remplace l'ancienne table par la nouvelle nettoyée
        cursor.execute("DROP TABLE relation;")
        cursor.execute("""
            CREATE TABLE relation (
                data_name TEXT,
                tag_name TEXT,
                PRIMARY KEY (data_name, tag_name),
                FOREIGN KEY (data_name) REFERENCES data(name),
                FOREIGN KEY (tag_name) REFERENCES tags(name)
            );
        """)
        cursor.execute("INSERT INTO relation SELECT * FROM relation_backup;")
        cursor.execute("DROP TABLE relation_backup;")

        # 2. Finalisation
        conn.commit()
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        # Vérification finale
        cursor.execute("PRAGMA foreign_key_check;")
        if not cursor.fetchall():
            print("✅ Succès ! Les lignes ont été fusionnées et nettoyées.")
        else:
            print("⚠️ Le nettoyage est fait, mais certaines relations pointent vers des noms inexistants.")

    except sqlite3.Error as e:
        print(f"Erreur critique : {e}")
        conn.rollback()
    finally:
        conn.close()

def debug_and_clean_relation(db_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    print("Analyse des doublons potentiels dans la table 'relation'...")
    
    # Cette requête trouve les lignes qui, une fois nettoyées (TRIM), 
    # créeraient des doublons dans la table relation.
    cursor.execute("""
        SELECT data_name, tag_name, COUNT(*)
        FROM (
            SELECT TRIM(data_name) as data_name, TRIM(tag_name) as tag_name 
            FROM relation
        )
        GROUP BY data_name, tag_name
        HAVING COUNT(*) > 1
    """)
    
    doublons = cursor.fetchall()
    
    if doublons:
        print("❌ Erreur d'intégrité détectée. Voici les lignes qui causent le conflit :")
        for d in doublons:
            print(f"Le couple (Data: '{d[0]}', Tag: '{d[1]}') apparaît {d[2]} fois après nettoyage.")
        print("\nSolution : Supprimez manuellement les doublons ou fusionnez-les avant de relancer le script.")
    else:
        print("✅ Aucun doublon détecté. Tentative de mise à jour...")
        try:
            cursor.execute("PRAGMA foreign_keys = OFF;")
            cursor.execute("UPDATE relation SET data_name = TRIM(data_name), tag_name = TRIM(tag_name);")
            conn.commit()
            print("Mise à jour réussie.")
        except sqlite3.IntegrityError as e:
            print(f"Erreur persistante : {e}")
            
    conn.close()

def check_orphans(db_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    print("--- Recherche d'orphelins dans la table 'relation' ---")

    # Chercher les data_name qui n'existent pas dans la table data
    cursor.execute("""
        SELECT data_name FROM relation 
        WHERE data_name NOT IN (SELECT name FROM data)
    """)
    orphan_data = cursor.fetchall()
    
    # Chercher les tag_name qui n'existent pas dans la table tags
    cursor.execute("""
        SELECT DISTINCT tag_name FROM relation 
        WHERE tag_name NOT IN (SELECT name FROM tags)
    """)
    orphan_tags = cursor.fetchall()

    if orphan_data:
        print(f"❌ {len(orphan_data)} lignes pointent vers des DATA inexistants :")
        for d in orphan_data: print(f"   - '{d[0]}'")
    
    if orphan_tags:
        print(f"❌ {len(orphan_tags)} lignes pointent vers des TAGS inexistants :")
        for t in orphan_tags: print(f"   - '{t[0]}'")

    if not orphan_data and not orphan_tags:
        print("✅ Aucune erreur d'intégrité trouvée.")

    conn.close()

def add_idea(db_name) -> None:
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    name = "Jevon's paradox"
    description = 'description'
    cursor.execute(
        "INSERT INTO data (name, description) VALUES (?, ?)",
        (name, description)
    )
    conn.commit()

if __name__ == "__main__":
    # Remplace par le nom de ton fichier
    NAME_DB = "backend/data/knowledge.db" 
    fix_and_clean_database(NAME_DB)