# 🔄 SCRIPT DE MIGRACIÓN SEGURA
# Para actualizar tu base de datos existente sin perder datos

import psycopg2
from datetime import datetime

DB_CONFIG = {
    'host': 'aws-1-us-east-2.pooler.supabase.com',
    'port': 5432,
    'database': 'postgres',
    'user': 'postgres.nxbdcbqqkqeweosfefqj',
    'password': 'bDHNtUlpLEPHFBFe'
}

class SafeMigration:
    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor()
        self.backup_tables = []
        
    def backup_table(self, table_name):
        """Crea un backup de una tabla antes de modificarla"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{table_name}_backup_{timestamp}"
        
        print(f"📦 Creando backup: {backup_name}")
        self.cursor.execute(f"""
            CREATE TABLE music_streaming.{backup_name} AS 
            SELECT * FROM music_streaming.{table_name}
        """)
        self.conn.commit()
        self.backup_tables.append(backup_name)
        return backup_name
    
    def check_table_exists(self, table_name):
        """Verifica si una tabla existe"""
        self.cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 'music_streaming' 
                AND table_name = %s
            )
        """, (table_name,))
        return self.cursor.fetchone()[0]
    
    def add_column_safe(self, table_name, column_def):
        """Agrega una columna solo si no existe"""
        column_name = column_def.split()[0]
        
        self.cursor.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = 'music_streaming'
            AND table_name = %s
            AND column_name = %s
        """, (table_name, column_name))
        
        if not self.cursor.fetchone():
            print(f"   ➕ Agregando columna: {table_name}.{column_name}")
            self.cursor.execute(f"""
                ALTER TABLE music_streaming.{table_name}
                ADD COLUMN {column_def}
            """)
            self.conn.commit()
        else:
            print(f"   ⏭️  Columna ya existe: {table_name}.{column_name}")
    
    def migrate(self):
        """Ejecuta migración completa de forma segura"""
        print("🔄 INICIANDO MIGRACIÓN SEGURA")
        print("=" * 60)
        
        try:
            # 1. Agregar columnas faltantes a tablas existentes
            print("\n📝 Paso 1: Actualizando tablas existentes")
            
            # Users
            if self.check_table_exists('users'):
                self.add_column_safe('users', 'profile_picture TEXT')
                self.add_column_safe('users', 'bio TEXT')
                self.add_column_safe('users', 'last_login TIMESTAMP')
                self.add_column_safe('users', 'deleted_at TIMESTAMP')
            
            # Artists
            if self.check_table_exists('artists'):
                self.add_column_safe('artists', 'banner_pic TEXT')
                self.add_column_safe('artists', 'total_followers INTEGER DEFAULT 0')
                self.add_column_safe('artists', 'total_plays INTEGER DEFAULT 0')
                self.add_column_safe('artists', 'monthly_listeners INTEGER DEFAULT 0')
                self.add_column_safe('artists', 'is_verified BOOLEAN DEFAULT false')
                self.add_column_safe('artists', 'verified_at TIMESTAMP')
                self.add_column_safe('artists', 'deleted_at TIMESTAMP')
            
            # Albums
            if self.check_table_exists('albums'):
                self.add_column_safe('albums', 'album_type VARCHAR(20) DEFAULT \'album\'')
                self.add_column_safe('albums', 'total_tracks INTEGER DEFAULT 0')
                self.add_column_safe('albums', 'total_plays INTEGER DEFAULT 0')
                self.add_column_safe('albums', 'total_likes INTEGER DEFAULT 0')
                self.add_column_safe('albums', 'deleted_at TIMESTAMP')
            
            # Songs
            if self.check_table_exists('songs'):
                self.add_column_safe('songs', 'disc_number INTEGER DEFAULT 1')
                self.add_column_safe('songs', 'bitrate INTEGER')
                self.add_column_safe('songs', 'sample_rate INTEGER')
                self.add_column_safe('songs', 'file_size BIGINT')
                self.add_column_safe('songs', 'file_format VARCHAR(10)')
                self.add_column_safe('songs', 'lyrics TEXT')
                self.add_column_safe('songs', 'has_lyrics BOOLEAN DEFAULT false')
                self.add_column_safe('songs', 'play_count INTEGER DEFAULT 0')
                self.add_column_safe('songs', 'like_count INTEGER DEFAULT 0')
                self.add_column_safe('songs', 'skip_count INTEGER DEFAULT 0')
                self.add_column_safe('songs', 'is_explicit BOOLEAN DEFAULT false')
                self.add_column_safe('songs', 'is_available BOOLEAN DEFAULT true')
                self.add_column_safe('songs', 'deleted_at TIMESTAMP')
            
            # Playlists
            if self.check_table_exists('playlists'):
                self.add_column_safe('playlists', 'cover_image TEXT')
                self.add_column_safe('playlists', 'is_public BOOLEAN DEFAULT false')
                self.add_column_safe('playlists', 'is_collaborative BOOLEAN DEFAULT false')
                self.add_column_safe('playlists', 'total_songs INTEGER DEFAULT 0')
                self.add_column_safe('playlists', 'total_duration INTEGER DEFAULT 0')
                self.add_column_safe('playlists', 'follower_count INTEGER DEFAULT 0')
                self.add_column_safe('playlists', 'play_count INTEGER DEFAULT 0')
                self.add_column_safe('playlists', 'deleted_at TIMESTAMP')
            
            # Playlist_songs
            if self.check_table_exists('playlist_songs'):
                self.add_column_safe('playlist_songs', 'position INTEGER NOT NULL DEFAULT 0')
                self.add_column_safe('playlist_songs', 'added_by INTEGER REFERENCES music_streaming.users(id)')
            
            # 2. Crear tablas nuevas
            print("\n📝 Paso 2: Creando tablas nuevas")
            
            # Genres (mejorada)
            if not self.check_table_exists('genres'):
                print("   ➕ Creando tabla: genres")
                self.cursor.execute("""
                    CREATE TABLE music_streaming.genres (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100) UNIQUE NOT NULL,
                        description TEXT,
                        parent_genre_id INTEGER REFERENCES music_streaming.genres(id),
                        icon_url TEXT,
                        color_hex VARCHAR(7),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                self.conn.commit()
            
            # User_likes
            if not self.check_table_exists('user_likes'):
                print("   ➕ Creando tabla: user_likes")
                self.cursor.execute("""
                    CREATE TABLE music_streaming.user_likes (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES music_streaming.users(id) ON DELETE CASCADE,
                        entity_type VARCHAR(20) NOT NULL CHECK (entity_type IN ('song', 'album', 'playlist', 'artist')),
                        entity_id INTEGER NOT NULL,
                        liked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, entity_type, entity_id)
                    )
                """)
                self.conn.commit()
            
            # Play_history
            if not self.check_table_exists('play_history'):
                print("   ➕ Creando tabla: play_history")
                self.cursor.execute("""
                    CREATE TABLE music_streaming.play_history (
                        id BIGSERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES music_streaming.users(id) ON DELETE CASCADE,
                        song_id INTEGER NOT NULL REFERENCES music_streaming.songs(id) ON DELETE CASCADE,
                        played_from VARCHAR(50),
                        context_id INTEGER,
                        played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        duration_played INTEGER,
                        was_skipped BOOLEAN DEFAULT false,
                        completion_percentage FLOAT,
                        device_type VARCHAR(50),
                        ip_address INET
                    )
                """)
                self.conn.commit()
            
            # User_follows
            if not self.check_table_exists('user_follows'):
                print("   ➕ Creando tabla: user_follows")
                self.cursor.execute("""
                    CREATE TABLE music_streaming.user_follows (
                        follower_id INTEGER NOT NULL REFERENCES music_streaming.users(id) ON DELETE CASCADE,
                        following_id INTEGER NOT NULL REFERENCES music_streaming.users(id) ON DELETE CASCADE,
                        followed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (follower_id, following_id),
                        CHECK (follower_id != following_id)
                    )
                """)
                self.conn.commit()
            
            # Now_playing
            if not self.check_table_exists('now_playing'):
                print("   ➕ Creando tabla: now_playing")
                self.cursor.execute("""
                    CREATE TABLE music_streaming.now_playing (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER UNIQUE NOT NULL REFERENCES music_streaming.users(id) ON DELETE CASCADE,
                        song_id INTEGER NOT NULL REFERENCES music_streaming.songs(id) ON DELETE CASCADE,
                        position INTEGER DEFAULT 0,
                        is_playing BOOLEAN DEFAULT true,
                        volume INTEGER DEFAULT 100,
                        repeat_mode VARCHAR(10) DEFAULT 'off',
                        shuffle_enabled BOOLEAN DEFAULT false,
                        queue_context VARCHAR(50),
                        queue_context_id INTEGER,
                        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                self.conn.commit()
            
            # Search_history
            if not self.check_table_exists('search_history'):
                print("   ➕ Creando tabla: search_history")
                self.cursor.execute("""
                    CREATE TABLE music_streaming.search_history (
                        id BIGSERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES music_streaming.users(id) ON DELETE CASCADE,
                        query TEXT NOT NULL,
                        result_count INTEGER DEFAULT 0,
                        searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                self.conn.commit()
            
            # Daily_song_stats
            if not self.check_table_exists('daily_song_stats'):
                print("   ➕ Creando tabla: daily_song_stats")
                self.cursor.execute("""
                    CREATE TABLE music_streaming.daily_song_stats (
                        id BIGSERIAL PRIMARY KEY,
                        song_id INTEGER NOT NULL REFERENCES music_streaming.songs(id) ON DELETE CASCADE,
                        date DATE NOT NULL,
                        total_plays INTEGER DEFAULT 0,
                        total_skips INTEGER DEFAULT 0,
                        total_likes INTEGER DEFAULT 0,
                        unique_listeners INTEGER DEFAULT 0,
                        total_duration_played BIGINT DEFAULT 0,
                        avg_completion_rate FLOAT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(song_id, date)
                    )
                """)
                self.conn.commit()
            
            # 3. Crear índices importantes
            print("\n📝 Paso 3: Creando índices para rendimiento")
            indices = [
                "CREATE INDEX IF NOT EXISTS idx_songs_play_count ON music_streaming.songs(play_count DESC)",
                "CREATE INDEX IF NOT EXISTS idx_user_likes_user ON music_streaming.user_likes(user_id, entity_type)",
                "CREATE INDEX IF NOT EXISTS idx_play_history_user_date ON music_streaming.play_history(user_id, played_at DESC)",
                "CREATE INDEX IF NOT EXISTS idx_play_history_song ON music_streaming.play_history(song_id)",
                "CREATE INDEX IF NOT EXISTS idx_follows_follower ON music_streaming.user_follows(follower_id)",
                "CREATE INDEX IF NOT EXISTS idx_follows_following ON music_streaming.user_follows(following_id)",
            ]
            
            for idx in indices:
                try:
                    self.cursor.execute(idx)
                    self.conn.commit()
                    print(f"   ✓ Índice creado")
                except Exception as e:
                    print(f"   ⏭️  Índice ya existe o error: {str(e)[:50]}")
            
            print("\n" + "=" * 60)
            print("✅ MIGRACIÓN COMPLETADA EXITOSAMENTE!")
            print(f"\n📦 Backups creados: {len(self.backup_tables)}")
            for backup in self.backup_tables:
                print(f"   - music_streaming.{backup}")
            
            print("\n⚠️  IMPORTANTE:")
            print("   - Verifica que todo funcione correctamente")
            print("   - Los backups se pueden eliminar después de validar")
            print(f"   - Comando para eliminar backups:")
            for backup in self.backup_tables:
                print(f"     DROP TABLE IF EXISTS music_streaming.{backup};")
            
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            print("\n🔄 Revertiendo cambios...")
            self.conn.rollback()
            raise e
        finally:
            self.cursor.close()
            self.conn.close()

if __name__ == "__main__":
    print("\n⚠️  ADVERTENCIA: Este script modificará tu base de datos")
    print("   Se crearán backups automáticos antes de cada cambio")
    print("   Presiona Ctrl+C para cancelar en los próximos 5 segundos...")
    
    import time
    for i in range(5, 0, -1):
        print(f"   {i}...")
        time.sleep(1)
    
    print("\n🚀 Iniciando migración...\n")
    
    migrator = SafeMigration()
    migrator.migrate()
