// LiveQuest graph constraints. Applied idempotently on startup.
// One uniqueness constraint per node label, keyed on the canonical `key`
// property (see GraphNode.key). This is what makes MERGE-by-key idempotent.

CREATE CONSTRAINT disease_key IF NOT EXISTS FOR (n:Disease) REQUIRE n.key IS UNIQUE;
CREATE CONSTRAINT gene_key IF NOT EXISTS FOR (n:Gene) REQUIRE n.key IS UNIQUE;
CREATE CONSTRAINT protein_key IF NOT EXISTS FOR (n:Protein) REQUIRE n.key IS UNIQUE;
CREATE CONSTRAINT drug_key IF NOT EXISTS FOR (n:Drug) REQUIRE n.key IS UNIQUE;
CREATE CONSTRAINT ae_key IF NOT EXISTS FOR (n:AdverseEvent) REQUIRE n.key IS UNIQUE;
CREATE CONSTRAINT trial_key IF NOT EXISTS FOR (n:Trial) REQUIRE n.key IS UNIQUE;
