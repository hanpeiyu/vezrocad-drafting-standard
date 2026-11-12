-- VezroCAD proposed PROJECT INDEX, separate from immutable STANDARD catalog.
-- Physical paper sheet != logical drawing type/content != CAD viewport.
-- Store no real client data in the public standards repo.
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
  source_dwg_uid TEXT NOT NULL,
  content_digest TEXT,
  PRIMARY KEY(project_uid,object_uid),
  FOREIGN KEY(project_uid) REFERENCES project_document(project_uid) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS drawing_instance(
  project_uid TEXT NOT NULL,
  drawing_uid TEXT NOT NULL,
  drawing_type_id TEXT NOT NULL,
  source_view_id TEXT,
  target_ref_json TEXT NOT NULL DEFAULT '{}',
  drawing_title TEXT NOT NULL,
  PRIMARY KEY(project_uid,drawing_uid),
  FOREIGN KEY(project_uid) REFERENCES project_document(project_uid) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS sheet_instance(
  project_uid TEXT NOT NULL,
  sheet_uid TEXT NOT NULL,
  layout_template_id TEXT NOT NULL,
  frame_template_id TEXT NOT NULL,
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
  drawing_uid TEXT NOT NULL,
  layout_slot_id TEXT NOT NULL,
  source_view_id TEXT NOT NULL,
  scale_denominator INTEGER NOT NULL CHECK(scale_denominator>0),
  rotation_degrees INTEGER NOT NULL DEFAULT 0 CHECK(rotation_degrees IN (0,90)),
  is_scale_locked INTEGER NOT NULL DEFAULT 1 CHECK(is_scale_locked IN (0,1)),
  display_label TEXT,
  viewport_metadata_json TEXT NOT NULL DEFAULT '{}',
  PRIMARY KEY(project_uid,viewport_uid),
  UNIQUE(project_uid,sheet_uid,layout_slot_id),
  FOREIGN KEY(project_uid,sheet_uid) REFERENCES sheet_instance(project_uid,sheet_uid) ON DELETE CASCADE,
  FOREIGN KEY(project_uid,drawing_uid) REFERENCES drawing_instance(project_uid,drawing_uid)
);
CREATE TABLE IF NOT EXISTS drawing_object_dependency(
  project_uid TEXT NOT NULL,
  drawing_uid TEXT NOT NULL,
  object_uid TEXT NOT NULL,
  impact_policy TEXT NOT NULL CHECK(impact_policy IN ('AUTO','REGENERATE','REVIEW')),
  reason TEXT NOT NULL,
  PRIMARY KEY(project_uid,drawing_uid,object_uid,reason),
  FOREIGN KEY(project_uid,drawing_uid) REFERENCES drawing_instance(project_uid,drawing_uid) ON DELETE CASCADE,
  FOREIGN KEY(project_uid,object_uid) REFERENCES project_object(project_uid,object_uid) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS drawing_reference(
  project_uid TEXT NOT NULL,
  source_drawing_uid TEXT NOT NULL,
  reference_uid TEXT NOT NULL,
  target_drawing_uid TEXT NOT NULL,
  reference_type TEXT NOT NULL CHECK(reference_type IN ('ELEVATION','DETAIL','SECTION','CALLOUT')),
  PRIMARY KEY(project_uid,source_drawing_uid,reference_uid),
  FOREIGN KEY(project_uid,source_drawing_uid) REFERENCES drawing_instance(project_uid,drawing_uid) ON DELETE CASCADE,
  FOREIGN KEY(project_uid,target_drawing_uid) REFERENCES drawing_instance(project_uid,drawing_uid)
);
CREATE INDEX IF NOT EXISTS idx_project_sheet_number ON sheet_instance(project_uid,display_sheet_no);
CREATE INDEX IF NOT EXISTS idx_viewport_sheet ON viewport_instance(project_uid,sheet_uid);
CREATE INDEX IF NOT EXISTS idx_viewport_drawing ON viewport_instance(project_uid,drawing_uid);
CREATE INDEX IF NOT EXISTS idx_dependency_object ON drawing_object_dependency(project_uid,object_uid);
-- Issue sheets must have title block values but not every drawing instance must occupy its own sheet.
-- Copy/reorder must NOT change drawingUid or sheetUid; renumber only display_sheet_no.
-- DWG Handle is a mutable per-document lookup, not a globally immutable object identifier.
