CREATE TABLE IF NOT EXISTS patients (
  id            SERIAL PRIMARY KEY,
  patient_code  TEXT NOT NULL,
  age           INT  NOT NULL,
  bmi           NUMERIC(4,1) NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO patients (patient_code, age, bmi, created_at)
SELECT
  'P' || lpad(gs::text, 5, '0')                       AS patient_code,
  (20 + (random() * 60))::int                         AS age,
  round((18 + random() * 20)::numeric, 1)             AS bmi,
  now() - (random() * interval '365 days')            AS created_at
FROM generate_series(1, 50) AS gs;