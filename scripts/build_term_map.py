"""
术语映射构建脚本 — 从 full_book.json + 精选节点列表生成 term_map.json。

输出为 list-of-dicts 格式，每个条目对应 TermMapping dataclass 的所有字段。

用法:
    python scripts/build_term_map.py --full_book ../../kg_system/medical/data/full_book.json

输出: data/ontology/term_map.json
"""

import json
import os
import sys
from collections import defaultdict
from typing import Any


# ═══════════════════════════════════════════════════════════════
# 精选节点列表（来自旧项目的 generate_term_map.py NODES + ALIASES）
# 这些节点经过了人工筛选和中文标注，优先级高于 full_book.json 的自动提取
# ═══════════════════════════════════════════════════════════════

CURATED_NODES: list[dict[str, Any]] = [
    # ── L0: 动作 / 暴露 ──────────────────────────────────────
    {"name": "Repeated_Lumbar_Flexion", "layer": "L0", "type": "action", "subtype": "", "description": "反复腰椎屈曲动作，是椎间盘突出的主要诱因之一。"},
    {"name": "Prolonged_Sitting", "layer": "L0", "type": "exposure", "subtype": "", "description": "长时间坐着，尤其是在腰椎屈曲的姿势下，与椎间盘突出风险增加相关。"},
    {"name": "Sit_Up", "layer": "L0", "type": "action", "subtype": "", "description": "仰卧起坐运动，包括屈膝或直腿的变体。"},
    {"name": "Stoop_Lifting", "layer": "L0", "type": "action", "subtype": "", "description": "弯腰（脊柱屈曲）抬举重物，而非屈髋屈膝。"},
    {"name": "Morning_Flexion", "layer": "L0", "type": "action", "subtype": "", "description": "早晨起床后不久进行脊柱屈曲动作。"},
    {"name": "Hip_Hinge_Lifting", "layer": "L0", "type": "action", "subtype": "", "description": "髋部铰链式抬举，在抬举时保持腰椎中立位，通过髋关节屈曲来完成动作。"},
    {"name": "Lumbar_Flexion", "layer": "L0", "type": "action", "subtype": "", "description": "腰椎屈曲动作，特别是指脊柱的完全屈曲，是椎间盘损伤的主要机制。"},
    {"name": "Backward_Bending", "layer": "L0", "type": "action", "subtype": "", "description": "脊柱后伸/后弯动作"},
    {"name": "Walking_Extension", "layer": "L0", "type": "exposure", "subtype": "", "description": "行走时腰椎进入后伸位"},
    {"name": "Standing_Extended", "layer": "L0", "type": "exposure", "subtype": "", "description": "长时间站立后伸姿势"},
    {"name": "Quadratus_Lumborum", "layer": "L0", "type": "anatomy_variation", "subtype": "", "description": "腰方肌，主要脊柱稳定肌。"},
    {"name": "Multifidus", "layer": "L0", "type": "anatomy_variation", "subtype": "", "description": "多裂肌，脊柱后方稳定器。"},
    {"name": "Lumbar_Flexion_Mobility_Exercise", "layer": "L0", "type": "action", "subtype": "", "description": "旨在增加腰椎屈曲活动度的练习。"},
    # ── L1: 负荷 / 力学 ──────────────────────────────────────
    {"name": "Flexion_Compression", "layer": "L1", "type": "load", "subtype": "flexion_compression", "description": "脊柱在屈曲状态下承受压缩负荷，是导致后侧椎间盘突出的典型力学机制。"},
    {"name": "Disc_Shear", "layer": "L1", "type": "load", "subtype": "shear", "description": "作用于椎间关节的剪切力，脊柱在完全屈曲时剪切力显著增加。"},
    {"name": "Repetitive_Low_Load", "layer": "L1", "type": "load", "subtype": "repetitive_low_load", "description": "反复施加的低水平压缩负荷，仅需约800-1000N，配合反复屈曲即可导致椎间盘突出。"},
    {"name": "Sitting_Disc_Load", "layer": "L1", "type": "load", "subtype": "sustained_posture", "description": "坐姿下椎间盘内压力增高，并对椎间盘后部纤维环产生持续的应力。"},
    {"name": "Sustained_Posture", "layer": "L1", "type": "load", "subtype": "sustained_posture", "description": "长时间保持屈曲姿势，如坐姿，导致被动组织蠕变，降低其失效耐受力。"},
    {"name": "Spine_Compression", "layer": "L1", "type": "load", "subtype": "", "description": "脊柱承受的轴向压缩力，在椎间盘屈曲时显著增加纤维环后部的应力。"},
    {"name": "Sustained_Posture_Load", "layer": "L1", "type": "load", "subtype": "sustained_posture", "description": "持续姿势导致营养交换受限与组织退变"},
    {"name": "Loaded_Spine_Motion", "layer": "L1", "type": "load", "subtype": "flexion_compression", "description": "在脊柱承受外部负荷时进行屈伸运动。"},
    {"name": "High_Spine_Power", "layer": "L1", "type": "load", "subtype": "repetitive_low_load", "description": "高速脊柱弯曲运动伴随肌肉力量会增加损伤风险。"},
    {"name": "Increased_IAP", "layer": "L1", "type": "load", "subtype": "", "description": "腹内压增高，可增加躯干刚度。"},
    {"name": "Extension_Compression", "layer": "L1", "type": "load", "subtype": "extension_compression", "description": "后伸+压缩负荷，集中于小关节"},
    # ── L2: 病理 ─────────────────────────────────────────────
    {"name": "Disc_Herniation", "layer": "L2", "type": "pathology", "subtype": "", "description": "椎间盘髓核突破纤维环，常为后外侧型，由反复屈曲和压缩负荷引起。"},
    {"name": "Endplate_Fracture", "layer": "L2", "type": "pathology", "subtype": "", "description": "椎体终板骨折，常由轴向压缩负荷导致，可引发Schmorl结节。"},
    {"name": "Annulus_Delamination", "layer": "L2", "type": "pathology", "subtype": "", "description": "纤维环分层，胶原纤维层之间分离，是椎间盘突出的早期阶段。"},
    {"name": "Spondylolisthesis", "layer": "L2", "type": "pathology", "subtype": "", "description": "脊椎滑脱，通常由椎弓峡部骨折引起，与剪切力负荷有关。"},
    {"name": "Disc_Bulge", "layer": "L2", "type": "pathology", "subtype": "", "description": "椎间盘纤维环向外膨出，但未完全破裂，是椎间盘突出的前期或较轻形式。"},
    {"name": "Spinal_Hinge", "layer": "L2", "type": "pathology", "subtype": "", "description": "脊柱铰链现象，某一节段承担不成比例的大幅运动。"},
    {"name": "Posterior_Disc_Herniation", "layer": "L2", "type": "pathology", "subtype": "", "description": "髓核向后突破纤维环。"},
    {"name": "Facet_Joint_Arthritis", "layer": "L2", "type": "pathology", "subtype": "", "description": "小关节关节炎。"},
    {"name": "Spinal_Stenosis", "layer": "L2", "type": "pathology", "subtype": "", "description": "椎管狭窄。"},
    {"name": "Facet_Impingement", "layer": "L2", "type": "pathology", "subtype": "", "description": "小关节撞击/卡压"},
    {"name": "Facet_Irritation", "layer": "L2", "type": "pathology", "subtype": "", "description": "小关节激惹/炎症"},
    {"name": "Annulus_Tear", "layer": "L2", "type": "pathology", "subtype": "", "description": "纤维环撕裂，常由反复屈曲压缩引起"},
    {"name": "Disc_Degeneration", "layer": "L2", "type": "pathology", "subtype": "", "description": "椎间盘退变，与长期低负荷重复应力相关"},
    # ── L3: 机制 ─────────────────────────────────────────────
    {"name": "Nerve_Root_Compression", "layer": "L3", "type": "mechanism", "subtype": "", "description": "突出的椎间盘或狭窄的椎间孔直接压迫神经根。"},
    {"name": "Instability", "layer": "L3", "type": "mechanism", "subtype": "", "description": "由于组织损伤（如韧带松弛、椎间盘高度丢失）导致的节段性不稳定，引发异常微动和疼痛。"},
    {"name": "Inflammation", "layer": "L3", "type": "mechanism", "subtype": "", "description": "髓核突破纤维环后，作为异物被免疫系统识别，引发局部炎症反应。"},
    {"name": "Central_Sensitization", "layer": "L3", "type": "mechanism", "subtype": "", "description": "持续的疼痛信号导致中枢神经系统对痛觉信号放大和敏化。"},
    {"name": "Gluteal_Amnesia", "layer": "L3", "type": "mechanism", "subtype": "", "description": "臀肌失忆症，髋伸展时臀肌无法被充分激活。"},
    {"name": "Segmental_Instability", "layer": "L3", "type": "mechanism", "subtype": "", "description": "节段性稳定性丧失。"},
    # ── L4: 症状 ─────────────────────────────────────────────
    {"name": "Radicular_Pain", "layer": "L4", "type": "symptom", "subtype": "", "description": "由于神经根受刺激或压迫引起的放射性疼痛，常沿坐骨神经通路放散。"},
    {"name": "Low_Back_Pain", "layer": "L4", "type": "symptom", "subtype": "", "description": "局限于腰背部的疼痛，可能与椎间盘、关节突关节或肌肉韧带损伤有关。"},
    {"name": "Morning_Stiffness", "layer": "L4", "type": "symptom", "subtype": "", "description": "晨起时疼痛和僵硬感加重，与夜间仰卧时椎间盘吸水膨胀有关。"},
    {"name": "Radicular_Pain_Sciatica", "layer": "L4", "type": "symptom", "subtype": "", "description": "神经根受压引起的放射性腿部疼痛。"},
    {"name": "Mechanical_Back_Pain", "layer": "L4", "type": "symptom", "subtype": "", "description": "与活动相关的背部疼痛。"},
    {"name": "Walking_Intolerance", "layer": "L4", "type": "symptom", "subtype": "", "description": "行走不能耐受，后伸加重"},
    # ── L5: 体征 / 测试 ──────────────────────────────────────
    {"name": "Flexion_Intolerance", "layer": "L5", "type": "sign", "subtype": "", "description": "患者在脊柱进行屈曲动作或体位时诱发的疼痛。"},
    {"name": "SLR_Positive", "layer": "L5", "type": "sign", "subtype": "", "description": "直腿抬高试验阳性，提示坐骨神经或神经根受到牵拉或压迫。"},
    {"name": "Sitting_Intolerance", "layer": "L5", "type": "symptom", "subtype": "", "description": "无法耐受长时间坐姿，坐位会加剧疼痛，常见于椎间盘源性疼痛。"},
    {"name": "Prone_Extension_Relief", "layer": "L5", "type": "test", "subtype": "", "description": "俯卧位脊柱后伸时患者报告疼痛减轻，是椎间盘源性疼痛的强体征。"},
    {"name": "Flexion_Relaxation_Phenomenon", "layer": "L5", "type": "test", "subtype": "", "description": "完全屈曲时背部伸肌肌电活动突然静默。"},
    {"name": "Aberrant_Motion_Catch", "layer": "L5", "type": "sign", "subtype": "", "description": "脊柱出现异常顿挫运动，提示节段不稳定。"},
    {"name": "MRI_Disc_Bulge", "layer": "L5", "type": "test", "subtype": "", "description": "MRI显示椎间盘膨出，但与症状相关性弱"},
    {"name": "Extension_Pain", "layer": "L5", "type": "sign", "subtype": "", "description": "后伸时诱发疼痛"},
    {"name": "Facet_Tenderness", "layer": "L5", "type": "sign", "subtype": "", "description": "小关节区域压痛"},
    # ── L6: 诊断 ─────────────────────────────────────────────
    {"name": "Discogenic_Pain", "layer": "L6", "type": "diagnosis", "subtype": "", "description": "源于椎间盘内部结构紊乱或损伤的疼痛，通常在脊柱屈曲时加重。"},
    {"name": "Lumbopelvic_Rhythm", "layer": "L6", "type": "diagnosis", "subtype": "", "description": "腰盆节律，McGill认为这是一个临床误区。"},
    {"name": "Discogenic_Disorder_Diagnosis", "layer": "L6", "type": "diagnosis", "subtype": "", "description": "椎间盘源性疼痛诊断。"},
    {"name": "Facet_Joint_Syndrome", "layer": "L6", "type": "diagnosis", "subtype": "", "description": "小关节综合征诊断"},
    # ── L7: 干预 ─────────────────────────────────────────────
    {"name": "Avoid_Spine_Flexion", "layer": "L7", "type": "intervention", "subtype": "remove_cause", "description": "避免脊柱屈曲动作和姿势，以消除疼痛和损伤的诱因。"},
    {"name": "Core_Stabilization_Exercise", "layer": "L7", "type": "intervention", "subtype": "exercise_therapy", "description": "核心稳定训练，旨在增强躯干肌肉的耐力，以稳定脊柱，减少微动和疼痛。"},
    {"name": "Cat_Camel_Exercise", "layer": "L7", "type": "intervention", "subtype": "exercise_therapy", "description": "猫驼式运动，在四点跪位下进行的脊柱屈伸活动，作为无负荷的脊柱活动度练习。"},
    {"name": "Neutral_Spine_Posture", "layer": "L7", "type": "intervention", "subtype": "remove_cause", "description": "教导患者在日常生活中保持腰椎中立位，通过屈髋代替屈腰。"},
    {"name": "Big_Three_Exercises", "layer": "L7", "type": "intervention", "subtype": "exercise_therapy", "description": "McGill推荐的三项核心训练：改良卷腹、侧桥和鸟狗式。"},
    {"name": "Prone_Extension_Exercise", "layer": "L7", "type": "intervention", "subtype": "exercise_therapy", "description": "俯卧位静力性伸展，用于减轻急性椎间盘后部突出的压力。"},
    {"name": "Abdominal_Bracing", "layer": "L7", "type": "intervention", "subtype": "exercise_therapy", "description": "腹部支撑，对称性地激活所有腹部肌层以形成核心刚度。"},
    {"name": "Abdominal_Hollowing", "layer": "L7", "type": "intervention", "subtype": "exercise_therapy", "description": "腹部内收动作，被McGill证明降低脊柱稳定性。"},
    {"name": "Flexion_Stretching", "layer": "L7", "type": "intervention", "subtype": "exercise_therapy", "description": "屈曲拉伸（如抱膝触胸），常被错误推荐但会加剧损伤。"},
    {"name": "Endurance_Training", "layer": "L7", "type": "intervention", "subtype": "exercise_therapy", "description": "耐力训练对减少未来背痛发作风险更具保护作用。"},
    {"name": "Golfers_Lift", "layer": "L7", "type": "intervention", "subtype": "remove_cause", "description": "高尔夫式提举法，安全拾取地面轻物。"},
    {"name": "Avoid_Early_Morning_Flexion", "layer": "L7", "type": "intervention", "subtype": "remove_cause", "description": "避免晨起后立即进行脊柱屈曲，损伤风险最高。"},
    {"name": "Spine_Mobilizing_Exercises", "layer": "L7", "type": "intervention", "subtype": "exercise_therapy", "description": "如猫驼式，无压缩负荷下的活动度训练。"},
    {"name": "Directed_Stretching_Exercises", "layer": "L7", "type": "intervention", "subtype": "exercise_therapy", "description": "特定方向牵伸。"},
    {"name": "Nerve_Flossing", "layer": "L7", "type": "intervention", "subtype": "exercise_therapy", "description": "神经滑动练习。"},
    {"name": "Surgery", "layer": "L7", "type": "intervention", "subtype": "surgery", "description": "手术治疗。"},
    {"name": "Avoid_Flexion", "layer": "L7", "type": "intervention", "subtype": "remove_cause", "description": "避免腰椎屈曲动作"},
    {"name": "Extension_Mobility_Exercise", "layer": "L7", "type": "intervention", "subtype": "exercise_therapy", "description": "后伸活动度训练"},
    {"name": "Avoid_Extension", "layer": "L7", "type": "intervention", "subtype": "remove_cause", "description": "避免重复后伸动作"},
    {"name": "NSAIDs", "layer": "L7", "type": "intervention", "subtype": "medication", "description": "非甾体抗炎药"},
    {"name": "Muscle_Relaxants", "layer": "L7", "type": "intervention", "subtype": "medication", "description": "肌肉松弛剂"},
    {"name": "Acetaminophen", "layer": "L7", "type": "intervention", "subtype": "medication", "description": "对乙酰氨基酚"},
    {"name": "Gabapentinoid", "layer": "L7", "type": "intervention", "subtype": "medication", "description": "加巴喷丁类药物"},
    {"name": "Epidural_Steroid_Injection", "layer": "L7", "type": "intervention", "subtype": "medication", "description": "硬膜外类固醇注射"},
    {"name": "Manual_Therapy", "layer": "L7", "type": "intervention", "subtype": "passive_therapy", "description": "手法治疗"},
    {"name": "Traction", "layer": "L7", "type": "intervention", "subtype": "passive_therapy", "description": "腰椎牵引"},
    {"name": "Heat_Therapy", "layer": "L7", "type": "intervention", "subtype": "passive_therapy", "description": "热敷治疗"},
    {"name": "Ice_Therapy", "layer": "L7", "type": "intervention", "subtype": "passive_therapy", "description": "冷敷治疗"},
    {"name": "TENS", "layer": "L7", "type": "intervention", "subtype": "passive_therapy", "description": "经皮神经电刺激"},
    {"name": "Acupuncture", "layer": "L7", "type": "intervention", "subtype": "passive_therapy", "description": "针灸"},
    {"name": "Microdiscectomy", "layer": "L7", "type": "intervention", "subtype": "surgery", "description": "显微椎间盘切除术"},
    {"name": "Spinal_Fusion", "layer": "L7", "type": "intervention", "subtype": "surgery", "description": "脊柱融合术"},
    {"name": "Laminectomy", "layer": "L7", "type": "intervention", "subtype": "surgery", "description": "椎板切除术"},
    # ── L8: 结果 ─────────────────────────────────────────────
    {"name": "Pain_Relief", "layer": "L8", "type": "outcome", "subtype": "", "description": "疼痛减轻，是康复治疗的主要目标之一。"},
    {"name": "Functional_Recovery", "layer": "L8", "type": "outcome", "subtype": "", "description": "恢复无痛的日常活动、工作和运动能力。"},
]

# 中文别名映射（来自旧项目 generate_term_map.py 的 ALIASES）
CURATED_ALIASES: dict[str, str] = {
    "Repeated_Lumbar_Flexion": "反复腰椎屈曲",
    "Prolonged_Sitting": "久坐",
    "Sit_Up": "仰卧起坐",
    "Stoop_Lifting": "弯腰抬举",
    "Morning_Flexion": "早晨屈曲",
    "Flexion_Compression": "屈曲压缩负荷",
    "Disc_Shear": "椎间盘剪切力",
    "Repetitive_Low_Load": "重复低负荷",
    "Disc_Herniation": "椎间盘突出",
    "Endplate_Fracture": "终板骨折",
    "Annulus_Delamination": "纤维环分层",
    "Spondylolisthesis": "脊椎滑脱",
    "Nerve_Root_Compression": "神经根压迫",
    "Instability": "节段性不稳定",
    "Discogenic_Pain": "椎间盘源性疼痛",
    "Radicular_Pain": "放射性腿痛",
    "Flexion_Intolerance": "屈曲不耐受",
    "SLR_Positive": "直腿抬高试验阳性",
    "Sitting_Intolerance": "久坐不耐受",
    "Avoid_Spine_Flexion": "避免脊柱屈曲",
    "Core_Stabilization_Exercise": "核心稳定训练",
    "Hip_Hinge_Lifting": "髋铰链抬举",
    "Cat_Camel_Exercise": "猫驼式运动",
    "Pain_Relief": "疼痛缓解",
    "Lumbar_Flexion": "腰椎屈曲",
    "Sustained_Posture": "持续姿势负荷",
    "Spine_Compression": "脊柱压缩",
    "Disc_Bulge": "椎间盘膨出",
    "Inflammation": "炎症",
    "Central_Sensitization": "中枢致敏",
    "Low_Back_Pain": "腰痛",
    "Morning_Stiffness": "晨僵",
    "Prone_Extension_Relief": "俯卧后伸缓解",
    "Neutral_Spine_Posture": "中立位姿势",
    "Big_Three_Exercises": "McGill三大训练",
    "Prone_Extension_Exercise": "俯卧后伸练习",
    "Functional_Recovery": "功能恢复",
    "Abdominal_Bracing": "腹部支撑",
    "Abdominal_Hollowing": "腹部内收",
    "Spinal_Hinge": "脊柱铰链",
    "Quadratus_Lumborum": "腰方肌",
    "Multifidus": "多裂肌",
    "Gluteal_Amnesia": "臀肌失忆",
    "Flexion_Stretching": "屈曲拉伸",
    "Endurance_Training": "耐力训练",
    "Golfers_Lift": "高尔夫拾物法",
    "Flexion_Relaxation_Phenomenon": "屈曲放松现象",
    "Lumbopelvic_Rhythm": "腰盆节律",
    "Spinal_Stenosis": "椎管狭窄",
    "Aberrant_Motion_Catch": "异常顿挫运动",
    "Spine_Mobilizing_Exercises": "脊柱活动度训练",
    "Directed_Stretching_Exercises": "定向牵伸",
    "Nerve_Flossing": "神经滑动练习",
    "Surgery": "手术",
    "Annulus_Tear": "纤维环撕裂",
    "Disc_Degeneration": "椎间盘退变",
    "MRI_Disc_Bulge": "MRI椎间盘膨出",
    "Backward_Bending": "后伸动作",
    "Walking_Extension": "行走后伸",
    "Standing_Extended": "站立后伸",
    "Extension_Compression": "后伸压缩负荷",
    "Facet_Impingement": "小关节撞击",
    "Facet_Irritation": "小关节激惹",
    "Facet_Joint_Syndrome": "小关节综合征",
    "Extension_Pain": "后伸痛",
    "Facet_Tenderness": "小关节压痛",
    "Walking_Intolerance": "行走不耐受",
    "Extension_Mobility_Exercise": "后伸活动度训练",
    "Avoid_Extension": "避免后伸",
    "NSAIDs": "非甾体抗炎药",
    "Muscle_Relaxants": "肌肉松弛剂",
    "Acetaminophen": "对乙酰氨基酚",
    "Gabapentinoid": "加巴喷丁类药物",
    "Epidural_Steroid_Injection": "硬膜外类固醇注射",
    "Manual_Therapy": "手法治疗",
    "Traction": "腰椎牵引",
    "Heat_Therapy": "热敷",
    "Ice_Therapy": "冷敷",
    "TENS": "经皮神经电刺激",
    "Acupuncture": "针灸",
    "Microdiscectomy": "显微椎间盘切除术",
    "Spinal_Fusion": "脊柱融合术",
    "Laminectomy": "椎板切除术",
}


def extract_curation_level(node_name: str) -> str:
    """判断精加工程度。"""
    if node_name in CURATED_ALIASES:
        return "curated"
    return "auto_zh"


def extract_zh_academic(node_name: str) -> str:
    """提取中文学术术语。"""
    return CURATED_ALIASES.get(node_name, "")


def extract_zh_common(node_name: str) -> str:
    """提取日常用语（暂从 common_names.json 加载）。"""
    return ""


def build_entity_mapping(entity: dict, edges_index: dict[str, list[dict]]) -> dict:
    """从 full_book.json 的单个实体构建 TermMapping dict。"""
    name = entity["name"]
    source_edges = edges_index.get(name, [])

    return {
        "node_name": name,
        "zh_academic": extract_zh_academic(name),
        "zh_common": "",
        "layer": entity.get("layer", ""),
        "node_type": entity.get("type", "generic"),
        "node_subtype": entity.get("subtype", ""),
        "description_en": entity.get("description", ""),
        "description_zh": "",
        "curation_level": extract_curation_level(name),
        "source": "full_book.json",
        "source_edges": json.dumps(source_edges, ensure_ascii=False),
        "aliases": json.dumps([name], ensure_ascii=False),
    }


def build_curated_mapping(node: dict) -> dict:
    """从精选节点构建 TermMapping dict（覆盖或新增）。"""
    name = node["name"]
    description = node.get("description", "")
    # 中英文描述：旧项目 description 是中文，我们用 description_en 存英文占位符
    return {
        "node_name": name,
        "zh_academic": CURATED_ALIASES.get(name, ""),
        "zh_common": "",
        "layer": node.get("layer", ""),
        "node_type": node.get("type", "generic"),
        "node_subtype": node.get("subtype", ""),
        "description_en": description,
        "description_zh": description,
        "curation_level": "curated",
        "source": "patch_list",
        "source_edges": "[]",
        "aliases": json.dumps([name], ensure_ascii=False),
    }


def build_edges_index(edges: list[dict]) -> dict[str, list[dict]]:
    """构建边倒排索引：node_name → 以该节点为 source 的边列表。"""
    index: dict[str, list[dict]] = defaultdict(list)
    for edge in edges:
        source = edge.get("source", "")
        if source:
            index[source].append({
                "relation": edge.get("relation", ""),
                "target": edge.get("target", ""),
                "evidence_text": edge.get("evidence", ""),
                "source_ref": edge.get("source_ref", ""),
                "confidence": edge.get("confidence", 1.0),
            })
    return dict(index)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Build term_map.json from full_book.json")
    parser.add_argument(
        "--full_book",
        default=r"d:\kg_system\medical\data\full_book.json",
        help="Path to full_book.json (old project data)",
    )
    parser.add_argument(
        "--common_names",
        default="",
        help="Path to common_names.json (optional, for zh_common filling)",
    )
    parser.add_argument(
        "-o", "--output",
        default="",
        help="Output path (default: data/ontology/term_map.json)",
    )
    args = parser.parse_args()

    # ── 1. 读取 full_book.json ────────────────────────────────
    if not os.path.exists(args.full_book):
        print(f"❌ 未找到 full_book.json: {args.full_book}")
        sys.exit(1)

    with open(args.full_book, "r", encoding="utf-8") as f:
        book = json.load(f)

    entities = book.get("entities", [])
    edges = book.get("edges", [])
    print(f"📄 full_book.json: {len(entities)} entities, {len(edges)} edges")

    # ── 2. 构建边索引 ────────────────────────────────────────
    edges_index = build_edges_index(edges)

    # ── 3. 构建实体映射 ──────────────────────────────────────
    entity_dict: dict[str, dict] = {}
    for entity in entities:
        m = build_entity_mapping(entity, edges_index)
        entity_dict[m["node_name"]] = m

    print(f"📝 从 full_book.json 构建了 {len(entity_dict)} 个基础映射")

    # ── 4. 合并精选节点（覆盖/新增） ──────────────────────────
    override_count = 0
    new_count = 0
    for node in CURATED_NODES:
        name = node["name"]
        curated = build_curated_mapping(node)
        if name in entity_dict:
            # 保留 source_edges 不被 curated 覆盖
            curated["source_edges"] = entity_dict[name]["source_edges"]
            override_count += 1
        else:
            new_count += 1
        entity_dict[name] = curated

    print(f"🔄 精选节点覆盖: {override_count}, 新增: {new_count}")

    # ── 5. 输出 ──────────────────────────────────────────────
    output_path = args.output or os.path.join(
        os.path.dirname(__file__), "..", "data", "ontology", "term_map.json"
    )
    output_path = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    result = list(entity_dict.values())
    # 按层级排序（L0-L8，其他排最后）
    def layer_sort_key(m: dict) -> tuple:
        l = m.get("layer", "")
        if l.startswith("L") and l[1:].isdigit():
            return (0, int(l[1:]))
        return (1, l)

    result.sort(key=layer_sort_key)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"✅ term_map.json 已生成: {output_path}")
    print(f"   共 {len(result)} 个术语映射条目")


if __name__ == "__main__":
    main()