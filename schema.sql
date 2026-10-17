-- lookup tables
CREATE TABLE project     (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE);
CREATE TABLE condition   (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE);
CREATE TABLE treatment   (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE);
CREATE TABLE sample_type (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE);
CREATE TABLE population  (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE);


CREATE TABLE subject (
    id           INTEGER PRIMARY KEY,
    name         TEXT    NOT NULL UNIQUE,
    project_id   INTEGER NOT NULL REFERENCES project (id),
    condition_id INTEGER NOT NULL REFERENCES condition (id),
    age          INTEGER NOT NULL,
    sex          TEXT    NOT NULL CHECK (sex IN ('M', 'F'))
);

-- unique subject/treatment combo
CREATE TABLE subject_treatment (
    id           INTEGER PRIMARY KEY,
    subject_id   INTEGER NOT NULL REFERENCES subject (id),
    treatment_id INTEGER NOT NULL REFERENCES treatment (id),
    response     TEXT    CHECK (response IN ('yes', 'no')),
    UNIQUE (subject_id, treatment_id)
);

CREATE TABLE sample (
    id                        INTEGER PRIMARY KEY,
    name                      TEXT    NOT NULL UNIQUE,
    subject_treatment_id      INTEGER NOT NULL REFERENCES subject_treatment (id),
    sample_type_id            INTEGER NOT NULL REFERENCES sample_type (id),
    time_from_treatment_start INTEGER NOT NULL
);

CREATE TABLE cell_count (
    sample_id     INTEGER NOT NULL REFERENCES sample (id),
    population_id INTEGER NOT NULL REFERENCES population (id),
    count         INTEGER NOT NULL CHECK (count >= 0),
    PRIMARY KEY (sample_id, population_id)
);
