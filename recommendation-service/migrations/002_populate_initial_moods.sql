-- Script to populate initial mood data for existing songs
-- This analyzes existing songs and assigns moods based on their genres

-- Insert mood features for all songs based on genre
INSERT INTO music_streaming.track_mood_features (song_id, primary_mood, mood_confidence, mood_tags, energy, valence, tempo)
SELECT 
    s.id,
    CASE 
        -- Chill moods
        WHEN LOWER(g.name) LIKE '%lofi%' OR LOWER(g.name) LIKE '%lo-fi%' THEN 'chill'
        WHEN LOWER(g.name) LIKE '%chill%' THEN 'chill'
        WHEN LOWER(g.name) LIKE '%ambient%' THEN 'chill'
        WHEN LOWER(g.name) LIKE '%classical%' THEN 'chill'
        WHEN LOWER(g.name) LIKE '%acoustic%' THEN 'chill'
        WHEN LOWER(g.name) LIKE '%jazz%' THEN 'chill'
        WHEN LOWER(g.name) LIKE '%bossa%' THEN 'chill'
        WHEN LOWER(g.name) LIKE '%r&b%' OR LOWER(g.name) LIKE '%rnb%' THEN 'chill'
        WHEN LOWER(g.name) LIKE '%reggae%' THEN 'chill'
        
        -- Intense moods
        WHEN LOWER(g.name) LIKE '%metal%' THEN 'intense'
        WHEN LOWER(g.name) LIKE '%punk%' THEN 'intense'
        WHEN LOWER(g.name) LIKE '%hardcore%' THEN 'intense'
        WHEN LOWER(g.name) LIKE '%thrash%' THEN 'intense'
        WHEN LOWER(g.name) LIKE '%trap%' THEN 'intense'
        
        -- Energetic moods
        WHEN LOWER(g.name) LIKE '%rock%' THEN 'energetic'
        WHEN LOWER(g.name) LIKE '%electronic%' THEN 'energetic'
        WHEN LOWER(g.name) LIKE '%house%' THEN 'energetic'
        WHEN LOWER(g.name) LIKE '%techno%' THEN 'energetic'
        WHEN LOWER(g.name) LIKE '%edm%' THEN 'energetic'
        WHEN LOWER(g.name) LIKE '%electro%' THEN 'energetic'
        WHEN LOWER(g.name) LIKE '%drum%' THEN 'energetic'
        WHEN LOWER(g.name) LIKE '%dubstep%' THEN 'energetic'
        WHEN LOWER(g.name) LIKE '%hip%hop%' OR LOWER(g.name) LIKE '%hip-hop%' THEN 'energetic'
        WHEN LOWER(g.name) LIKE '%rap%' THEN 'energetic'
        
        -- Happy moods
        WHEN LOWER(g.name) LIKE '%pop%' THEN 'happy'
        WHEN LOWER(g.name) LIKE '%dance%' THEN 'happy'
        WHEN LOWER(g.name) LIKE '%reggaeton%' THEN 'happy'
        WHEN LOWER(g.name) LIKE '%latin%' THEN 'happy'
        WHEN LOWER(g.name) LIKE '%salsa%' THEN 'happy'
        WHEN LOWER(g.name) LIKE '%country%' THEN 'happy'
        WHEN LOWER(g.name) LIKE '%gospel%' THEN 'happy'
        WHEN LOWER(g.name) LIKE '%disco%' THEN 'happy'
        WHEN LOWER(g.name) LIKE '%funk%' THEN 'happy'
        
        -- Sad/Melancholic moods
        WHEN LOWER(g.name) LIKE '%blues%' THEN 'sad'
        WHEN LOWER(g.name) LIKE '%soul%' THEN 'melancholic'
        WHEN LOWER(g.name) LIKE '%indie%' THEN 'melancholic'
        WHEN LOWER(g.name) LIKE '%folk%' THEN 'melancholic'
        WHEN LOWER(g.name) LIKE '%alternative%' THEN 'melancholic'
        WHEN LOWER(g.name) LIKE '%bachata%' THEN 'melancholic'
        
        -- Default
        ELSE 'happy'
    END as primary_mood,
    0.7 as mood_confidence,
    CASE 
        WHEN LOWER(g.name) LIKE '%lofi%' THEN '["chill", "relaxing", "study"]'::jsonb
        WHEN LOWER(g.name) LIKE '%metal%' THEN '["intense", "powerful", "aggressive"]'::jsonb
        WHEN LOWER(g.name) LIKE '%pop%' THEN '["happy", "upbeat", "positive"]'::jsonb
        WHEN LOWER(g.name) LIKE '%jazz%' THEN '["chill", "sophisticated", "smooth"]'::jsonb
        ELSE '["neutral"]'::jsonb
    END as mood_tags,
    0.5 as energy,
    0.5 as valence,
    120.0 as tempo
FROM music_streaming.songs s
LEFT JOIN music_streaming.genres g ON s.genre_id = g.id
WHERE NOT EXISTS (
    SELECT 1 FROM music_streaming.track_mood_features tmf WHERE tmf.song_id = s.id
)
ON CONFLICT (song_id) DO NOTHING;

-- Report results
DO $$
DECLARE
    row_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO row_count FROM music_streaming.track_mood_features;
    RAISE NOTICE 'Initial mood data populated! Total tracks with mood: %', row_count;
END $$;
