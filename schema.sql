-- lookup tables keyed by name
CREATE TABLE project     (name TEXT NOT NULL PRIMARY KEY);
CREATE TABLE condition   (name TEXT NOT NULL PRIMARY KEY);
CREATE TABLE treatment   (name TEXT NOT NULL PRIMARY KEY);
CREATE TABLE sample_type (name TEXT NOT NULL PRIMARY KEY);
CREATE TABLE population  (name TEXT NOT NULL PRIMARY KEY);


CREATE TABLE subject (
    id        INTEGER PRIMARY KEY,
    name      TEXT    NOT NULL UNIQUE,
    project   TEXT    NOT NULL REFERENCES project (name) ON UPDATE CASCADE,
    condition TEXT    NOT NULL REFERENCES condition (name) ON UPDATE CASCADE,
    age       INTEGER NOT NULL,
    sex       TEXT    NOT NULL CHECK (sex IN ('M', 'F'))
);

-- unique subject/treatment combo
-- i sort of just did this because if we're trying to make it iteratable on,
-- in many clinical trials (at least in my experience, eg move-to events)
-- a second drug might be given, even though that's not the case in this csv
-- it only adds like a single join so i figured why not, but if all we care about is the data in the csv then it would be better 
-- to drop this table and just have sample point straight to subject
CREATE TABLE subject_treatment (
    id         INTEGER PRIMARY KEY,
    subject_id INTEGER NOT NULL REFERENCES subject (id),
    treatment  TEXT    NOT NULL REFERENCES treatment (name) ON UPDATE CASCADE,
    response   TEXT    CHECK (response IN ('yes', 'no')),
    UNIQUE (subject_id, treatment)
);

CREATE TABLE sample (
    id                        INTEGER PRIMARY KEY,
    name                      TEXT    NOT NULL UNIQUE,
    subject_treatment_id      INTEGER NOT NULL REFERENCES subject_treatment (id),
    sample_type               TEXT    NOT NULL REFERENCES sample_type (name) ON UPDATE CASCADE,
    time_from_treatment_start INTEGER NOT NULL
);

CREATE TABLE cell_count (
    sample_id  INTEGER NOT NULL REFERENCES sample (id),
    population TEXT    NOT NULL REFERENCES population (name) ON UPDATE CASCADE,
    count      INTEGER NOT NULL CHECK (count >= 0),
    PRIMARY KEY (sample_id, population)
);
