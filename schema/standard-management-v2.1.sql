-- VezroCAD Drawing Standards management catalog: DRAFT schema proposal.
-- SQLite is an offline editing/query cache. Published JSON in Git remains authoritative.
-- This is not the DWG geometric database or a client-project data store.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS standard_revision (
  revision_id TEXT PRIMARY KEY,
  semver TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'DRAFT'
    CHECK (status IN ('DRAFT','REVIEW','PUBLISHED','RETIRED')),
  source_commit_sha TEXT,
  sha256_manifest TEXT,
  created_utc TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (semver, revision_id)
);
CREATE TABLE IF NOT EXISTS profession (
  revision_id TEXT NOT NULL,
  profession_id TEXT NOT NULL,
  name TEXT NOT NULL,
  PRIMARY KEY (revision_id, profession_id),
  FOREIGN KEY (revision_id) REFERENCES standard_revision(revision_id)
);
CREATE TABLE IF NOT EXISTS view_preset (
  revision_id TEXT NOT NULL,
  view_id TEXT NOT NULL,
  name TEXT NOT NULL,
  data_json TEXT NOT NULL DEFAULT '{}',
  PRIMARY KEY (revision_id, view_id),
  FOREIGN KEY (revision_id) REFERENCES standard_revision(revision_id)
);
CREATE TABLE IF NOT EXISTS semantic_tag (
  revision_id TEXT NOT NULL,
  tag_id TEXT NOT NULL,
  name TEXT NOT NULL,
  profession_id TEXT,
  PRIMARY KEY (revision_id, tag_id),
  FOREIGN KEY (revision_id) REFERENCES standard_revision(revision_id),
  FOREIGN KEY (revision_id, profession_id) REFERENCES profession(revision_id, profession_id)
);
CREATE TABLE IF NOT EXISTS representation_role (
  revision_id TEXT NOT NULL,
  role_id TEXT NOT NULL,
  name TEXT NOT NULL,
  lineweight_mm REAL,
  PRIMARY KEY (revision_id, role_id),
  FOREIGN KEY (revision_id) REFERENCES standard_revision(revision_id)
);
CREATE TABLE IF NOT EXISTS sheet_type (
  revision_id TEXT NOT NULL,
  sheet_type_id TEXT NOT NULL,
  profession_id TEXT NOT NULL,
  name TEXT NOT NULL,
  base_view_id TEXT,
  preferred_scale INTEGER,
  state TEXT NOT NULL DEFAULT 'PROPOSED',
  PRIMARY KEY (revision_id, sheet_type_id),
  FOREIGN KEY (revision_id, profession_id) REFERENCES profession(revision_id, profession_id),
  FOREIGN KEY (revision_id, base_view_id) REFERENCES view_preset(revision_id, view_id)
);
CREATE TABLE IF NOT EXISTS sheet_expression (
  revision_id TEXT NOT NULL,
  sheet_type_id TEXT NOT NULL,
  tag_id TEXT NOT NULL,
  visibility TEXT NOT NULL
    CHECK (visibility IN ('FOCUS','CONTEXT','HIDE','CONDITIONAL')),
  note TEXT,
  PRIMARY KEY (revision_id, sheet_type_id, tag_id),
  FOREIGN KEY (revision_id, sheet_type_id) REFERENCES sheet_type(revision_id, sheet_type_id),
  FOREIGN KEY (revision_id, tag_id) REFERENCES semantic_tag(revision_id, tag_id)
);
CREATE TABLE IF NOT EXISTS layer_rule (
  revision_id TEXT NOT NULL,
  layer_rule_id TEXT NOT NULL,
  layer_name TEXT NOT NULL,
  default_role_id TEXT,
  PRIMARY KEY (revision_id, layer_rule_id),
  UNIQUE (revision_id, layer_name),
  FOREIGN KEY (revision_id) REFERENCES standard_revision(revision_id),
  FOREIGN KEY (revision_id, default_role_id) REFERENCES representation_role(revision_id, role_id)
);
CREATE TABLE IF NOT EXISTS role_layer_binding (
  revision_id TEXT NOT NULL,
  binding_id TEXT NOT NULL,
  semantic_tag_id TEXT NOT NULL,
  role_id TEXT NOT NULL,
  layer_rule_id TEXT NOT NULL,
  view_id TEXT,
  PRIMARY KEY (revision_id, binding_id),
  FOREIGN KEY (revision_id, semantic_tag_id) REFERENCES semantic_tag(revision_id, tag_id),
  FOREIGN KEY (revision_id, role_id) REFERENCES representation_role(revision_id, role_id),
  FOREIGN KEY (revision_id, layer_rule_id) REFERENCES layer_rule(revision_id, layer_rule_id),
  FOREIGN KEY (revision_id, view_id) REFERENCES view_preset(revision_id, view_id)
);
CREATE TABLE IF NOT EXISTS paper_template (
  revision_id TEXT NOT NULL,
  paper_template_id TEXT NOT NULL,
  paper_id TEXT NOT NULL,
  orientation TEXT NOT NULL CHECK (orientation IN ('landscape','portrait')),
  paper_width_mm REAL NOT NULL CHECK (paper_width_mm>0),
  paper_height_mm REAL NOT NULL CHECK (paper_height_mm>0),
  usable_width_mm REAL NOT NULL CHECK (usable_width_mm>0),
  usable_height_mm REAL NOT NULL CHECK (usable_height_mm>0),
  device_verified INTEGER NOT NULL DEFAULT 0 CHECK (device_verified IN (0,1)),
  PRIMARY KEY (revision_id, paper_template_id),
  FOREIGN KEY (revision_id) REFERENCES standard_revision(revision_id)
);
CREATE TABLE IF NOT EXISTS scale_policy (
  revision_id TEXT NOT NULL,
  policy_id TEXT NOT NULL,
  name TEXT NOT NULL,
  candidates_json TEXT NOT NULL,
  allowed_rotation_json TEXT NOT NULL,
  PRIMARY KEY (revision_id, policy_id),
  FOREIGN KEY (revision_id) REFERENCES standard_revision(revision_id)
);
CREATE TABLE IF NOT EXISTS sheet_scale_binding (
  revision_id TEXT NOT NULL,
  sheet_type_id TEXT NOT NULL,
  policy_id TEXT NOT NULL,
  PRIMARY KEY (revision_id, sheet_type_id),
  FOREIGN KEY (revision_id, sheet_type_id) REFERENCES sheet_type(revision_id, sheet_type_id),
  FOREIGN KEY (revision_id, policy_id) REFERENCES scale_policy(revision_id, policy_id)
);
CREATE TABLE IF NOT EXISTS lineweight_profile (
  revision_id TEXT NOT NULL,
  profile_id TEXT NOT NULL,
  paper_id TEXT NOT NULL,
  scale_denominator INTEGER NOT NULL CHECK (scale_denominator>0),
  PRIMARY KEY (revision_id, profile_id),
  UNIQUE (revision_id, paper_id, scale_denominator),
  FOREIGN KEY (revision_id) REFERENCES standard_revision(revision_id)
);
CREATE TABLE IF NOT EXISTS lineweight_by_role (
  revision_id TEXT NOT NULL,
  profile_id TEXT NOT NULL,
  role_id TEXT NOT NULL,
  paper_width_mm REAL NOT NULL CHECK (paper_width_mm>0),
  PRIMARY KEY (revision_id, profile_id, role_id),
  FOREIGN KEY (revision_id, profile_id) REFERENCES lineweight_profile(revision_id, profile_id),
  FOREIGN KEY (revision_id, role_id) REFERENCES representation_role(revision_id, role_id)
);
CREATE TABLE IF NOT EXISTS print_mode (
  revision_id TEXT NOT NULL,
  mode_id TEXT NOT NULL,
  name TEXT NOT NULL,
  binary_verified INTEGER NOT NULL DEFAULT 0 CHECK (binary_verified IN (0,1)),
  PRIMARY KEY (revision_id, mode_id),
  FOREIGN KEY (revision_id) REFERENCES standard_revision(revision_id)
);
CREATE TABLE IF NOT EXISTS plot_style (
  revision_id TEXT NOT NULL,
  style_name TEXT NOT NULL,
  PRIMARY KEY (revision_id, style_name),
  FOREIGN KEY (revision_id) REFERENCES standard_revision(revision_id)
);
CREATE TABLE IF NOT EXISTS plot_style_color (
  revision_id TEXT NOT NULL,
  mode_id TEXT NOT NULL,
  style_name TEXT NOT NULL,
  output_rgb TEXT NOT NULL,
  preserve_object_lineweight INTEGER NOT NULL DEFAULT 1 CHECK (preserve_object_lineweight=1),
  PRIMARY KEY (revision_id, mode_id, style_name),
  FOREIGN KEY (revision_id, mode_id) REFERENCES print_mode(revision_id, mode_id),
  FOREIGN KEY (revision_id, style_name) REFERENCES plot_style(revision_id, style_name)
);
CREATE TABLE IF NOT EXISTS draw_order_constraint (
  revision_id TEXT NOT NULL,
  constraint_id TEXT NOT NULL,
  view_id TEXT,
  below_role_id TEXT NOT NULL,
  above_role_id TEXT NOT NULL,
  description TEXT,
  PRIMARY KEY (revision_id, constraint_id),
  CHECK (below_role_id <> above_role_id),
  FOREIGN KEY (revision_id, view_id) REFERENCES view_preset(revision_id, view_id),
  FOREIGN KEY (revision_id, below_role_id) REFERENCES representation_role(revision_id, role_id),
  FOREIGN KEY (revision_id, above_role_id) REFERENCES representation_role(revision_id, role_id)
);
CREATE TABLE IF NOT EXISTS change_audit (
  event_id INTEGER PRIMARY KEY AUTOINCREMENT,
  revision_id TEXT NOT NULL,
  actor_label TEXT,
  action TEXT NOT NULL,
  object_ref TEXT NOT NULL,
  change_json TEXT,
  at_utc TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (revision_id) REFERENCES standard_revision(revision_id)
);

CREATE INDEX IF NOT EXISTS idx_sheet_type_profession ON sheet_type(revision_id,profession_id);
CREATE INDEX IF NOT EXISTS idx_sheet_expression_tag ON sheet_expression(revision_id,tag_id);
CREATE INDEX IF NOT EXISTS idx_binding_tag ON role_layer_binding(revision_id,semantic_tag_id);
CREATE INDEX IF NOT EXISTS idx_constraint_view ON draw_order_constraint(revision_id,view_id);

-- The UI must prohibit mutation of a published revision; edit by cloning to DRAFT.
-- The actual release is a Git-reviewed, immutable, versioned JSON bundle with digest.
-- This schema intentionally contains no customer addresses, geometry, or client drawings.
