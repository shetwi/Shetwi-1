from __future__ import annotations

import html
from typing import Any

import streamlit as st

from engine import generate_response
from game_logic import (
    SHOP,
    add_log,
    apply_relationship_delta,
    attempt_awakening,
    become_rogue,
    buy_item,
    end_awakening,
    finish_quest,
    load_state,
    meditate,
    new_game,
    resolve_action,
    rest,
    save_state,
    use_item,
)
from styles import APP_CSS, render_kawarimi_slots, render_meter


st.set_page_config(
    page_title="ظلّ الشينوبي | RPG",
    page_icon="忍",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(APP_CSS, unsafe_allow_html=True)


def current_state():
    return st.session_state.game_state


def persist() -> None:
    try:
        save_state(current_state())
    except OSError as exc:
        st.warning(f"تعذّر حفظ اللعبة محليًا: {exc}")


def push_chat(role: str, content: str) -> None:
    st.session_state.chat_history.append({"role": role, "content": content})


def narrate(player_text: str, display_text: str | None = None) -> None:
    state = current_state()
    push_chat("user", display_text or player_text)
    response = generate_response(state, player_text)
    push_chat("assistant", response.narration)
    if response.npc_name and response.npc_name in state.relationships:
        apply_relationship_delta(
            state, response.npc_name, response.relationship_delta
        )
    add_log(state, f"المشهد: {response.atmosphere}")
    persist()


if "game_state" not in st.session_state:
    st.session_state.game_state = load_state() or new_game()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if not st.session_state.chat_history:
    st.session_state.chat_history.append(
        {
            "role": "assistant",
            "content": (
                "ليلٌ ثقيل يهبط على حدود أرض النار. آثار أقدام حديثة تقطع الوحل "
                "نحو غابة لا تُسمع فيها الطيور. أمامك مهمة، وخلفك قرية لا تنسى "
                "من يعود إليها خالي الوفاض."
            ),
        }
    )

state = current_state()

with st.sidebar:
    st.title("忍 ظلّ الشينوبي")
    st.caption("حملة سردية — قراراتك تُخلّف آثارًا.")
    st.markdown(
        render_meter("الصحة", state.hp, state.max_hp, "hp-fill"),
        unsafe_allow_html=True,
    )
    st.markdown(
        render_meter("التشاكرا", state.chakra, state.max_chakra, "chakra-fill"),
        unsafe_allow_html=True,
    )
    st.markdown(
        render_meter("مقياس العاصفة", state.storm_gauge, 100, "storm-fill"),
        unsafe_allow_html=True,
    )
    st.markdown(
        render_kawarimi_slots(state.kawarimi, state.max_kawarimi),
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<span class="badge gold">المستوى {state.level}</span>'
        f'<span class="badge">الخبرة {state.exp}</span>'
        f'<span class="badge">ريو {state.ryo}</span>',
        unsafe_allow_html=True,
    )
    if state.player.alignment == "نينجا مارق":
        st.markdown(
            f'<span class="badge red">مطلوب: {state.bounty} ريو</span>'
            f'<span class="badge red">حرارة الأنبو: {state.anbu_heat}%</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<span class="badge blue">{html.escape(state.player.alignment)}</span>',
            unsafe_allow_html=True,
        )
    st.divider()

    with st.expander("الملف الشخصي", expanded=False):
        st.write(f"**الاسم:** {state.player.name}")
        st.write(f"**القرية:** {state.player.village}")
        st.write(f"**النيندو:** {state.player.nindo}")
        st.write(
            f"**الإحصاءات:** نينجوتسو {state.stats.ninjutsu}، "
            f"تايجتسو {state.stats.taijutsu}، "
            f"جينجتسو {state.stats.genjutsu}، "
            f"دفاع {state.stats.defense}، سرعة {state.stats.speed}"
        )
        if state.awakening:
            st.warning(f"الحالة النشطة: {state.awakening}")

    with st.expander("العلاقات", expanded=False):
        for relationship in state.relationships.values():
            st.write(
                f"**{relationship.name}:** {relationship.sentiment:+d}/100"
            )
            if relationship.note:
                st.caption(relationship.note)

    with st.expander("الحقيبة", expanded=False):
        if not state.inventory:
            st.caption("الحقيبة فارغة.")
        for item in state.inventory:
            left, right = st.columns([3, 1])
            left.write(f"{item.name} ×{item.quantity}")
            if item.name in {"حبوب التشاكرا", "مرهم طبي"} and right.button(
                "استخدم", key=f"use_{item.name}"
            ):
                ok, message = use_item(state, item.name)
                st.toast(message, icon="✅" if ok else "⚠️")
                persist()
                st.rerun()

    st.subheader("إجراءات")
    if st.button("راحة قصيرة", use_container_width=True):
        st.toast(rest(state))
        persist()
        st.rerun()
    if st.button("تأمل", use_container_width=True):
        st.toast(meditate(state))
        persist()
        st.rerun()
    if state.awakening:
        if st.button("إنهاء الاستيقاظ", use_container_width=True):
            end_awakening(state)
            persist()
            st.rerun()
    else:
        awakening_choice = st.selectbox(
            "حالة استيقاظ", ["نمط الناسك", "علامة اللعنة", "طور التشاكرا", "سوسانو"]
        )
        if st.button("تفعيل الحالة", use_container_width=True):
            ok, message = attempt_awakening(state, awakening_choice)
            st.toast(message, icon="⚡" if ok else "⚠️")
            persist()
            st.rerun()

    if state.player.alignment != "نينجا مارق":
        if st.button("اهجر القرية", use_container_width=True):
            st.toast(become_rogue(state), icon="⚠️")
            narrate(
                "أعلن اللاعب انشقاقه عن القرية. لا يطلب المغفرة.",
                "أهجر القرية وأتحمل العواقب.",
            )
            st.rerun()

    if st.button("حفظ الآن", use_container_width=True):
        persist()
        st.toast("حُفظ التقدم.", icon="💾")

st.title("سجلّ المهمة")
st.markdown(
    f'<div class="panel"><span class="badge gold">{html.escape(state.player.name)}</span>'
    f'<span class="badge">{html.escape(state.player.village)}</span>'
    f'<span class="badge">{html.escape(state.player.nindo)}</span>'
    f'<p class="small-muted">الخبرة التالية: {max(0, 100 + (state.level - 1) * 50 - state.exp)}</p>'
    f'</div>',
    unsafe_allow_html=True,
)

main_col, side_col = st.columns([2.2, 1], gap="large")

with side_col:
    st.subheader("المهمة")
    active_quests = [quest for quest in state.quests if quest.status == "نشطة"]
    if active_quests:
        quest = active_quests[0]
        st.markdown(
            f'<div class="panel"><strong>{html.escape(quest.title)}</strong>'
            f'<p>{html.escape(quest.description)}</p>'
            f'<span class="badge gold">المكافأة: {quest.reward_ryo} ريو</span></div>',
            unsafe_allow_html=True,
        )
        if st.button("إكمال المهمة", use_container_width=True):
            ok, message = finish_quest(state)
            st.toast(message, icon="✅" if ok else "⚠️")
            if ok:
                push_chat("assistant", message)
            persist()
            st.rerun()
    else:
        st.info("لا توجد مهام نشطة.")

    st.subheader("المتجر")
    for item_name, details in SHOP.items():
        st.write(f"**{item_name}** — {details['price']} ريو")
        st.caption(details["description"])
        if st.button(f"شراء {item_name}", key=f"buy_{item_name}", use_container_width=True):
            ok, message = buy_item(state, item_name)
            st.toast(message, icon="🪙" if ok else "⚠️")
            persist()
            st.rerun()

    st.subheader("سجل الأحداث")
    for entry in reversed(state.log[-8:]):
        st.caption(f"• {entry}")

with main_col:
    st.subheader("المشهد")
    for message in st.session_state.chat_history[-24:]:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    st.markdown("**لوحة القتال**")
    combat_cols = st.columns(4)
    actions = [
        ("taijutsu", "تايجتسو"),
        ("ninjutsu", "نينجوتسو"),
        ("ougi", "أوغي"),
        ("kawarimi", "كاواريمي"),
    ]
    for column, (action, label) in zip(combat_cols, actions):
        disabled = state.defeated
        if action == "ougi":
            disabled = disabled or state.storm_gauge < 50
        if action == "kawarimi":
            disabled = disabled or state.kawarimi < 1
        if column.button(label, disabled=disabled, use_container_width=True):
            result = resolve_action(state, action)
            push_chat("assistant", result)
            narrate(
                f"نتيجة الحركة الميكانيكية: {result}. تابع المشهد دون تغيير هذه النتيجة.",
                f"نفذت حركة {label}.",
            )
            st.rerun()

    user_input = st.chat_input(
        "اكتب حوارًا أو قرارًا للشخصية...",
        disabled=state.defeated,
    )
    if user_input:
        narrate(user_input)
        st.rerun()

with st.expander("بدء شخصية جديدة أو تحميل الحفظ"):
    st.caption("بدء شخصية جديدة يمحو الحفظ المحلي الحالي عند تأكيده.")
    with st.form("new_character_form"):
        new_name = st.text_input("اسم الشخصية", max_chars=40, value="نينجا مجهول")
        new_village = st.selectbox(
            "القرية", ["كونوها", "سونا", "كيري", "إيوا", "كومو", "أخرى"]
        )
        new_nindo = st.text_input("النيندو", max_chars=120, value="حماية الرفاق")
        submitted = st.form_submit_button("إنشاء شخصية جديدة")
    if submitted:
        fresh_state = new_game(new_name, new_village)
        fresh_state.player.nindo = new_nindo.strip() or "حماية الرفاق"
        st.session_state.game_state = fresh_state
        st.session_state.chat_history = [
            {
                "role": "assistant",
                "content": (
                    "تبدأ رحلتك عند حدود قرية الشينوبي. الريح تحمل رائحة المطر "
                    "والحديد؛ لا أحد هنا يعرف بعد ما الذي ستصبح عليه."
                ),
            }
        ]
        persist()
        st.rerun()

    if st.button("تحميل آخر حفظ"):
        loaded = load_state()
        if loaded:
            st.session_state.game_state = loaded
            st.toast("تم تحميل الحفظ.", icon="💾")
            st.rerun()
        st.warning("لم يُعثر على حفظ صالح.")
