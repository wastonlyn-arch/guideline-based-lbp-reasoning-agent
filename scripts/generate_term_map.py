"""
从旧项目 init_data.py 提取节点中英对照，生成 term_map.json。

用法：python scripts/generate_term_map.py
输出：data/ontology/term_map.json
"""
import json, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# 直接复制旧项目 init_data.py 的 NODES 和 ALIASES 数据
NODES = [
    {"name": "Repeated_Lumbar_Flexion", "layer": "L0", "type": "action", "subtype": "None", "description": "反复腰椎屈曲动作，是椎间盘突出的主要诱因之一。"},
    {"name": "Prolonged_Sitting", "layer": "L0", "type": "exposure", "subtype": "None", "description": "长时间坐着，尤其是在腰椎屈曲的姿势下，与椎间盘突出风险增加相关。"},
    {"name": "Sit_Up", "layer": "L0", "type": "action", "subtype": "None", "description": "仰卧起坐运动，包括屈膝或直腿的变体。"},
    {"name": "Stoop_Lifting", "layer": "L0", "type": "action", "subtype": "None", "description": "弯腰（脊柱屈曲）抬举重物，而非屈髋屈膝。"},
    {"name": "Morning_Flexion", "layer": "L0", "type": "action", "subtype": "None", "description": "早晨起床后不久进行脊柱屈曲动作。"},
    {"name": "Flexion_Compression", "layer": "L1", "type": "load", "subtype": "flexion_compression", "description": "脊柱在屈曲状态下承受压缩负荷，是导致后侧椎间盘突出的典型力学机制。"},
    {"name": "Disc_Shear", "layer": "L1", "type": "load", "subtype": "shear", "description": "作用于椎间关节的剪切力，脊柱在完全屈曲时剪切力显著增加。"},
    {"name": "Repetitive_Low_Load", "layer": "L1", "type": "load", "subtype": "repetitive_low_load", "description": "反复施加的低水平压缩负荷，仅需约800-1000N，配合反复屈曲即可导致椎间盘突出。"},
    {"name": "Sitting_Disc_Load", "layer": "L1", "type": "load", "subtype": "sustained_posture", "description": "坐姿下椎间盘内压力增高，并对椎间盘后部纤维环产生持续的应力。"},
    {"name": "Disc_Herniation", "layer": "L2", "type": "pathology", "subtype": "None", "description": "椎间盘髓核突破纤维环，常为后外侧型，由反复屈曲和压缩负荷引起。"},
    {"name": "Endplate_Fracture", "layer": "L2", "type": "pathology", "subtype": "None", "description": "椎体终板骨折，常由轴向压缩负荷导致，可引发Schmorl结节。"},
    {"name": "Annulus_Delamination", "layer": "L2", "type": "pathology", "subtype": "None", "description": "纤维环分层，胶原纤维层之间分离，是椎间盘突出的早期阶段。"},
    {"name": "Spondylolisthesis", "layer": "L2", "type": "pathology", "subtype": "None", "description": "脊椎滑脱，通常由椎弓峡部骨折引起，与剪切力负荷有关。"},
    {"name": "Nerve_Root_Compression", "layer": "L3", "type": "mechanism", "subtype": "None", "description": "突出的椎间盘或狭窄的椎间孔直接压迫神经根。"},
    {"name": "Instability", "layer": "L3", "type": "mechanism", "subtype": "None", "description": "由于组织损伤（如韧带松弛、椎间盘高度丢失）导致的节段性不稳定，引发异常微动和疼痛。"},
    {"name": "Discogenic_Pain", "layer": "L6", "type": "diagnosis", "subtype": "None", "description": "源于椎间盘内部结构紊乱或损伤的疼痛，通常在脊柱屈曲时加重。"},
    {"name": "Radicular_Pain", "layer": "L4", "type": "symptom", "subtype": "None", "description": "由于神经根受刺激或压迫引起的放射性疼痛，常沿坐骨神经通路放散。"},
    {"name": "Flexion_Intolerance", "layer": "L5", "type": "sign", "subtype": "None", "description": "患者在脊柱进行屈曲动作或体位时诱发的疼痛。"},
    {"name": "SLR_Positive", "layer": "L5", "type": "sign", "subtype": "None", "description": "直腿抬高试验阳性，提示坐骨神经或神经根受到牵拉或压迫。"},
    {"name": "Sitting_Intolerance", "layer": "L5", "type": "symptom", "subtype": "None", "description": "无法耐受长时间坐姿，坐位会加剧疼痛，常见于椎间盘源性疼痛。"},
    {"name": "Avoid_Spine_Flexion", "layer": "L7", "type": "intervention", "subtype": "remove_cause", "description": "避免脊柱屈曲动作和姿势，以消除疼痛和损伤的诱因。"},
    {"name": "Core_Stabilization_Exercise", "layer": "L7", "type": "intervention", "subtype": "exercise_therapy", "description": "核心稳定训练，旨在增强躯干肌肉的耐力，以稳定脊柱，减少微动和疼痛。"},
    {"name": "Hip_Hinge_Lifting", "layer": "L0", "type": "action", "subtype": "None", "description": "髋部铰链式抬举，在抬举时保持腰椎中立位，通过髋关节屈曲来完成动作。"},
    {"name": "Cat_Camel_Exercise", "layer": "L7", "type": "intervention", "subtype": "exercise_therapy", "description": "猫驼式运动，在四点跪位下进行的脊柱屈伸活动，作为无负荷的脊柱活动度练习。"},
    {"name": "Pain_Relief", "layer": "L8", "type": "outcome", "subtype": "None", "description": "疼痛减轻，是康复治疗的主要目标之一。"},
    {"name": "Lumbar_Flexion", "layer": "L0", "type": "action", "subtype": "None", "description": "腰椎屈曲动作，特别是指脊柱的完全屈曲，是椎间盘损伤的主要机制。"},
    {"name": "Sustained_Posture", "layer": "L1", "type": "load", "subtype": "sustained_posture", "description": "长时间保持屈曲姿势，如坐姿，导致被动组织蠕变，降低其失效耐受力。"},
    {"name": "Spine_Compression", "layer": "L1", "type": "load", "subtype": "None", "description": "脊柱承受的轴向压缩力，在椎间盘屈曲时显著增加纤维环后部的应力。"},
    {"name": "Disc_Bulge", "layer": "L2", "type": "pathology", "subtype": "None", "description": "椎间盘纤维环向外膨出，但未完全破裂，是椎间盘突出的前期或较轻形式。"},
    {"name": "Inflammation", "layer": "L3", "type": "mechanism", "subtype": "None", "description": "髓核突破纤维环后，作为异物被免疫系统识别，引发局部炎症反应。"},
    {"name": "Central_Sensitization", "layer": "L3", "type": "mechanism", "subtype": "None", "description": "持续的疼痛信号导致中枢神经系统对痛觉信号放大和敏化。"},
    {"name": "Low_Back_Pain", "layer": "L4", "type": "symptom", "subtype": "None", "description": "局限于腰背部的疼痛，可能与椎间盘、关节突关节或肌肉韧带损伤有关。"},
    {"name": "Morning_Stiffness", "layer": "L4", "type": "symptom", "subtype": "None", "description": "晨起时疼痛和僵硬感加重，与夜间仰卧时椎间盘吸水膨胀有关。"},
    {"name": "Prone_Extension_Relief", "layer": "L5", "type": "test", "subtype": "None", "description": "俯卧位脊柱后伸时患者报告疼痛减轻，是椎间盘源性疼痛的强体征。"},
    {"name": "Neutral_Spine_Posture", "layer": "L7", "type": "intervention", "subtype": "remove_cause", "description": "教导患者在日常生活中保持腰椎中立位，通过屈髋代替屈腰。"},
    {"name": "Big_Three_Exercises", "layer": "L7", "type": "intervention", "subtype": "exercise_therapy", "description": "McGill推荐的三项核心训练：改良卷腹、侧桥和鸟狗式。"},
    {"name": "Prone_Extension_Exercise", "layer": "L7", "type": "intervention", "subtype": "exercise_therapy", "description": "俯卧位静力性伸展，用于减轻急性椎间盘后部突出的压力。"},
    {"name": "Functional_Recovery", "layer": "L8", "type": "outcome", "subtype": "None", "description": "恢复无痛的日常活动、工作和运动能力。"},
    {"name": "Abdominal_Bracing", "layer": "L7", "type": "intervention", "subtype": "exercise_therapy", "description": "腹部支撑，对称性地激活所有腹部肌层以形成核心刚度。"},
    {"name": "Abdominal_Hollowing", "layer": "L7", "type": "intervention", "subtype": "exercise_therapy", "description": "腹部内收动作，被McGill证明降低脊柱稳定性。"},
    {"name": "Spinal_Hinge", "layer": "L2", "type": "pathology", "subtype": "None", "description": "脊柱铰链现象，某一节段承担不成比例的大幅运动。"},
    {"name": "Quadratus_Lumborum", "layer": "L0", "type": "anatomy_variation", "subtype": "None", "description": "腰方肌，主要脊柱稳定肌。"},
    {"name": "Multifidus", "layer": "L0", "type": "anatomy_variation", "subtype": "None", "description": "多裂肌，脊柱后方稳定器。"},
    {"name": "Gluteal_Amnesia", "layer": "L3", "type": "mechanism", "subtype": "None", "description": "臀肌失忆症，髋伸展时臀肌无法被充分激活。"},
    {"name": "Flexion_Stretching", "layer": "L7", "type": "intervention", "subtype": "exercise_therapy", "description": "屈曲拉伸（如抱膝触胸），常被错误推荐但会加剧损伤。"},
    {"name": "Endurance_Training", "layer": "L7", "type": "intervention", "subtype": "exercise_therapy", "description": "耐力训练对减少未来背痛发作风险更具保护作用。"},
    {"name": "Golfers_Lift", "layer": "L7", "type": "intervention", "subtype": "remove_cause", "description": "高尔夫式提举法，安全拾取地面轻物。"},
    {"name": "Flexion_Relaxation_Phenomenon", "layer": "L5", "type": "test", "subtype": "None", "description": "完全屈曲时背部伸肌肌电活动突然静默。"},
    {"name": "Lumbopelvic_Rhythm", "layer": "L6", "type": "diagnosis", "subtype": "None", "description": "腰盆节律，McGill认为这是一个临床误区。"},
    {"name": "Avoid_Early_Morning_Flexion", "layer": "L7", "type": "intervention", "subtype": "remove_cause", "description": "避免晨起后立即进行脊柱屈曲，损伤风险最高。"},
    {"name": "Lumbar_Flexion_Mobility_Exercise", "layer": "L0", "type": "action", "subtype": "None", "description": "旨在增加腰椎屈曲活动度的练习。"},
    {"name": "Loaded_Spine_Motion", "layer": "L1", "type": "load", "subtype": "flexion_compression", "description": "在脊柱承受外部负荷时进行屈伸运动。"},
    {"name": "High_Spine_Power", "layer": "L1", "type": "load", "subtype": "repetitive_low_load", "description": "高速脊柱弯曲运动伴随肌肉力量会增加损伤风险。"},
    {"name": "Increased_IAP", "layer": "L1", "type": "load", "subtype": "None", "description": "腹内压增高，可增加躯干刚度。"},
    {"name": "Posterior_Disc_Herniation", "layer": "L2", "type": "pathology", "subtype": "None", "description": "髓核向后突破纤维环。"},
    {"name": "Facet_Joint_Arthritis", "layer": "L2", "type": "pathology", "subtype": "None", "description": "小关节关节炎。"},
    {"name": "Spinal_Stenosis", "layer": "L2", "type": "pathology", "subtype": "None", "description": "椎管狭窄。"},
    {"name": "Segmental_Instability", "layer": "L3", "type": "mechanism", "subtype": "None", "description": "节段性稳定性丧失。"},
    {"name": "Radicular_Pain_Sciatica", "layer": "L4", "type": "symptom", "subtype": "None", "description": "神经根受压引起的放射性腿部疼痛。"},
    {"name": "Mechanical_Back_Pain", "layer": "L4", "type": "symptom", "subtype": "None", "description": "与活动相关的背部疼痛。"},
    {"name": "Aberrant_Motion_Catch", "layer": "L5", "type": "sign", "subtype": "None", "description": "脊柱出现异常顿挫运动，提示节段不稳定。"},
    {"name": "Discogenic_Disorder_Diagnosis", "layer": "L6", "type": "diagnosis", "subtype": "None", "description": "椎间盘源性疼痛诊断。"},
    {"name": "Spine_Mobilizing_Exercises", "layer": "L7", "type": "intervention", "subtype": "exercise_therapy", "description": "如猫驼式，无压缩负荷下的活动度训练。"},
    {"name": "Directed_Stretching_Exercises", "layer": "L7", "type": "intervention", "subtype": "exercise_therapy", "description": "特定方向牵伸。"},
    {"name": "Nerve_Flossing", "layer": "L7", "type": "intervention", "subtype": "exercise_therapy", "description": "神经滑动练习。"},
    {"name": "Surgery", "layer": "L7", "type": "intervention", "subtype": "surgery", "description": "手术治疗。"},
    {"name": "Sustained_Posture_Load", "layer": "L1", "type": "load", "subtype": "sustained_posture", "description": "持续姿势导致营养交换受限与组织退变"},
    {"name": "Annulus_Tear", "layer": "L2", "type": "pathology", "subtype": "None", "description": "纤维环撕裂，常由反复屈曲压缩引起"},
    {"name": "Disc_Degeneration", "layer": "L2", "type": "pathology", "subtype": "None", "description": "椎间盘退变，与长期低负荷重复应力相关"},
    {"name": "MRI_Disc_Bulge", "layer": "L5", "type": "test", "subtype": "None", "description": "MRI显示椎间盘膨出，但与症状相关性弱"},
    {"name": "Avoid_Flexion", "layer": "L7", "type": "intervention", "subtype": "remove_cause", "description": "避免腰椎屈曲动作"},
    {"name": "Backward_Bending", "layer": "L0", "type": "action", "subtype": "None", "description": "脊柱后伸/后弯动作"},
    {"name": "Walking_Extension", "layer": "L0", "type": "exposure", "subtype": "None", "description": "行走时腰椎进入后伸位"},
    {"name": "Standing_Extended", "layer": "L0", "type": "exposure", "subtype": "None", "description": "长时间站立后伸姿势"},
    {"name": "Extension_Compression", "layer": "L1", "type": "load", "subtype": "extension_compression", "description": "后伸+压缩负荷，集中于小关节"},
    {"name": "Facet_Impingement", "layer": "L2", "type": "pathology", "subtype": "None", "description": "小关节撞击/卡压"},
    {"name": "Facet_Irritation", "layer": "L2", "type": "pathology", "subtype": "None", "description": "小关节激惹/炎症"},
    {"name": "Facet_Joint_Syndrome", "layer": "L6", "type": "diagnosis", "subtype": "None", "description": "小关节综合征诊断"},
    {"name": "Extension_Pain", "layer": "L5", "type": "sign", "subtype": "None", "description": "后伸时诱发疼痛"},
    {"name": "Facet_Tenderness", "layer": "L5", "type": "sign", "subtype": "None", "description": "小关节区域压痛"},
    {"name": "Walking_Intolerance", "layer": "L4", "type": "symptom", "subtype": "None", "description": "行走不能耐受，后伸加重"},
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
]

ALIASES = [
    {"node_name": "Repeated_Lumbar_Flexion", "language": "zh", "display_name": "反复腰椎屈曲"},
    {"node_name": "Prolonged_Sitting", "language": "zh", "display_name": "久坐"},
    {"node_name": "Sit_Up", "language": "zh", "display_name": "仰卧起坐"},
    {"node_name": "Stoop_Lifting", "language": "zh", "display_name": "弯腰抬举"},
    {"node_name": "Morning_Flexion", "language": "zh", "display_name": "早晨屈曲"},
    {"node_name": "Flexion_Compression", "language": "zh", "display_name": "屈曲压缩负荷"},
    {"node_name": "Disc_Shear", "language": "zh", "display_name": "椎间盘剪切力"},
    {"node_name": "Repetitive_Low_Load", "language": "zh", "display_name": "重复低负荷"},
    {"node_name": "Disc_Herniation", "language": "zh", "display_name": "椎间盘突出"},
    {"node_name": "Endplate_Fracture", "language": "zh", "display_name": "终板骨折"},
    {"node_name": "Annulus_Delamination", "language": "zh", "display_name": "纤维环分层"},
    {"node_name": "Spondylolisthesis", "language": "zh", "display_name": "脊椎滑脱"},
    {"node_name": "Nerve_Root_Compression", "language": "zh", "display_name": "神经根压迫"},
    {"node_name": "Instability", "language": "zh", "display_name": "节段性不稳定"},
    {"node_name": "Discogenic_Pain", "language": "zh", "display_name": "椎间盘源性疼痛"},
    {"node_name": "Radicular_Pain", "language": "zh", "display_name": "放射性腿痛"},
    {"node_name": "Flexion_Intolerance", "language": "zh", "display_name": "屈曲不耐受"},
    {"node_name": "SLR_Positive", "language": "zh", "display_name": "直腿抬高试验阳性"},
    {"node_name": "Sitting_Intolerance", "language": "zh", "display_name": "久坐不耐受"},
    {"node_name": "Avoid_Spine_Flexion", "language": "zh", "display_name": "避免脊柱屈曲"},
    {"node_name": "Core_Stabilization_Exercise", "language": "zh", "display_name": "核心稳定训练"},
    {"node_name": "Hip_Hinge_Lifting", "language": "zh", "display_name": "髋铰链抬举"},
    {"node_name": "Cat_Camel_Exercise", "language": "zh", "display_name": "猫驼式运动"},
    {"node_name": "Pain_Relief", "language": "zh", "display_name": "疼痛缓解"},
    {"node_name": "Lumbar_Flexion", "language": "zh", "display_name": "腰椎屈曲"},
    {"node_name": "Sustained_Posture", "language": "zh", "display_name": "持续姿势负荷"},
    {"node_name": "Spine_Compression", "language": "zh", "display_name": "脊柱压缩"},
    {"node_name": "Disc_Bulge", "language": "zh", "display_name": "椎间盘膨出"},
    {"node_name": "Inflammation", "language": "zh", "display_name": "炎症"},
    {"node_name": "Central_Sensitization", "language": "zh", "display_name": "中枢致敏"},
    {"node_name": "Low_Back_Pain", "language": "zh", "display_name": "腰痛"},
    {"node_name": "Morning_Stiffness", "language": "zh", "display_name": "晨僵"},
    {"node_name": "Prone_Extension_Relief", "language": "zh", "display_name": "俯卧后伸缓解"},
    {"node_name": "Neutral_Spine_Posture", "language": "zh", "display_name": "中立位姿势"},
    {"node_name": "Big_Three_Exercises", "language": "zh", "display_name": "McGill三大训练"},
    {"node_name": "Prone_Extension_Exercise", "language": "zh", "display_name": "俯卧后伸练习"},
    {"node_name": "Functional_Recovery", "language": "zh", "display_name": "功能恢复"},
    {"node_name": "Abdominal_Bracing", "language": "zh", "display_name": "腹部支撑"},
    {"node_name": "Abdominal_Hollowing", "language": "zh", "display_name": "腹部内收"},
    {"node_name": "Spinal_Hinge", "language": "zh", "display_name": "脊柱铰链"},
    {"node_name": "Quadratus_Lumborum", "language": "zh", "display_name": "腰方肌"},
    {"node_name": "Multifidus", "language": "zh", "display_name": "多裂肌"},
    {"node_name": "Gluteal_Amnesia", "language": "zh", "display_name": "臀肌失忆"},
    {"node_name": "Flexion_Stretching", "language": "zh", "display_name": "屈曲拉伸"},
    {"node_name": "Endurance_Training", "language": "zh", "display_name": "耐力训练"},
    {"node_name": "Golfers_Lift", "language": "zh", "display_name": "高尔夫拾物法"},
    {"node_name": "Flexion_Relaxation_Phenomenon", "language": "zh", "display_name": "屈曲放松现象"},
    {"node_name": "Lumbopelvic_Rhythm", "language": "zh", "display_name": "腰盆节律"},
    {"node_name": "Spinal_Stenosis", "language": "zh", "display_name": "椎管狭窄"},
    {"node_name": "Aberrant_Motion_Catch", "language": "zh", "display_name": "异常顿挫运动"},
    {"node_name": "Spine_Mobilizing_Exercises", "language": "zh", "display_name": "脊柱活动度训练"},
    {"node_name": "Directed_Stretching_Exercises", "language": "zh", "display_name": "定向牵伸"},
    {"node_name": "Nerve_Flossing", "language": "zh", "display_name": "神经滑动练习"},
    {"node_name": "Surgery", "language": "zh", "display_name": "手术"},
    {"node_name": "Annulus_Tear", "language": "zh", "display_name": "纤维环撕裂"},
    {"node_name": "Disc_Degeneration", "language": "zh", "display_name": "椎间盘退变"},
    {"node_name": "MRI_Disc_Bulge", "language": "zh", "display_name": "MRI椎间盘膨出"},
    {"node_name": "Backward_Bending", "language": "zh", "display_name": "后伸动作"},
    {"node_name": "Walking_Extension", "language": "zh", "display_name": "行走后伸"},
    {"node_name": "Standing_Extended", "language": "zh", "display_name": "站立后伸"},
    {"node_name": "Extension_Compression", "language": "zh", "display_name": "后伸压缩负荷"},
    {"node_name": "Facet_Impingement", "language": "zh", "display_name": "小关节撞击"},
    {"node_name": "Facet_Irritation", "language": "zh", "display_name": "小关节激惹"},
    {"node_name": "Facet_Joint_Syndrome", "language": "zh", "display_name": "小关节综合征"},
    {"node_name": "Extension_Pain", "language": "zh", "display_name": "后伸痛"},
    {"node_name": "Facet_Tenderness", "language": "zh", "display_name": "小关节压痛"},
    {"node_name": "Walking_Intolerance", "language": "zh", "display_name": "行走不耐受"},
    {"node_name": "Extension_Mobility_Exercise", "language": "zh", "display_name": "后伸活动度训练"},
    {"node_name": "Avoid_Extension", "language": "zh", "display_name": "避免后伸"},
    {"node_name": "NSAIDs", "language": "zh", "display_name": "非甾体抗炎药"},
    {"node_name": "Muscle_Relaxants", "language": "zh", "display_name": "肌肉松弛剂"},
    {"node_name": "Acetaminophen", "language": "zh", "display_name": "对乙酰氨基酚"},
    {"node_name": "Gabapentinoid", "language": "zh", "display_name": "加巴喷丁类药物"},
    {"node_name": "Epidural_Steroid_Injection", "language": "zh", "display_name": "硬膜外类固醇注射"},
    {"node_name": "Manual_Therapy", "language": "zh", "display_name": "手法治疗"},
    {"node_name": "Traction", "language": "zh", "display_name": "腰椎牵引"},
    {"node_name": "Heat_Therapy", "language": "zh", "display_name": "热敷"},
    {"node_name": "Ice_Therapy", "language": "zh", "display_name": "冷敷"},
    {"node_name": "TENS", "language": "zh", "display_name": "经皮神经电刺激"},
    {"node_name": "Acupuncture", "language": "zh", "display_name": "针灸"},
    {"node_name": "Microdiscectomy", "language": "zh", "display_name": "显微椎间盘切除术"},
    {"node_name": "Spinal_Fusion", "language": "zh", "display_name": "脊柱融合术"},
    {"node_name": "Laminectomy", "language": "zh", "display_name": "椎板切除术"},
]


def main():
    # 建立 node_name → 中文名的映射（优先用 zh 别名，其次 description 首句）
    name_to_zh = {}
    for a in ALIASES:
        if a["language"] == "zh":
            name_to_zh[a["node_name"]] = a["display_name"]

    # 对没有中文别名的节点，用 description 的简短版
    for n in NODES:
        if n["name"] not in name_to_zh:
            desc = n["description"]
            # 取第一句（句号前）
            first_sentence = desc.split("。")[0].split(",")[0] if desc else n["name"]
            name_to_zh[n["name"]] = first_sentence

    term_map = {}
    for n in NODES:
        term_map[n["name"]] = {
            "zh": name_to_zh.get(n["name"], n["name"]),
            "layer": n["layer"],
            "type": n["type"],
            "subtype": n.get("subtype", ""),
            "description": n["description"],
        }

    output_dir = os.path.join(os.path.dirname(__file__), "..", "data", "ontology")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "term_map.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(term_map, f, ensure_ascii=False, indent=2)

    print(f"✅ term_map.json 已生成: {output_path}")
    print(f"   共 {len(term_map)} 个术语")


if __name__ == "__main__":
    main()