"""한국 고속도로 소품 세트: 6개 생성기를 차례로 final 게이트에 돌린다 (편의 스크립트, 자체는 에셋을 만들지 않음).

  python projects/highway-props/highway_props_cs2.py          # 키트 루트에서
"""
import os
import subprocess
import sys

GENERATORS = ["noise_wall_clear_cs2.py", "noise_wall_metal_cs2.py", "sign_gantry_cs2.py",
              "sign_side_cs2.py", "guardrail_wbeam_cs2.py", "guardrail_wbeam_double_cs2.py",
              "median_barrier_cs2.py"]
KIT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    for g in GENERATORS:
        subprocess.run([sys.executable, "tools/agent.py", "cycle", "--project", "highway-props", "--generator", g,
                        "--mode", "final", "--label", "final", "--brief", "--json"], cwd=KIT, check=False)
