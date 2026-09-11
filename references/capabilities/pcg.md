# Capability: pcg
> toolsets: PCGToolset / PCGSpatialToolset | status: VERIFIED (graph+node+instance) | 2026-08-29 UE5.8-EN
> Routing: any task about procedural content generation, scattering, PCG graphs, surface sampling.

## 1. Boundaries
- CAN: create graphs, add nodes (native node types), connect pins, comments, graph instances in levels, execute instances, set params, read structure/schemas, subgraphs, spline drawing.
- CANNOT: authoring custom node types; spatial toolset (PCGSpatialToolset) untested.
- Note: graphs land in /Game/PCG/ by default (folder param untested to redirect).

## 2. Design conventions
- Node vocabulary via ListNativeNodes (display names like "Surface Sampler"); node params via jsonParams.
- Instance pattern: SpawnGraphInstance(graph+name+transform+jsonParams) places a PCG actor in level.

## 3. Tool params (verified signatures)
| Tool | Params |
|---|---|
| `PCGToolset.CreateGraph` | name, folder_path → ref in /Game/PCG/ |
| `AddNode` | graph:OBJ-path, nativeNodeType:"Surface Sampler"(display), nodeName, nodeTitle, nodeComment, jsonParams:"{}" (ALL required) |
| `SpawnGraphInstance` | graph:OBJ-path, name, transform{location,rotation,scale}, jsonParams:"{}" → {actor, graph} |
| `ListNativeNodes` | {} → display names |
| `GetGraphStructure` / `GetGraphSchema` / `GetNodeInfo` | graph:OBJ-path |
| `ConnectNodePins` / `DisconnectNodePins` | graph, node+pin ids |
| `ExecuteGraphInstance` / `ListGraphInstances` | instance/graph refs |
| `DrawSpline` / `SetGraphParams` / `SetNodeComment` | graph/instance refs |

## 4. Laws (domain)
- AddNode demands FOUR string params + jsonParams — minimal args fail (G12 iterate-on-error works).
- Cross-domain: G12 (graph param wants OBJ path — "PCG_Test13" string rejected).

## 5. Recipes
| Task | Recipe |
|---|---|
| Scatter props on surface | CreateGraph → AddNode(Surface Sampler) → SpawnGraphInstance → Execute (chain verified 2026-08-29; param tuning untested) |

## 6. Evidence
- 2026-08-29: PCG_Test13 graph + MySampler node + PCGI_Test13 instance in LS_T11 (all refs returned); ExecuteGraphInstance not yet run on populated graph.
