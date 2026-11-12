-- VezroCAD project SHEET INDEX schema proposal, separate from standards DB.
-- Never commit a populated project DB or client data to this public repository.
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS project_document(
  project_uid TEXT PRIMARY KEY,
  standard_revision_id TEXT NOT NULL,
  standard_bundle_sha256 TEXT NOT NULL,
  created_utc TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS project_object(
  project_uid TEXT NOT NULL,
  object_uid TEXT NOT NULL,
  semantic_type TEXT NOT NULL,
  drawing_uid TEXT NOT NULL,
  content_digest TEXT,
  PRIMARY KEY(project_uid,object_uid),
  FOREIGN KEY(project_uid) REFERENCES project_document(project_uid) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS sheet_instance(
  project_uid TEXT NOT NULL,
  sheet_uid TEXT NOT NULL,
  sheet_type_id TEXT NOT NULL,
  layout_template_id TEXT,
  display_sheet_no TEXT,
  sheet_title TEXT NOT NULL,
  revision_label TEXT NOT NULL DEFAULT 'A',
  status TEXT NOT NULL DEFAULT 'DRAFT' CHECK(status IN ('DRAFT','REVIEW','ISSUED','SUPERSEDED')),
  PRIMARY KEY(project_uid,sheet_uid),
  FOREIGN KEY(project_uid) REFERENCES project_document(project_uid) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS viewport_instance(
  project_uid TEXT NOT NULL,
  viewport_uid TEXT NOT NULL,
  sheet_uid TEXT NOT NULL,
  layout_slot_id TEXT NOT NULL,
  source_view_id TEXT NOT NULL,
  scale_denominator INTEGER NOT NULL CHECK(scale_denominator>0),
  rotation_degrees INTEGER NOT NULL DEFAULT 0 CHECK(rotation_degrees IN (0,90)),
  is_scale_locked INTEGER NOT NULL DEFAULT 1 CHECK(is_scale_locked IN (0,1)),
  display_label TEXT,
  viewport_metadata_json TEXT NOT NULL DEFAULT '{}',
  PRIMARY KEY(project_uid,viewport_uid),
  FOREIGN KEY(project_uid,sheet_uid) REFERENCES sheet_instance(project_uid,sheet_uid) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS sheet_object_dependency(
  project_uid TEXT NOT NULL,
  sheet_uid TEXT NOT NULL,
  object_uid TEXT NOT NULL,
  impact_policy TEXT NOT NULL CHECK(impact_policy IN ('AUTO','REGENERATE','REVIEW')),
  reason TEXT NOT NULL,
  PRIMARY KEY(project_uid,sheet_uid,object_uid,reason),
  FOREIGN KEY(project_uid,sheet_uid) REFERENCES sheet_instance(project_uid,sheet_uid) ON DELETE CASCADE,
  FOREIGN KEY(project_uid,object_uid) REFERENCES project_object(project_uid,object_uid) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS sheet_reference(
  project_uid TEXT NOT NULL,
  source_sheet_uid TEXT NOT NULL,
  reference_uid TEXT NOT NULL,
  target_sheet_uid TEXT NOT NULL,
  reference_type TEXT NOT NULL CHECK(reference_type IN ('ELEVATION','DETAIL','SECTION','CALLOUT')),
  PRIMARY KEY(project_uid,source_sheet_uid,reference_uid),
  FOREIGN KEY(project_uid,source_sheet_uid) REFERENCES sheet_instance(project_uid,sheet_uid) ON DELETE CASCADE,
  FOREIGN KEY(project_uid,target_sheet_uid) REFERENCES sheet_instance(project_uid,sheet_uid)
);
CREATE INDEX IF NOT EXISTS idx_project_sheet_number ON sheet_instance(project_uid,display_sheet_no);
CREATE INDEX IF NOT EXISTS idx_viewport_sheet ON viewport_instance(project_uid,sheet_uid);
CREATE INDEX IF NOT EXISTS idx_dependency_object ON sheet_object_dependency(project_uid,object_uid);
-- Stable UID survives reordering; display_sheet_no is a changeable issued label.
-- A DWG Handle is a local locator, NOT a cross-drawing stable UID; use immutable object_uid.
