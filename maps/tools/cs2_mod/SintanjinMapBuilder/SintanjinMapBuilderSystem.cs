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

    public partial class SintanjinMapBuilderSystem : GameSystemBase
    {
        private TerrainSystem m_TerrainSystem;
        private WaterSystem m_WaterSystem;
        private NaturalResourceSystem m_NaturalResourceSystem;
        private GroundWaterSystem m_GroundWaterSystem;
        private PrefabSystem m_PrefabSystem;
        private WindSimulationSystem m_WindSystem;

        private EntityQuery m_TreePrefabQuery;
        private EntityQuery m_WildTreeQuery;

        private readonly List<Entity> m_ConiferPrefabs = new List<Entity>();
        private readonly List<Entity> m_BroadleafPrefabs = new List<Entity>();
        private readonly List<Entity> m_RiparianPrefabs = new List<Entity>();
        private readonly List<Entity> m_ShrubPrefabs = new List<Entity>();
        private readonly List<Entity> m_AllValidTrees = new List<Entity>();
        private readonly HashSet<Entity> m_PrefabsWithSeed = new HashSet<Entity>();

        private List<TreeRecord> m_PendingTrees;
        private int m_PendingCursor;
        private int m_SpawnedThisRun;
        private int m_SkippedWaterThisRun;
        private bool m_LoggedPrefabs;

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
            m_WindSystem = World.GetOrCreateSystemManaged<WindSimulationSystem>();

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

            WriteStatus("SintanjinMapBuilderSystem initialized (Modification1). Hotkeys: F6=ALL(Resources+Trees), Ctrl+Shift+R=Resources, Ctrl+Shift+T=Trees, Ctrl+Shift+X=ClearWildTrees, Ctrl+Shift+W=Wind(NNW->SSE).");
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

            // Process batched tree planting cleanly without freezing the frame
            if (m_PendingTrees != null)
            {
                ProcessTreeBatch(2200);
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
                    WriteStatus("Hotkey F6 -> Full Pipeline (Resources + Realistic Forest Trees)");
                    ApplyNaturalResources();
                    StartTreeSpawn();
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
                if (ctrl && shift && kb.wKey.wasPressedThisFrame)
                {
                    WriteStatus("Hotkey Ctrl+Shift+W -> Setting Wind NNW->SSE");
                    ApplyWind();
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
                    if (cmd.Contains("CLEAR"))
                        ClearWildTrees();
                    if (cmd.Contains("ALL") || cmd.Contains("RESOURCE"))
                        ApplyNaturalResources();
                    if (cmd.Contains("ALL") || cmd.Contains("TREE"))
                        StartTreeSpawn();
                    if (cmd.Contains("WIND"))
                        ApplyWind();
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

        // docs/wind_direction_plan.md: wind blows FROM 337.5 deg (NNW) TOWARD SSE.
        // Vector = downwind direction (AirPollutionMoveJob samples cellCenter - speed*wind), x=east, z=north
        // (generator row 0 = +z = north). Magnitude 0.389 = vanilla default |(0.275,0.275)|; pressure 40 = vanilla.
        private static readonly float2 kSintanjinWind = new float2(0.149f, -0.359f);

        private void ApplyWind()
        {
            try
            {
                float2 before = m_WindSystem.constantWind;
                m_WindSystem.SetWind(kSintanjinWind, 40f);
                float2 now = m_WindSystem.constantWind;
                WriteStatus($"SUCCESS: Wind set (before=({before.x:F3},{before.y:F3}), now=({now.x:F3},{now.y:F3}), x=east z=north, NNW->SSE).");
            }
            catch (Exception ex)
            {
                WriteStatus($"ERROR in ApplyWind: {ex}");
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
                    // Archetype ships Decoration enabled; vanilla placement (GenerateObjectsSystem) disables it.
                    // Enabled = decorative: AreaResourceSystem skips it for wood and TreeGrowthSystem never grows it.
                    ecb.SetComponentEnabled<Decoration>(e, false);
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
    }
}
