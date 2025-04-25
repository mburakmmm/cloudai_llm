-- Mevcut tabloları sil
DROP TABLE IF EXISTS training_data CASCADE;
DROP TABLE IF EXISTS ai_intent_groups CASCADE;
DROP TABLE IF EXISTS intent_analytics CASCADE;
DROP TABLE IF EXISTS exports CASCADE;

-- Vector uzantısını etkinleştir
CREATE EXTENSION IF NOT EXISTS vector;

-- training_data tablosunu oluştur
CREATE TABLE IF NOT EXISTS training_data (
    id BIGSERIAL PRIMARY KEY,
    prompt TEXT NOT NULL,
    response TEXT NOT NULL,
    embedding VECTOR(384),
    intent TEXT,
    tags TEXT[],
    priority INTEGER DEFAULT 1,
    context_message TEXT,
    category TEXT DEFAULT 'genel',
    confidence_score FLOAT DEFAULT 1.0,
    usage_count INTEGER DEFAULT 0,
    last_used TIMESTAMP WITH TIME ZONE,
    avg_match_score FLOAT DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Intent grupları tablosunu oluştur
CREATE TABLE IF NOT EXISTS ai_intent_groups (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    intents TEXT[],
    priority INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Intent analizi tablosunu oluştur
CREATE TABLE IF NOT EXISTS intent_analytics (
    id BIGSERIAL PRIMARY KEY,
    intent TEXT NOT NULL,
    count INTEGER DEFAULT 0,
    avg_confidence FLOAT DEFAULT 0.0,
    last_used TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Dışa aktarma tablosunu oluştur
CREATE TABLE IF NOT EXISTS exports (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    file_path TEXT,
    file_type TEXT,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- RLS politikalarını ayarla
ALTER TABLE training_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_intent_groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE intent_analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE exports ENABLE ROW LEVEL SECURITY;

-- Anonim kullanıcılar için okuma izinleri
CREATE POLICY "Anonim okuma - training_data" ON training_data FOR SELECT TO anon USING (true);
CREATE POLICY "Anonim okuma - intent_groups" ON ai_intent_groups FOR SELECT TO anon USING (true);
CREATE POLICY "Anonim okuma - analytics" ON intent_analytics FOR SELECT TO anon USING (true);
CREATE POLICY "Anonim okuma - exports" ON exports FOR SELECT TO anon USING (true);

-- Anonim kullanıcılar için yazma izinleri
CREATE POLICY "Anonim yazma - training_data" ON training_data FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "Anonim yazma - intent_groups" ON ai_intent_groups FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "Anonim yazma - analytics" ON intent_analytics FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "Anonim yazma - exports" ON exports FOR INSERT TO anon WITH CHECK (true);

-- Anonim kullanıcılar için güncelleme izinleri
CREATE POLICY "Anonim güncelleme - training_data" ON training_data FOR UPDATE TO anon USING (true) WITH CHECK (true);
CREATE POLICY "Anonim güncelleme - intent_groups" ON ai_intent_groups FOR UPDATE TO anon USING (true) WITH CHECK (true);
CREATE POLICY "Anonim güncelleme - analytics" ON intent_analytics FOR UPDATE TO anon USING (true) WITH CHECK (true);
CREATE POLICY "Anonim güncelleme - exports" ON exports FOR UPDATE TO anon USING (true) WITH CHECK (true);

-- Anonim kullanıcılar için silme izinleri
CREATE POLICY "Anonim silme - training_data" ON training_data FOR DELETE TO anon USING (true);
CREATE POLICY "Anonim silme - intent_groups" ON ai_intent_groups FOR DELETE TO anon USING (true);
CREATE POLICY "Anonim silme - analytics" ON intent_analytics FOR DELETE TO anon USING (true);
CREATE POLICY "Anonim silme - exports" ON exports FOR DELETE TO anon USING (true);

-- Otomatik güncelleme fonksiyonu
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggerları oluştur
CREATE TRIGGER update_training_data_updated_at
    BEFORE UPDATE ON training_data
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_intent_groups_updated_at
    BEFORE UPDATE ON ai_intent_groups
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_analytics_updated_at
    BEFORE UPDATE ON intent_analytics
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_exports_updated_at
    BEFORE UPDATE ON exports
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Vektör indeksi oluştur
CREATE INDEX IF NOT EXISTS training_data_embedding_idx 
ON training_data 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100); 