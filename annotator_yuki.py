# annotator_A1.py
# ============================================================
# 编码员：A1
# 负责样本范围：0 - 499（共500条）
# 使用方式：streamlit run annotator_A1.py
# ============================================================

import streamlit as st
import json
import os

# ============================================================
# ⚙️ 编码员配置（每个文件唯一不同的部分）
# ============================================================
ANNOTATOR_NAME = "Yuki"
SAMPLE_START = 500
SAMPLE_END = 999

# ============================================================
# 📁 路径配置（将 .py 和 .jsonl 放在同一文件夹即可）
# ============================================================
#此处将参考编码文档中的【第三步】调整，保证.py和.jsonl文件都在该文件夹即可。
# 路徑配置（相對路徑，保證不出錯）
SOURCE_DATA_PATH = "260510_resultsV5_final.jsonl"
RESULT_DATA_PATH = "results_yuki.jsonl"
 #和Source_data_path在同一个文件夹下，之后你需要将该文件发送给我

# ============================================================
# 常量
# ============================================================
STATUS_OPTIONS = ["未标注", "标注中", "已完成"]
STATUS_COLORS = {"未标注": "🔴", "标注中": "🟡", "已完成": "🟢"}

SCORE_KEYS = [
    "score_assured", "score_dominant", "score_assertive",
    "score_in_control", "score_upper_status", "score_seeking_closeness",
    "score_expressing_emotions", "score_emotionally_involved", "score_affectionate"
]

HIDDEN_FIELDS = SCORE_KEYS + [
    "annotation_status", "annotator", "remark", "full_dialog"
]

st.set_page_config(page_title=f"编码工作台 — {ANNOTATOR_NAME}", layout="wide")

# ============================================================
# 核心函数
# ============================================================
@st.cache_data
def load_source_data(path, start, end):
    if not os.path.exists(path):
        return []
    all_data = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                all_data.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return all_data[start:end + 1]

@st.cache_data
def load_result_data(path):
    if not os.path.exists(path):
        return {}
    results = {}
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                item = json.loads(line)
                results[item["image_number"]] = item
            except json.JSONDecodeError:
                continue
    return results

def save_result(path, image_number, record, all_source_data, existing_results):
    existing_results[image_number] = record
    ordered_keys = [d["image_number"] for d in all_source_data]
    with open(path, 'w', encoding='utf-8') as f:
        for key in ordered_keys:
            if key in existing_results:
                f.write(json.dumps(existing_results[key], ensure_ascii=False) + '\n')
    load_result_data.clear()
    st.success(f"💾 已保存！结果文件：{path}")

# ============================================================
# 初始化 session_state
# ============================================================
if 'source_data' not in st.session_state:
    st.session_state.source_data = load_source_data(SOURCE_DATA_PATH, SAMPLE_START, SAMPLE_END)
if 'existing_results' not in st.session_state:
    st.session_state.existing_results = load_result_data(RESULT_DATA_PATH)
if 'current_idx' not in st.session_state:
    st.session_state.current_idx = 0
if 'visible_pos' not in st.session_state:
    st.session_state.visible_pos = 0
if 'auto_next' not in st.session_state:
    st.session_state.auto_next = False

source_data = st.session_state.source_data
existing_results = st.session_state.existing_results

if not source_data:
    st.error("数据加载失败，请检查 SOURCE_DATA_PATH 是否正确，并确认文件与本脚本在同一文件夹。")
    st.stop()

# ============================================================
# 侧边栏
# ============================================================
st.sidebar.header(f"👤 编码员：{ANNOTATOR_NAME}")
st.sidebar.caption(f"负责样本：第 {SAMPLE_START + 1} — {SAMPLE_END + 1} 条")

total = len(source_data)
done = sum(1 for d in source_data
           if existing_results.get(d["image_number"], {}).get("coder_annotation_status") == "已完成")
in_progress = sum(1 for d in source_data
                  if existing_results.get(d["image_number"], {}).get("coder_annotation_status") == "标注中")
unlabeled = total - done - in_progress

st.sidebar.markdown("### 📊 标注进度")
st.sidebar.progress(done / total if total > 0 else 0)
st.sidebar.markdown(
    f"✅ 已完成: **{done}** &nbsp;|&nbsp; "
    f"🔄 标注中: **{in_progress}** &nbsp;|&nbsp; "
    f"⬜ 未标注: **{unlabeled}**"
)
st.sidebar.divider()

# 过滤器
st.sidebar.markdown("### 🔍 筛选")
filter_status = st.sidebar.selectbox("按标注状态筛选", ["全部"] + STATUS_OPTIONS)

visible_indices = []
for i, d in enumerate(source_data):
    status = existing_results.get(d["image_number"], {}).get("coder_annotation_status", "未标注")
    if filter_status == "全部" or status == filter_status:
        visible_indices.append(i)

if not visible_indices:
    st.sidebar.warning("没有符合条件的样本")
    st.stop()

st.sidebar.markdown(f"筛选结果: **{len(visible_indices)}** 条")
st.sidebar.divider()

# 导航
st.session_state.visible_pos = min(st.session_state.visible_pos, len(visible_indices) - 1)

def go_next():
    if st.session_state.visible_pos < len(visible_indices) - 1:
        st.session_state.visible_pos += 1
        st.session_state.current_idx = visible_indices[st.session_state.visible_pos]

def go_prev():
    if st.session_state.visible_pos > 0:
        st.session_state.visible_pos -= 1
        st.session_state.current_idx = visible_indices[st.session_state.visible_pos]

def go_next_unlabeled():
    for pos in range(st.session_state.visible_pos + 1, len(visible_indices)):
        i = visible_indices[pos]
        status = existing_results.get(source_data[i]["image_number"], {}).get("coder_annotation_status", "未标注")
        if status == "未标注":
            st.session_state.visible_pos = pos
            st.session_state.current_idx = i
            return
    st.toast("🎉 后面没有未标注的样本了！")

st.sidebar.markdown("### 🚀 导航与跳转")
nav_col1, nav_col2 = st.sidebar.columns(2)
nav_col1.button("⬅️ 上一张", on_click=go_prev, use_container_width=True)
nav_col2.button("下一张 ➡️", on_click=go_next, use_container_width=True)
st.sidebar.button("⏭️ 跳到下一个未标注", on_click=go_next_unlabeled, use_container_width=True)

id_options = [f"{i}: ID {source_data[i].get('image_number')}" for i in visible_indices]
safe_pos = min(st.session_state.visible_pos, len(id_options) - 1)
selected_option = st.sidebar.selectbox("跳转到指定样本", options=id_options, index=safe_pos)
if selected_option is not None:
    st.session_state.visible_pos = id_options.index(selected_option)
    st.session_state.current_idx = visible_indices[st.session_state.visible_pos]

# ============================================================
# 主界面
# ============================================================
idx = st.session_state.current_idx
current_source = source_data[idx]
image_number = current_source["image_number"]
saved = existing_results.get(image_number, {})

st.title(f"🛠️ 编码工作台 — {ANNOTATOR_NAME}")

stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
stat_col1.info(f"📍 当前位置: {idx + 1} / {total}")
stat_col2.success(f"🖼️ image_number: {image_number}")
stat_col3.warning(f"📊 负责样本量: {total}")

current_status = saved.get("coder_annotation_status", "未标注")
if current_status == "已完成":
    stat_col4.success(f"🏷️ {current_status}")
elif current_status == "标注中":
    stat_col4.warning(f"🏷️ {current_status}")
else:
    stat_col4.error(f"🏷️ {current_status}")

col_left, col_right = st.columns([1, 1])

# --- 左侧：图片与分值 ---
with col_left:
    if current_source.get('finalurls'):
        st.image(current_source.get('finalurls'), use_container_width=True)

    st.markdown("### 🔢 维度分数（请独立填写）")
    updated_scores = {}
    s_col1, s_col2 = st.columns(2)
    for i, key in enumerate(SCORE_KEYS):
        target_col = s_col1 if i % 2 == 0 else s_col2
        default_val = float(saved.get(f"coder_{key}", 0.0))
        updated_scores[key] = target_col.number_input(
            f"{key}",
            value=default_val,
            step=0.1,
            min_value=0.0,
            max_value=10.0,
            key=f"input_score_{key}_{idx}"
        )

# --- 右侧：角色名称、对话、标注信息 ---
with col_right:
    st.markdown("### 👤 角色识别与对话")

    name_col1, name_col2 = st.columns(2)
    new_ai_name = name_col1.text_input(
        "🤖 AI 角色名",
        value=saved.get("coder_AI_name", current_source.get("AI_name", "")),
        key=f"ai_name_{idx}"
    )
    new_user_name = name_col2.text_input(
        "👤 用户名 (User)",
        value=saved.get("coder_user_name", current_source.get("user_name", "")),
        key=f"user_name_{idx}"
    )

    st.write("---")

    original_ai_text = current_source.get("AI_text", "")
    original_user_text = current_source.get("User_text", "")

    edited_ai_text = st.text_area(
        "💬 AI 对话文本",
        value=saved.get("coder_AI_text", original_ai_text),
        height=150,
        key=f"edit_ai_{idx}"
    )
    edited_user_text = st.text_area(
        "💬 User 对话文本",
        value=saved.get("coder_User_text", original_user_text),
        height=150,
        key=f"edit_user_{idx}"
    )

    ai_text_edited = edited_ai_text != original_ai_text
    user_text_edited = edited_user_text != original_user_text
    dialog_edited = ai_text_edited or user_text_edited
    if dialog_edited:
        st.warning("⚠️ 对话文本已被修改，保存时将自动标记。")

    st.divider()
    st.markdown("### 🏷️ 标注管理")

    status_key = f"selected_status_{idx}"
    if status_key not in st.session_state:
        st.session_state[status_key] = saved.get("coder_annotation_status", "未标注")

    st.caption("标注状态")
    status_cols = st.columns(len(STATUS_OPTIONS))
    for i, status in enumerate(STATUS_OPTIONS):
        is_selected = st.session_state[status_key] == status
        label = f"{STATUS_COLORS[status]} {status}" + (" ✓" if is_selected else "")
        if status_cols[i].button(
            label,
            key=f"btn_status_{status}_{idx}",
            use_container_width=True,
            type="primary" if is_selected else "secondary"
        ):
            st.session_state[status_key] = status
            st.rerun()

    st.write("")

    new_remark = st.text_area(
        "📝 备注",
        value=saved.get("coder_remark", ""),
        height=80,
        placeholder="记录特殊情况、存疑内容等...",
        key=f"remark_{idx}"
    )

    st.divider()

    auto_next = st.checkbox(
        "💨 保存后自动跳下一张",
        value=st.session_state.auto_next,
        key="auto_next_checkbox"
    )
    st.session_state.auto_next = auto_next

    if st.button("💾 保存编码结果", type="primary", use_container_width=True):
        # 完整原始数据 + 编码员字段（coder_ 前缀）
        record = dict(current_source)

        for k, v in updated_scores.items():
            record[f"coder_{k}"] = v

        record["coder_AI_name"] = new_ai_name
        record["coder_user_name"] = new_user_name
        record["coder_AI_text"] = edited_ai_text
        record["coder_User_text"] = edited_user_text
        record["coder_dialog_edited"] = dialog_edited
        record["coder_ai_text_edited"] = ai_text_edited
        record["coder_user_text_edited"] = user_text_edited
        record["coder_annotation_status"] = st.session_state[status_key]
        record["coder_remark"] = new_remark
        record["coder_name"] = ANNOTATOR_NAME

        save_result(RESULT_DATA_PATH, image_number, record,
                    source_data, st.session_state.existing_results)

        if st.session_state.auto_next:
            if st.session_state.visible_pos < len(visible_indices) - 1:
                st.session_state.visible_pos += 1
                st.session_state.current_idx = visible_indices[st.session_state.visible_pos]
            else:
                st.toast("🎉 已经是最后一条了！")
        st.rerun()

with st.expander("🔍 查看原始样本结构（不含 AI 编码分数）"):
    display = {k: v for k, v in current_source.items() if k not in HIDDEN_FIELDS}
    st.write(display)