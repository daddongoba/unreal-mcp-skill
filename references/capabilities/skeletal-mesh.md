# Capability: skeletal-mesh
> toolsets: SkeletalMeshTools / PhysicsAssetToolset | status: VERIFIED (inspection) / UNTESTED (physics authoring) | 2026-08-29 UE5.8-EN
> Routing: any task about bones, sockets, morph targets, skeletal meshes, physics assets/ragdoll.

## 1. Boundaries
- CAN: bone hierarchy reads (names/parent/children), socket CRUD + transforms, morph target lists, skeleton ref, LODs/sections/vertex counts, material slots, physics asset assignment, import skeletal mesh files.
- UNTESTED: PhysicsAssetToolset authoring (18 tools: AddBody/SetSphere/SetConstraintLimits...) — no PhysicsAsset found in engine content to probe; CreateFromMesh untried.
- CANNOT: weight painting, bone editing on existing meshes (re-import instead); **asset-level Skeleton re-assignment has NO MCP path** (2026-08-29 exhaustive attempt: set_properties rejected [ref+string], import_file needs source FBX [absent], Slate UI right-click route dead [observer died]). Fix = GUI: content browser right-click SK mesh -> reassign skeleton, OR migrate assets properly via editor (not file copy).
- Cross-project asset copying breaks internal GUID refs (Skeleton→Mesh); the copied SKELETON asset itself loads fine but the MESH loses its link — component-level SkeletalMesh assignment still works for preview-binding but bones/anims stay dead.

## 2. Design conventions
- Health check before any skeleton-dependent work (ControlRig import, anims): get_bone_names must return real bones — "has no skeleton assigned" = broken GUID refs (cross-project copies).
- Component-level mesh assignment: SkeletalMeshComponent on BP CDO + set_properties SkeletalMesh:ref (works, readback verified) — anims bind through the mesh's skeleton automatically.
- Engine test subjects: /Engine/EngineMeshes/SkeletalCube (Bone01/Bone02), TutorialTPP; project crow: /Game/TestT13/Crow/Meshes/SK_Crow (broken skeleton — pending GUI fix).

## 3. Tool params (verified signatures)
| Tool | Params |
|---|---|
| `get_bone_names` / `get_bone_parent` / `get_bone_children` | mesh:ref(OBJECT) |
| `get_socket_names` / `add_socket` / `rename_socket` / `set_socket_transform` | mesh:ref, socket names/params |
| `get_morph_target_names` / `get_skeleton` / `get_lod_count` / `get_vertex_count` / `get_bounds` / `get_material_slots` | mesh:ref |
| `assign_physics_asset` / `get_physics_asset` | mesh:ref, physics_asset:ref |
| `import_file` | file + mesh options |
| PhysicsAssetToolset: `GetBodyNames` / `GetBodyShapes` / `CreateFromMesh` / `AddBody` / `SetSphere` / `AddConstraint` / `SetConstraintLimits` | physicsAsset:ref + params (schema-live, untested) |

## 4. Laws (domain)
- mesh param wants OBJECT ref (`{"refPath":"/Engine/.../X.X"}`) — plain string path rejected (G12).
- Asset-level Skeleton NOT settable via set_properties (G9) — repair requires GUI (reassign skeleton in content browser) or re-import.
- Cross-domain: G12, G9.

## 5. Recipes
| Task | Recipe |
|---|---|
| Skeletal actor from mesh | blueprint.md §3 add_component(SkeletalMeshComponent) + set SkeletalMesh → compile → place (BP_CrowActor pattern, verified) |
| Rig from bones | anim-controlrig.md (import_bones_from_asset) |

## 6. Evidence
- 2026-08-28/29: SkeletalCube inspection verified; BP_CrowActor + BP_CubeActor component-assign pattern verified (readback).
