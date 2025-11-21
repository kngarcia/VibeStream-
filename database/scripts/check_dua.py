"""Script para verificar qué hay en la base de datos"""
import psycopg2

DB_CONFIG = {
    'host': 'aws-1-us-east-2.pooler.supabase.com',
    'port': 5432,
    'database': 'postgres',
    'user': 'postgres.nxbdcbqqkqeweosfefqj',
    'password': 'bDHNtUlpLEPHFBFe'
}

conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

print("\n=== CANCIONES CON 'DUA' ===")
cursor.execute("""
    SELECT s.id, s.title, a.artist_name, al.title as album
    FROM music_streaming.songs s
    JOIN music_streaming.albums al ON s.album_id = al.id
    JOIN music_streaming.artists a ON al.artist_id = a.id
    WHERE LOWER(s.title) LIKE '%dua%' 
       OR LOWER(a.artist_name) LIKE '%dua%'
    LIMIT 10
""")

for row in cursor.fetchall():
    print(f"ID: {row[0]}, Canción: {row[1]}, Artista: {row[2]}, Álbum: {row[3]}")

print("\n=== TOTAL DE CANCIONES ===")
cursor.execute("SELECT COUNT(*) FROM music_streaming.songs")
print(f"Total: {cursor.fetchone()[0]}")

print("\n=== ARTISTA 'DUA LIPA' ===")
cursor.execute("""
    SELECT id, artist_name FROM music_streaming.artists
    WHERE LOWER(artist_name) LIKE '%dua%'
""")
for row in cursor.fetchall():
    print(f"ID: {row[0]}, Artista: {row[1]}")

cursor.close()
conn.close()
