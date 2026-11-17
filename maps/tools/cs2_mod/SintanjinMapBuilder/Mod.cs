using Colossal.Logging;
using Game;
using Game.Modding;

namespace SintanjinMapBuilder
{
    public class Mod : IMod
    {
        public static readonly ILog Log = LogManager.GetLogger(nameof(SintanjinMapBuilder)).SetShowsErrorsInUI(false);

        public void OnLoad(UpdateSystem updateSystem)
        {
            Log.Info("[SintanjinMapBuilder] Loaded! Hotkeys: F6=ALL(Resources+Trees+Roads), Ctrl+Shift+H=BackboneRoads, Ctrl+Shift+K=ClearRoads, Ctrl+Shift+R=Resources, Ctrl+Shift+T=Trees, Ctrl+Shift+X=ClearWildTrees.");
            updateSystem.UpdateBefore<SintanjinMapBuilderSystem, Game.Tools.GenerateNodesSystem>(SystemUpdatePhase.Modification1);
        }

        public void OnDispose()
        {
            Log.Info("[SintanjinMapBuilder] Disposed.");
        }
    }
}
