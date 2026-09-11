# UE Python import task - executed via `py` console command in Output Log
import unreal

FILE = r"{{FILE}}"
DEST = "{{DEST}}"

task = unreal.AssetImportTask()
task.set_editor_property("filename", FILE)
task.set_editor_property("destination_path", DEST)
task.set_editor_property("automated", True)
task.set_editor_property("save", True)
task.set_editor_property("replace_existing", True)

result = unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
imported = task.get_editor_property("imported_object_paths")
print("IMPORT_DONE paths={}".format(list(imported) if imported else []))
