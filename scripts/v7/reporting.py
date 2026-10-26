"""Predetermined result rendering; does not select or modify any model."""
import json
from .lock import BASE,ROOT


def table(results):
    lines=['| Model | Games | Accuracy | Log loss | Brier |','|---|---:|---:|---:|---:|']
    for name,r in results.items():
        lines.append(f"| {name} | {r['games']:,} | {r['accuracy']*100:.2f}% | {r['log_loss']:.5f} | {r['brier']:.5f} |")
    return '\n'.join(lines)


def write_final(report):
    rows=table(report['metrics'])
    ablation=table(report['ablation'])
    text='# Nexus Sight v7 — single frozen 2026 evaluation\n\n'+rows+'\n\n## Frozen-feature ablations\n\n'+ablation
    text+='\n\nAll choices were frozen before parsing 2026. No model changes followed this evaluation. '
    text+='Results cover the locked yearly CSV snapshot, not necessarily a completed 2026 season. '
    text+='Secondary games update ratings only. The estimator remains fitted through 2024; 2025 was validation/calibration only.\n\n'
    text+='## Conditional uncertainty vs Elo\n\n'
    for name,r in report['metrics'].items():
        if 'vs_Elo' in r:
            interval=r['vs_Elo']['log_loss_improvement']
            text+=f"- {name}: log-loss improvement 95% interval [{interval[0]:.5f}, {interval[1]:.5f}].\n"
    text+='\n## Limitations\n\n'+'\n'.join('- '+v for v in report['limitations'])+'\n'
    (BASE/'FINAL_REPORT.md').write_text(text,encoding='utf-8')
    (BASE/'final_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    readme=ROOT/'README.md'
    content=readme.read_text(encoding='utf-8')
    a='<!-- V7_FINAL_START -->';b='<!-- V7_FINAL_END -->'
    if a not in content or b not in content:raise ValueError('README result markers absent')
    start=content.index(a)+len(a);end=content.index(b,start)
    block='\n\n'+rows+'\n\n[Full frozen report](scripts/v7/FINAL_REPORT.md) · [Calibration plot](scripts/v7/final_calibration.png)\n\n'
    readme.write_text(content[:start]+block+content[end:],encoding='utf-8')
