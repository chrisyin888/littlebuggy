-- Run once on existing Postgres DBs after deploying TrendSnapshot.respiratory_ranking_json.
ALTER TABLE trend_snapshots ADD COLUMN IF NOT EXISTS respiratory_ranking_json TEXT;
