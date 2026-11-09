"""Validate the Q furniture/finish detail pass without opening Blender."""
import json
import base64
import re
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
result = {}


def check(name, condition, detail=None):
    result[name] = {"pass": bool(condition)}
    if detail is not None:
        result[name]["detail"] = detail
    assert condition, name


report = json.loads((ROOT / "model/model-report.json").read_text())
check("model_version", report["version"] == "O", report.get("version"))
check("mesh_objects", report["mesh_objects"] >= 6000, report["mesh_objects"])

glb = (ROOT / "model/courtyard-house.glb").read_bytes()
check("glb_header", glb[:4] == b"glTF", glb[:4].decode("ascii", "replace"))
payload = (ROOT / "model/scene-data.js").read_text()
check("embedded_glb_matches",
      base64.b64decode(payload.split("'", 2)[1]) == glb,
      f"{len(glb)/1048576:.1f} MiB embedded")

design = json.loads((ROOT / "model/design.json").read_text())
check("design_layout_keys", set(design["rooms"]) == {"front", "rear1", "rear2"})
room_count = sum(len(v) for v in design["rooms"].values())
check("room_count_unchanged", room_count == 22, room_count)
check("finish_revision_doc", (ROOT / "docs/revision-Q-details.md").exists())

manifest = json.loads((ROOT / "精装效果图/manifest.json").read_text())
check("view_count", len(manifest["views"]) == 13, len(manifest["views"]))
for view in manifest["views"]:
    path = ROOT / "精装效果图" / view["file"]
    with Image.open(path) as image:
        check("image_" + view["id"], image.size == (2560, 1440), list(image.size))

overview = Image.open(ROOT / "精装效果图/00-精装总览.jpg")
check("overview", overview.size == (1800, 1940), list(overview.size))

rear_finishes = [r["finish"] for r in design["room_specs"]
                 if r["kind"] == "bed" and r["group"] in ("rear1", "rear2")]
check("rear_bedrooms_light_stone", rear_finishes and all("石纹砖" in f for f in rear_finishes), rear_finishes)
check("light_palette_note", "浅色" in design["version"], design["version"])

html = (ROOT / "精装效果图/index.html").read_text()
check("gallery_images", len(re.findall(r'<img src="\d\d-[^"]+\.png"', html)) == 13)
check("gallery_title", "浅色精装" in html)
check("gallery_material_section", 'id="material-advice"' in html)

index = (ROOT / "index.html").read_text()
check("index_links_gallery", "精装效果图/index.html" in index)

visuals = [
    "Wall skirting", "Door casing", "Recessed downlight ring", "Linen upholstered headboard",
    "Timber wall slat", "Draped bed throw", "LIGHTROOF", "PAVILIONPOST",
    "Woven rug", "Framed artwork", "Plant pot", "Kitchen open shelf", "Bathroom tile wainscot",
    "Pantry jar", "Sofa arm blanket", "Bath mat",
]
source = (ROOT / "scripts/interior_details.py").read_text() + (ROOT / "scripts/render_model.py").read_text()
missing = [name for name in visuals if name not in source]
check("detail_features_present", not missing, missing)

(ROOT / "check/Q-finish-validation.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2))
print("Q FINISH VALIDATION PASS:", len(result), "checks")
