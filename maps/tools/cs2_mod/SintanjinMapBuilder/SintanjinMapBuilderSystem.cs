using System;
using System.Collections.Generic;
using System.IO;
using System.Runtime.InteropServices;
using Colossal.Mathematics;
using Game;
using Game.Common;
using Game.Net;
using Game.Objects;
using Game.Prefabs;
using Game.SceneFlow;
using Game.Simulation;
using Game.Tools;
using Unity.Collections;
using Unity.Entities;
using Unity.Jobs;
using Unity.Mathematics;
using UnityEngine;
using UnityEngine.InputSystem;

namespace SintanjinMapBuilder
{
    [StructLayout(LayoutKind.Sequential, Pack = 1)]
    internal struct TreeRecord
    {
        public float Wx;
        public float Wz;
        public byte Biome;
        public byte Age;
        public byte Rot;
        public byte Var;
    }

    internal struct RoadRecord
    {
        public byte Kind;
        public byte Flags;
        public float P0x, P0y, P0z;
        public float P1x, P1y, P1z;
        public float P2x, P2y, P2z;
        public float P3x, P3y, P3z;
        public float Elev0, Elev1;
    }

    public partial class SintanjinMapBuilderSystem : GameSystemBase
    {
        private TerrainSystem m_TerrainSystem;
        private WaterSystem m_WaterSystem;
        private NaturalResourceSystem m_NaturalResourceSystem;
        private GroundWaterSystem m_GroundWaterSystem;
        private PrefabSystem m_PrefabSystem;

        private EntityQuery m_TreePrefabQuery;
        private EntityQuery m_WildTreeQuery;
        private EntityQuery m_RoadPrefabQuery;
        private EntityQuery m_TrackPrefabQuery;
        private EntityQuery m_NetNodeQuery;
        private EntityQuery m_NetEdgeQuery;

        private readonly List<Entity> m_ConiferPrefabs = new List<Entity>();
        private readonly List<Entity> m_BroadleafPrefabs = new List<Entity>();
        private readonly List<Entity> m_RiparianPrefabs = new List<Entity>();
        private readonly List<Entity> m_ShrubPrefabs = new List<Entity>();
        private readonly List<Entity> m_AllValidTrees = new List<Entity>();
        private readonly HashSet<Entity> m_PrefabsWithSeed = new HashSet<Entity>();
        private readonly Entity[] m_NetPrefabs = new Entity[6];
        private bool m_HasNetPrefabs;
        private bool m_LoggedNetPrefabs;

        private List<TreeRecord> m_PendingTrees;
        private int m_PendingCursor;
        private int m_SpawnedThisRun;
        private int m_SkippedWaterThisRun;
        private bool m_LoggedPrefabs;

        private List<RoadRecord> m_PendingRoads;
        private int m_PendingRoadCursor;
        private int m_SpawnedRoadsThisRun;
        private int m_SkippedRoadsThisRun;
        private int m_SnappedNodesThisRun;
        private readonly List<Entity> m_CreatedRoadDefs = new List<Entity>();
        private readonly Dictionary<long, List<(Entity entity, float3 pos, float elevMid)>> m_NodeGrid =
            new Dictionary<long, List<(Entity, float3, float)>>();

        private static string BaseDataDir =>
            Path.Combine(Application.persistentDataPath, "Sintanjin_Jeonmin_Pack");

        private static string StatusLogPath =>
            Path.Combine(Application.persistentDataPath, "Sintanjin_Status.log");

        private static string CommandFilePath =>
            Path.Combine(Application.persistentDataPath, "Sintanjin_Command.txt");

        protected override void OnCreate()
        {
            base.OnCreate();
            m_TerrainSystem = World.GetOrCreateSystemManaged<TerrainSystem>();
            m_WaterSystem = World.GetOrCreateSystemManaged<WaterSystem>();
            m_NaturalResourceSystem = World.GetOrCreateSystemManaged<NaturalResourceSystem>();
            m_GroundWaterSystem = World.GetOrCreateSystemManaged<GroundWaterSystem>();
            m_PrefabSystem = World.GetOrCreateSystemManaged<PrefabSystem>();

            m_TreePrefabQuery = GetEntityQuery(
                ComponentType.ReadOnly<TreeData>(),
                ComponentType.ReadOnly<ObjectData>(),
                ComponentType.ReadOnly<PrefabData>(),
                ComponentType.Exclude<PlaceholderObjectElement>()
            );

            m_WildTreeQuery = GetEntityQuery(
                ComponentType.ReadOnly<Game.Objects.Tree>(),
                ComponentType.Exclude<Owner>(),
                ComponentType.Exclude<Deleted>(),
                ComponentType.Exclude<Game.Tools.Temp>()
            );

            m_RoadPrefabQuery = GetEntityQuery(
                ComponentType.ReadOnly<RoadData>(),
                ComponentType.ReadOnly<NetGeometryData>(),
                ComponentType.ReadOnly<PlaceableNetData>(),
                ComponentType.ReadOnly<PrefabData>()
            );

            m_TrackPrefabQuery = GetEntityQuery(
                ComponentType.ReadOnly<TrackData>(),
                ComponentType.ReadOnly<NetGeometryData>(),
                ComponentType.ReadOnly<PlaceableNetData>(),
                ComponentType.ReadOnly<PrefabData>()
            );

            m_NetNodeQuery = GetEntityQuery(
                ComponentType.ReadOnly<Game.Net.Node>(),
                ComponentType.Exclude<Owner>(),
                ComponentType.Exclude<Deleted>(),
                ComponentType.Exclude<Game.Tools.Temp>()
            );

            m_NetEdgeQuery = GetEntityQuery(
                ComponentType.ReadOnly<Game.Net.Edge>(),
                ComponentType.Exclude<Owner>(),
                ComponentType.Exclude<Deleted>(),
                ComponentType.Exclude<Game.Tools.Temp>()
            );

            WriteStatus("SintanjinMapBuilderSystem initialized (Modification1). Hotkeys: F6=ALL(Resources+Trees+Roads), Ctrl+Shift+H=BackboneRoads, Ctrl+Shift+K=ClearRoads, Ctrl+Shift+R=Resources, Ctrl+Shift+T=Trees, Ctrl+Shift+X=ClearWildTrees.");
        }

        private static void WriteStatus(string msg)
        {
            try
            {
                string line = $"[{DateTime.Now:HH:mm:ss}] {msg}";
                Mod.Log.Info(line);
                File.AppendAllText(StatusLogPath, line + Environment.NewLine);
            }
            catch { }
        }

        private bool IsMapReady()
        {
            var gm = GameManager.instance;
            if (gm == null || !gm.gameMode.IsGameOrEditor() || gm.isGameLoading)
                return false;
            if (m_TerrainSystem == null)
                return false;
            var h = m_TerrainSystem.GetHeightData(false);
            return h.isCreated;
        }

        protected override void OnUpdate()
        {
            if (!IsMapReady())
                return;

            CleanupRoadDefinitions();

            // Process batched tree planting cleanly without freezing the frame
            if (m_PendingTrees != null)
            {
                ProcessTreeBatch(2200);
                return;
            }

            // Process batched backbone road/rail creation definitions right before GenerateNodesSystem (Modification1)
            if (m_PendingRoads != null)
            {
                ProcessRoadBatch(250);
                return;
            }

            // Keyboard hotkeys (non-conflicting with vanilla CS2 F1..F5)
            var kb = Keyboard.current;
            if (kb != null)
            {
                bool ctrl = kb.leftCtrlKey.isPressed || kb.rightCtrlKey.isPressed;
                bool shift = kb.leftShiftKey.isPressed || kb.rightShiftKey.isPressed;

                if (!ctrl && !shift && kb.f6Key.wasPressedThisFrame)
                {
                    WriteStatus("Hotkey F6 -> Full Pipeline (Resources + Realistic Forest Trees + Backbone Roads & Rail)");
                    ApplyNaturalResources();
                    StartTreeSpawn();
                    StartRoadSpawn();
                    return;
                }
                if (ctrl && shift && kb.rKey.wasPressedThisFrame)
                {
                    WriteStatus("Hotkey Ctrl+Shift+R -> Applying 256x256 Natural Resources");
                    ApplyNaturalResources();
                    return;
                }
                if (ctrl && shift && kb.tKey.wasPressedThisFrame)
                {
                    WriteStatus("Hotkey Ctrl+Shift+T -> Spawning Realistic Forest & Riparian Trees");
                    StartTreeSpawn();
                    return;
                }
                if (ctrl && shift && kb.hKey.wasPressedThisFrame)
                {
                    WriteStatus("Hotkey Ctrl+Shift+H -> Building Method A Backbone Roads & Rail (Mainlines/Bridges/Tunnels)");
                    StartRoadSpawn();
                    return;
                }
                if (ctrl && shift && kb.kKey.wasPressedThisFrame)
                {
                    WriteStatus("Hotkey Ctrl+Shift+K -> Clearing Existing Roads & Tracks");
                    ClearRoadsAndTracks();
                    return;
                }
                if (ctrl && shift && kb.xKey.wasPressedThisFrame)
                {
                    WriteStatus("Hotkey Ctrl+Shift+X -> Clearing Existing Wild Trees");
                    ClearWildTrees();
                    return;
                }
            }

            // Optional command file trigger
            if (File.Exists(CommandFilePath))
            {
                try
                {
                    string cmd = File.ReadAllText(CommandFilePath).Trim().ToUpperInvariant();
                    File.Delete(CommandFilePath);
                    WriteStatus($"Executing command file: {cmd}");
                    if (cmd.Contains("CLEARNET") || cmd.Contains("CLEARROAD"))
                        ClearRoadsAndTracks();
                    else if (cmd.Contains("CLEAR"))
                        ClearWildTrees();
                    if (cmd.Contains("ALL") || cmd.Contains("RESOURCE"))
                        ApplyNaturalResources();
                    if (cmd.Contains("ALL") || cmd.Contains("TREE"))
                        StartTreeSpawn();
                    if (cmd.Contains("ALL") || cmd.Contains("ROAD") || cmd.Contains("RAIL") || cmd.Contains("HIGHWAY"))
                        StartRoadSpawn();
                }
                catch (Exception ex)
                {
                    WriteStatus($"Command file error: {ex.Message}");
                }
            }
        }

        private void ApplyNaturalResources()
        {
            try
            {
                string binPath = Path.Combine(BaseDataDir, "sintanjin_resources_256.bin");
                if (!File.Exists(binPath))
                {
                    WriteStatus($"ERROR: Resource pack not found at {binPath}");
                    return;
                }

                byte[] bytes = File.ReadAllBytes(binPath);
                if (bytes.Length < 655360)
                {
                    WriteStatus($"ERROR: Resource binary truncated ({bytes.Length} bytes < 655360)");
                    return;
                }

                NativeArray<NaturalResourceCell> nrMap = m_NaturalResourceSystem.GetMap(false, out JobHandle nrDeps);
                nrDeps.Complete();

                NativeArray<GroundWater> gwMap = m_GroundWaterSystem.GetMap(false, out JobHandle gwDeps);
                gwDeps.Complete();

                int count = Math.Min(65536, nrMap.Length);
                int pos = 0;
                for (int i = 0; i < count; i++)
                {
                    ushort fert = Math.Min((ushort)NaturalResourceSystem.MAX_BASE_RESOURCES, BitConverter.ToUInt16(bytes, pos));
                    ushort ore = Math.Min((ushort)NaturalResourceSystem.MAX_BASE_RESOURCES, BitConverter.ToUInt16(bytes, pos + 2));
                    ushort oil = Math.Min((ushort)NaturalResourceSystem.MAX_BASE_RESOURCES, BitConverter.ToUInt16(bytes, pos + 4));
                    ushort fish = Math.Min((ushort)NaturalResourceSystem.MAX_BASE_RESOURCES, BitConverter.ToUInt16(bytes, pos + 6));
                    ushort gwRaw = BitConverter.ToUInt16(bytes, pos + 8);
                    pos += 10;

                    nrMap[i] = new NaturalResourceCell
                    {
                        m_Fertility = new NaturalResourceAmount { m_Base = fert, m_Used = 0 },
                        m_Ore = new NaturalResourceAmount { m_Base = ore, m_Used = 0 },
                        m_Oil = new NaturalResourceAmount { m_Base = oil, m_Used = 0 },
                        m_Fish = new NaturalResourceAmount { m_Base = fish, m_Used = 0 },
                    };

                    if (i < gwMap.Length)
                    {
                        short gwVal = (short)Math.Min((int)gwRaw, GroundWaterSystem.kMaxGroundWater);
                        gwMap[i] = new GroundWater
                        {
                            m_Amount = gwVal,
                            m_Max = gwVal,
                            m_Polluted = 0,
                        };
                    }
                }

                m_NaturalResourceSystem.AddWriter(default);
                m_GroundWaterSystem.AddWriter(default);
                WriteStatus($"SUCCESS: Applied 256x256 Natural Resources (Fertility, Ore, Oil, Fish, GroundWater) to ECS ({count} cells)!");
            }
            catch (Exception ex)
            {
                WriteStatus($"ERROR in ApplyNaturalResources: {ex}");
            }
        }

        private void ClearWildTrees()
        {
            try
            {
                using var existing = m_WildTreeQuery.ToEntityArray(Allocator.Temp);
                if (existing.Length == 0)
                {
                    WriteStatus("No wild trees found to clear.");
                    return;
                }
                EntityManager.AddComponent<Deleted>(existing);
                WriteStatus($"Cleared {existing.Length:N0} wild trees (queued Game.Common.Deleted).");
            }
            catch (Exception ex)
            {
                WriteStatus($"ERROR in ClearWildTrees: {ex}");
            }
        }

        private void DiscoverTreePrefabs()
        {
            m_ConiferPrefabs.Clear();
            m_BroadleafPrefabs.Clear();
            m_RiparianPrefabs.Clear();
            m_ShrubPrefabs.Clear();
            m_AllValidTrees.Clear();
            m_PrefabsWithSeed.Clear();

            TypeIndex seedTypeIdx = TypeManager.GetTypeIndex<PseudoRandomSeed>();
            using var prefabs = m_TreePrefabQuery.ToEntityArray(Allocator.Temp);
            var discoveredNames = new List<string>();

            for (int i = 0; i < prefabs.Length; i++)
            {
                Entity p = prefabs[i];
                string name;
                try { name = m_PrefabSystem.GetPrefabName(p) ?? ""; }
                catch { name = ""; }

                string low = name.ToLowerInvariant();
                if (low.Contains("pot") || low.Contains("planter") || low.Contains("palm") ||
                    low.Contains("cactus") || low.Contains("joshua") || low.Contains("yucca") ||
                    low.Contains("saguaro") || low.Contains("agave") || low.Contains("dead") ||
                    low.Contains("stump") || low.Contains("hedge"))
                    continue;

                m_AllValidTrees.Add(p);
                discoveredNames.Add(name);
                ObjectData od = EntityManager.GetComponentData<ObjectData>(p);
                using (var archTypes = od.m_Archetype.GetComponentTypes(Allocator.Temp))
                {
                    for (int t = 0; t < archTypes.Length; t++)
                    {
                        if (archTypes[t].TypeIndex == seedTypeIdx)
                        {
                            m_PrefabsWithSeed.Add(p);
                            break;
                        }
                    }
                }

                if (low.Contains("bush") || low.Contains("shrub"))
                    m_ShrubPrefabs.Add(p);
                else if (low.Contains("pine") || low.Contains("spruce") || low.Contains("fir") || low.Contains("cedar"))
                    m_ConiferPrefabs.Add(p);
                else if (low.Contains("birch") || low.Contains("alder") || low.Contains("willow") || low.Contains("linden") || low.Contains("london"))
                    m_RiparianPrefabs.Add(p);
                else
                    m_BroadleafPrefabs.Add(p);
            }

            if (m_ConiferPrefabs.Count == 0) m_ConiferPrefabs.AddRange(m_AllValidTrees);
            if (m_BroadleafPrefabs.Count == 0) m_BroadleafPrefabs.AddRange(m_AllValidTrees);
            if (m_RiparianPrefabs.Count == 0) m_RiparianPrefabs.AddRange(m_BroadleafPrefabs);
            if (m_ShrubPrefabs.Count == 0) m_ShrubPrefabs.AddRange(m_BroadleafPrefabs);

            if (!m_LoggedPrefabs)
            {
                m_LoggedPrefabs = true;
                WriteStatus($"Discovered {m_AllValidTrees.Count} suitable tree prefabs (Conifer={m_ConiferPrefabs.Count}, Broadleaf={m_BroadleafPrefabs.Count}, Riparian={m_RiparianPrefabs.Count}, Shrub={m_ShrubPrefabs.Count}): {string.Join(", ", discoveredNames)}");
            }
        }

        private void StartTreeSpawn()
        {
            try
            {
                string binPath = Path.Combine(BaseDataDir, "sintanjin_trees.bin");
                if (!File.Exists(binPath))
                {
                    WriteStatus($"ERROR: Tree pack not found at {binPath}");
                    return;
                }

                DiscoverTreePrefabs();
                if (m_AllValidTrees.Count == 0)
                {
                    WriteStatus("ERROR: No valid TreeData prefabs discovered in active game world!");
                    return;
                }

                using var fs = File.OpenRead(binPath);
                using var br = new BinaryReader(fs);
                byte[] magic = br.ReadBytes(4);
                if (magic.Length != 4 || magic[0] != 'S' || magic[1] != 'J' || magic[2] != 'T' || magic[3] != '1')
                {
                    WriteStatus("ERROR: Invalid sintanjin_trees.bin header!");
                    return;
                }

                int count = br.ReadInt32();
                var list = new List<TreeRecord>(count);
                for (int i = 0; i < count; i++)
                {
                    list.Add(new TreeRecord
                    {
                        Wx = br.ReadSingle(),
                        Wz = br.ReadSingle(),
                        Biome = br.ReadByte(),
                        Age = br.ReadByte(),
                        Rot = br.ReadByte(),
                        Var = br.ReadByte(),
                    });
                }

                m_PendingTrees = list;
                m_PendingCursor = 0;
                m_SpawnedThisRun = 0;
                m_SkippedWaterThisRun = 0;
                WriteStatus($"Queued {count:N0} realistic trees for batched terrain-snapped spawning...");
            }
            catch (Exception ex)
            {
                WriteStatus($"ERROR in StartTreeSpawn: {ex}");
            }
        }

        private Entity PickPrefab(TreeRecord rec, ref Unity.Mathematics.Random rng)
        {
            List<Entity> pool;
            switch (rec.Biome)
            {
                case 0: // Conifer ridge (Pine/Spruce heavy, light Oak/Birch mix)
                    pool = (rec.Var < 210) ? m_ConiferPrefabs : m_BroadleafPrefabs;
                    break;
                case 2: // Riparian / Park broadleaf (Birch/Alder/Linden/Oak heavy)
                    pool = (rec.Var < 185) ? m_RiparianPrefabs : m_BroadleafPrefabs;
                    break;
                case 3: // Edge shrub / young colonizer trees
                    pool = (rec.Var < 170) ? m_ShrubPrefabs : ((rec.Var < 215) ? m_ConiferPrefabs : m_BroadleafPrefabs);
                    break;
                default: // 1: Mixed Korean mountain forest (Oak/Broadleaf + Pine + Birch)
                    if (rec.Var < 115) pool = m_BroadleafPrefabs;
                    else if (rec.Var < 205) pool = m_ConiferPrefabs;
                    else pool = m_RiparianPrefabs;
                    break;
            }
            return pool[rng.NextInt(pool.Count)];
        }

        private void ProcessTreeBatch(int batchSize)
        {
            try
            {
                TerrainHeightData hData = m_TerrainSystem.GetHeightData(false);
                if (!hData.isCreated)
                    return;

                float minWaterSafeY = Math.Max(m_WaterSystem.SeaLevel + 0.45f, 18.0f);
                int end = Math.Min(m_PendingCursor + batchSize, m_PendingTrees.Count);
                var rng = new Unity.Mathematics.Random((uint)(DateTime.UtcNow.Ticks ^ (m_PendingCursor + 17)));
                using var ecb = new EntityCommandBuffer(Allocator.Temp);

                for (int i = m_PendingCursor; i < end; i++)
                {
                    TreeRecord rec = m_PendingTrees[i];
                    float3 pos = new float3(rec.Wx, 0f, rec.Wz);
                    float y = TerrainUtils.SampleHeight(ref hData, pos);
                    if (y < minWaterSafeY)
                    {
                        m_SkippedWaterThisRun++;
                        continue;
                    }
                    pos.y = y;

                    Entity prefab = PickPrefab(rec, ref rng);
                    ObjectData objData = EntityManager.GetComponentData<ObjectData>(prefab);

                    float yaw = (rec.Rot / 255f) * (2f * math.PI);
                    float age = math.clamp(rec.Age / 255f, 0.12f, 0.90f);

                    Game.Objects.Tree treeComp = ObjectUtils.InitializeTreeState(age);
                    Game.Objects.Transform tr = new Game.Objects.Transform
                    {
                        m_Position = pos,
                        m_Rotation = quaternion.RotateY(yaw),
                    };

                    Entity e = ecb.CreateEntity(objData.m_Archetype);
                    ecb.SetComponent(e, new PrefabRef(prefab));
                    ecb.SetComponent(e, tr);
                    ecb.SetComponent(e, treeComp);
                    if (m_PrefabsWithSeed.Contains(prefab))
                        ecb.SetComponent(e, new PseudoRandomSeed((ushort)rng.NextInt(1, 65536)));

                    m_SpawnedThisRun++;
                }

                ecb.Playback(EntityManager);

                m_PendingCursor = end;
                if (m_PendingCursor >= m_PendingTrees.Count)
                {
                    WriteStatus($"SUCCESS: Spawned {m_SpawnedThisRun:N0} trees into ECS world (skipped {m_SkippedWaterThisRun:N0} under water/shoreline).");
                    m_PendingTrees = null;
                }
            }
            catch (Exception ex)
            {
                WriteStatus($"ERROR in ProcessTreeBatch: {ex}");
                m_PendingTrees = null;
            }
        }

        private void CleanupRoadDefinitions()
        {
            if (m_CreatedRoadDefs.Count == 0)
                return;

            for (int i = 0; i < m_CreatedRoadDefs.Count; i++)
            {
                Entity e = m_CreatedRoadDefs[i];
                if (EntityManager.Exists(e))
                    EntityManager.DestroyEntity(e);
            }
            m_CreatedRoadDefs.Clear();
        }

        private void DiscoverNetPrefabs()
        {
            for (int i = 0; i < m_NetPrefabs.Length; i++)
                m_NetPrefabs[i] = Entity.Null;

            float[] bestScore = new float[6];
            for (int i = 0; i < 6; i++)
                bestScore[i] = float.MaxValue;

            var loggedCandidates = new List<string>();

            using (var roadEntities = m_RoadPrefabQuery.ToEntityArray(Allocator.Temp))
            {
                for (int i = 0; i < roadEntities.Length; i++)
                {
                    Entity p = roadEntities[i];
                    RoadData rd = EntityManager.GetComponentData<RoadData>(p);
                    NetGeometryData ngd = EntityManager.GetComponentData<NetGeometryData>(p);
                    if ((ngd.m_Flags & Game.Net.GeometryFlags.Marker) != 0)
                        continue;

                    string name;
                    try { name = m_PrefabSystem.GetPrefabName(p) ?? ""; }
                    catch { name = ""; }
                    string low = name.ToLowerInvariant();

                    if (low.Contains("gravel") || low.Contains("alley") || low.Contains("pedestrian") ||
                        low.Contains("tram") || low.Contains("bus") || low.Contains("quay") ||
                        low.Contains("bridge") || low.Contains("dam") || low.Contains("airport") ||
                        low.Contains("harbor") || low.Contains("parking") || low.Contains("invisible") ||
                        low.Contains("connection"))
                        continue;

                    bool isHwy = (rd.m_Flags & Game.Prefabs.RoadFlags.UseHighwayRules) != 0;
                    bool isSep = (rd.m_Flags & Game.Prefabs.RoadFlags.SeparatedCarriageways) != 0;
                    bool isFwd = (rd.m_Flags & Game.Prefabs.RoadFlags.DefaultIsForward) != 0;
                    bool isBwd = (rd.m_Flags & Game.Prefabs.RoadFlags.DefaultIsBackward) != 0;
                    float w = ngd.m_DefaultWidth;

                    loggedCandidates.Add($"{name}(w={w:F1},f={(int)rd.m_Flags})");

                    if (isHwy && isFwd && !isBwd && !isSep)
                    {
                        float s3 = Math.Abs(w - 14.0f) - (low.Contains("3") || low.Contains("three") ? 4.0f : 0f);
                        if (s3 < bestScore[0]) { bestScore[0] = s3; m_NetPrefabs[0] = p; }

                        float s2 = Math.Abs(w - 11.0f) - (low.Contains("2") || low.Contains("two") ? 4.0f : 0f);
                        if (s2 < bestScore[1]) { bestScore[1] = s2; m_NetPrefabs[1] = p; }
                    }
                    else if (!isHwy && !low.Contains("highway"))
                    {
                        // Kind 2: 4L Divided Twoway Arterial
                        if (!isFwd && !isBwd)
                        {
                            float s4d = Math.Abs(w - 24.0f)
                                - (isSep ? 8.0f : 0f)
                                - (low.Contains("divided") || low.Contains("median") ? 4.0f : 0f)
                                - (low.Contains("four") || low.Contains("4") ? 3.0f : 0f);
                            if (s4d < bestScore[2]) { bestScore[2] = s4d; m_NetPrefabs[2] = p; }
                        }

                        // Kind 3: 2L Twoway Street/Road
                        if (!isFwd && !isBwd && !isSep)
                        {
                            float s2tw = Math.Abs(w - 16.0f)
                                - (low.Contains("two") || low.Contains("2") || low.Contains("medium") ? 3.0f : 0f)
                                + (w < 10.0f ? 20.0f : 0f);
                            if (s2tw < bestScore[3]) { bestScore[3] = s2tw; m_NetPrefabs[3] = p; }
                        }

                        // Kind 4: 2L Oneway Street
                        if (isFwd && !isBwd && !isSep)
                        {
                            float s2ow = Math.Abs(w - 16.0f) - (low.Contains("two") || low.Contains("2") ? 3.0f : 0f);
                            if (s2ow < bestScore[4]) { bestScore[4] = s2ow; m_NetPrefabs[4] = p; }
                        }
                    }
                }
            }

            using (var trackEntities = m_TrackPrefabQuery.ToEntityArray(Allocator.Temp))
            {
                for (int i = 0; i < trackEntities.Length; i++)
                {
                    Entity p = trackEntities[i];
                    TrackData td = EntityManager.GetComponentData<TrackData>(p);
                    NetGeometryData ngd = EntityManager.GetComponentData<NetGeometryData>(p);
                    if ((ngd.m_Flags & Game.Net.GeometryFlags.Marker) != 0)
                        continue;
                    if ((td.m_TrackType & TrackTypes.Train) == 0 ||
                        (td.m_TrackType & (TrackTypes.Tram | TrackTypes.Subway)) != 0)
                        continue;

                    string name;
                    try { name = m_PrefabSystem.GetPrefabName(p) ?? ""; }
                    catch { name = ""; }
                    string low = name.ToLowerInvariant();
                    if (low.Contains("station") || low.Contains("cargo") || low.Contains("bridge") || low.Contains("quay"))
                        continue;

                    float w = ngd.m_DefaultWidth;
                    loggedCandidates.Add($"{name}(Track w={w:F1},t={(int)td.m_TrackType})");

                    bool isOneWay = low.Contains("oneway") || low.Contains("single");
                    float sr = Math.Abs(w - 16.0f)
                        + (isOneWay ? 30.0f : 0f)
                        - (low.Contains("double") || low.Contains("twoway") ? 5.0f : 0f);
                    if (sr < bestScore[5]) { bestScore[5] = sr; m_NetPrefabs[5] = p; }
                }
            }

            // Reasonable internal fallbacks among discovered prefabs
            if (m_NetPrefabs[0] == Entity.Null) m_NetPrefabs[0] = m_NetPrefabs[1];
            if (m_NetPrefabs[1] == Entity.Null) m_NetPrefabs[1] = m_NetPrefabs[0];
            if (m_NetPrefabs[2] == Entity.Null) m_NetPrefabs[2] = m_NetPrefabs[3];
            if (m_NetPrefabs[4] == Entity.Null) m_NetPrefabs[4] = m_NetPrefabs[3];

            m_HasNetPrefabs = true;
            for (int i = 0; i < 6; i++)
                if (m_NetPrefabs[i] == Entity.Null) m_HasNetPrefabs = false;

            if (!m_LoggedNetPrefabs)
            {
                m_LoggedNetPrefabs = true;
                string GetName(Entity e) => e == Entity.Null ? "<NULL>" : (m_PrefabSystem.GetPrefabName(e) ?? e.ToString());
                WriteStatus(
                    $"Selected Backbone Prefabs: " +
                    $"[0:3L_Hwy={GetName(m_NetPrefabs[0])}, " +
                    $"1:2L_Hwy={GetName(m_NetPrefabs[1])}, " +
                    $"2:4L_Div={GetName(m_NetPrefabs[2])}, " +
                    $"3:2L_Road={GetName(m_NetPrefabs[3])}, " +
                    $"4:2L_OW={GetName(m_NetPrefabs[4])}, " +
                    $"5:DblRail={GetName(m_NetPrefabs[5])}]"
                );
                WriteStatus($"All {loggedCandidates.Count} road/track prefabs seen: {string.Join(", ", loggedCandidates)}");
            }
        }

        private void StartRoadSpawn()
        {
            try
            {
                string binPath = Path.Combine(BaseDataDir, "sintanjin_roads.bin");
                if (!File.Exists(binPath))
                {
                    WriteStatus($"ERROR: Road backbone pack not found at {binPath}");
                    return;
                }

                DiscoverNetPrefabs();
                if (!m_HasNetPrefabs)
                {
                    WriteStatus("ERROR: Failed to resolve all required road/train prefabs (check Sintanjin_Status.log).");
                    return;
                }

                using var fs = File.OpenRead(binPath);
                using var br = new BinaryReader(fs);
                byte[] magic = br.ReadBytes(4);
                if (magic.Length != 4 || magic[0] != 'S' || magic[1] != 'J' || magic[2] != 'R' || magic[3] != '1')
                {
                    WriteStatus("ERROR: Invalid magic header in sintanjin_roads.bin");
                    return;
                }

                uint count = br.ReadUInt32();
                var list = new List<RoadRecord>((int)count);
                for (uint i = 0; i < count; i++)
                {
                    byte kind = br.ReadByte();
                    byte flags = br.ReadByte();
                    br.ReadUInt16(); // pad
                    RoadRecord rec = new RoadRecord
                    {
                        Kind = kind,
                        Flags = flags,
                        P0x = br.ReadSingle(), P0y = br.ReadSingle(), P0z = br.ReadSingle(),
                        P1x = br.ReadSingle(), P1y = br.ReadSingle(), P1z = br.ReadSingle(),
                        P2x = br.ReadSingle(), P2y = br.ReadSingle(), P2z = br.ReadSingle(),
                        P3x = br.ReadSingle(), P3y = br.ReadSingle(), P3z = br.ReadSingle(),
                        Elev0 = br.ReadSingle(), Elev1 = br.ReadSingle(),
                    };
                    list.Add(rec);
                }

                m_PendingRoads = list;
                m_PendingRoadCursor = 0;
                m_SpawnedRoadsThisRun = 0;
                m_SkippedRoadsThisRun = 0;
                m_SnappedNodesThisRun = 0;
                WriteStatus($"Queued {count:N0} backbone road/rail spans from sintanjin_roads.bin for Modification1 generation...");
            }
            catch (Exception ex)
            {
                WriteStatus($"ERROR in StartRoadSpawn: {ex}");
            }
        }

        private void ClearRoadsAndTracks()
        {
            try
            {
                m_PendingRoads = null;
                CleanupRoadDefinitions();
                using var edges = m_NetEdgeQuery.ToEntityArray(Allocator.Temp);
                using var nodes = m_NetNodeQuery.ToEntityArray(Allocator.Temp);
                if (edges.Length > 0)
                    EntityManager.AddComponent<Deleted>(edges);
                if (nodes.Length > 0)
                    EntityManager.AddComponent<Deleted>(nodes);
                WriteStatus($"Cleared {edges.Length:N0} net edges and {nodes.Length:N0} net nodes (queued Game.Common.Deleted).");
            }
            catch (Exception ex)
            {
                WriteStatus($"ERROR in ClearRoadsAndTracks: {ex}");
            }
        }

        private static long CellKey(int cx, int cz) => ((long)cx << 32) ^ (uint)cz;

        private void RebuildNodeGrid()
        {
            m_NodeGrid.Clear();
            using var nodes = m_NetNodeQuery.ToEntityArray(Allocator.Temp);
            for (int i = 0; i < nodes.Length; i++)
            {
                Entity e = nodes[i];
                Game.Net.Node nd = EntityManager.GetComponentData<Game.Net.Node>(e);
                float elevMid = 0f;
                if (EntityManager.HasComponent<Game.Net.Elevation>(e))
                {
                    float2 el = EntityManager.GetComponentData<Game.Net.Elevation>(e).m_Elevation;
                    elevMid = 0.5f * (el.x + el.y);
                }
                int cx = (int)math.floor(nd.m_Position.x * 0.25f);
                int cz = (int)math.floor(nd.m_Position.z * 0.25f);
                long key = CellKey(cx, cz);
                if (!m_NodeGrid.TryGetValue(key, out var list))
                {
                    list = new List<(Entity, float3, float)>(2);
                    m_NodeGrid[key] = list;
                }
                list.Add((e, nd.m_Position, elevMid));
            }
        }

        private bool TryFindExistingNode(float3 targetPos, float targetElev, out Entity matchEntity, out float3 matchPos)
        {
            matchEntity = Entity.Null;
            matchPos = targetPos;
            int cx = (int)math.floor(targetPos.x * 0.25f);
            int cz = (int)math.floor(targetPos.z * 0.25f);
            float bestD2 = 2.25f; // within 1.5m XZ radius

            for (int dx = -1; dx <= 1; dx++)
            {
                for (int dz = -1; dz <= 1; dz++)
                {
                    if (!m_NodeGrid.TryGetValue(CellKey(cx + dx, cz + dz), out var bucket))
                        continue;
                    for (int i = 0; i < bucket.Count; i++)
                    {
                        var (candEntity, candPos, candElev) = bucket[i];
                        if (math.abs(candElev - targetElev) > 5.5f || math.abs(candPos.y - targetPos.y) > 5.5f)
                            continue;
                        float2 d = candPos.xz - targetPos.xz;
                        float d2 = math.lengthsq(d);
                        if (d2 < bestD2)
                        {
                            bestD2 = d2;
                            matchEntity = candEntity;
                            matchPos = candPos;
                        }
                    }
                }
            }
            return matchEntity != Entity.Null;
        }

        private void ProcessRoadBatch(int batchSize)
        {
            try
            {
                TerrainHeightData hData = m_TerrainSystem.GetHeightData(false);
                if (!hData.isCreated)
                    return;

                RebuildNodeGrid();

                int end = Math.Min(m_PendingRoadCursor + batchSize, m_PendingRoads.Count);
                for (int i = m_PendingRoadCursor; i < end; i++)
                {
                    RoadRecord rec = m_PendingRoads[i];
                    if (rec.Kind >= m_NetPrefabs.Length || m_NetPrefabs[rec.Kind] == Entity.Null)
                    {
                        m_SkippedRoadsThisRun++;
                        continue;
                    }

                    float e0 = math.abs(rec.Elev0) < 0.05f ? 0f : rec.Elev0;
                    float e1 = math.abs(rec.Elev1) < 0.05f ? 0f : rec.Elev1;

                    float t0 = TerrainUtils.SampleHeight(ref hData, new float3(rec.P0x, 0f, rec.P0z));
                    float t3 = TerrainUtils.SampleHeight(ref hData, new float3(rec.P3x, 0f, rec.P3z));

                    float3 p0 = new float3(rec.P0x, t0 + e0, rec.P0z);
                    float3 p3 = new float3(rec.P3x, t3 + e1, rec.P3z);
                    if (math.lengthsq(p3.xz - p0.xz) < 1.0f)
                    {
                        m_SkippedRoadsThisRun++;
                        continue;
                    }

                    float3 p1 = new float3(rec.P1x, p0.y + (rec.P1y - rec.P0y), rec.P1z);
                    float3 p2 = new float3(rec.P2x, p3.y + (rec.P2y - rec.P3y), rec.P2z);

                    Entity startNodeEntity = Entity.Null;
                    Entity endNodeEntity = Entity.Null;
                    if (TryFindExistingNode(p0, e0, out Entity mStartE, out float3 mStartPos))
                    {
                        startNodeEntity = mStartE;
                        p0 = mStartPos;
                        m_SnappedNodesThisRun++;
                    }
                    if (TryFindExistingNode(p3, e1, out Entity mEndE, out float3 mEndPos))
                    {
                        endNodeEntity = mEndE;
                        p3 = mEndPos;
                        m_SnappedNodesThisRun++;
                    }

                    if ((startNodeEntity != Entity.Null && startNodeEntity == endNodeEntity) ||
                        math.lengthsq(p3.xz - p0.xz) < 1.0f)
                    {
                        m_SkippedRoadsThisRun++;
                        continue;
                    }

                    Bezier4x3 bezier = new Bezier4x3(p0, p1, p2, p3);
                    float3 tan0 = MathUtils.Tangent(bezier, 0f);
                    float3 tan1 = MathUtils.Tangent(bezier, 1f);
                    if (math.lengthsq(tan0) < 1e-4f) tan0 = p3 - p0;
                    if (math.lengthsq(tan1) < 1e-4f) tan1 = p3 - p0;

                    CoursePosFlags sFlags = CoursePosFlags.IsFirst;
                    CoursePosFlags eFlags = CoursePosFlags.IsLast;
                    if (math.abs(e0) > 0.05f) sFlags |= CoursePosFlags.FreeHeight;
                    if (math.abs(e1) > 0.05f) eFlags |= CoursePosFlags.FreeHeight;
                    if ((rec.Flags & 4) != 0) sFlags |= CoursePosFlags.ForceElevatedNode;
                    if ((rec.Flags & 8) != 0) eFlags |= CoursePosFlags.ForceElevatedNode;
                    if ((rec.Flags & 1) != 0)
                    {
                        sFlags |= CoursePosFlags.ForceElevatedEdge;
                        eFlags |= CoursePosFlags.ForceElevatedEdge;
                    }

                    CoursePos startPos = new CoursePos
                    {
                        m_Entity = startNodeEntity,
                        m_Position = p0,
                        m_Rotation = NetUtils.GetNodeRotation(tan0),
                        m_Elevation = new float2(e0),
                        m_CourseDelta = 0f,
                        m_SplitPosition = 0f,
                        m_Flags = sFlags,
                        m_ParentMesh = -1,
                    };

                    CoursePos endPos = new CoursePos
                    {
                        m_Entity = endNodeEntity,
                        m_Position = p3,
                        m_Rotation = NetUtils.GetNodeRotation(tan1),
                        m_Elevation = new float2(e1),
                        m_CourseDelta = 1f,
                        m_SplitPosition = 0f,
                        m_Flags = eFlags,
                        m_ParentMesh = -1,
                    };

                    NetCourse course = new NetCourse
                    {
                        m_StartPosition = startPos,
                        m_EndPosition = endPos,
                        m_Curve = bezier,
                        m_Elevation = new float2(e0, e1),
                        m_Length = MathUtils.Length(bezier),
                        m_FixedIndex = -1,
                    };

                    CreationDefinition def = new CreationDefinition
                    {
                        m_Prefab = m_NetPrefabs[rec.Kind],
                        m_SubPrefab = Entity.Null,
                        m_Original = Entity.Null,
                        m_Owner = Entity.Null,
                        m_Attached = Entity.Null,
                        m_Flags = CreationFlags.Permanent | CreationFlags.SubElevation,
                        m_RandomSeed = (i * 1973) ^ 0x51A7,
                    };

                    Entity defEntity = EntityManager.CreateEntity();
                    EntityManager.AddComponentData(defEntity, def);
                    EntityManager.AddComponentData(defEntity, course);
                    EntityManager.AddComponent<Updated>(defEntity);
                    m_CreatedRoadDefs.Add(defEntity);
                    m_SpawnedRoadsThisRun++;
                }

                m_PendingRoadCursor = end;
                if (m_PendingRoadCursor >= m_PendingRoads.Count)
                {
                    WriteStatus($"SUCCESS: Queued {m_SpawnedRoadsThisRun:N0} permanent backbone road/rail spans ({m_SnappedNodesThisRun:N0} cross-batch node snaps, skipped {m_SkippedRoadsThisRun:N0}).");
                    m_PendingRoads = null;
                }
            }
            catch (Exception ex)
            {
                WriteStatus($"ERROR in ProcessRoadBatch: {ex}");
                m_PendingRoads = null;
            }
        }
    }
}
