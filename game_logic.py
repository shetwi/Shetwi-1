from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Optional

from schemas import GameState, InventoryItem, Quest, Relationship

SAVE_PATH = Path("naruto_rpg_save.json")

SHOP = {
    "حبوب التشاكرا": {"price": 120, "description": "تعيد 35 نقطة تشاكرا."},
    "مرهم طبي": {"price": 100, "description": "يعيد 35 نقطة صحة."},
    "كوناي مسموم": {"price": 180, "description": "سلاح خطر؛ يزيد ضرر هجومك التالي."},
    "كوناي": {"price": 45, "description": "سلاح نينجا أساسي."},
}

INITIAL_RELATIONSHIPS = ("كاكاشي", "تسونادي", "إيتاتشي", "باين")


def new_game(name: str = "نينجا مجهول", village: str = "كونوها") -> GameState:
    state = GameState()
    state.player.name = name.strip()[:40] or "نينجا مجهول"
    state.player.village = village.strip()[:40] or "كونوها"
    state.inventory = [
        InventoryItem(name="كوناي", quantity=3, description=SHOP["كوناي"]["description"]),
        InventoryItem(name="حبوب التشاكرا", quantity=1, description=SHOP["حبوب التشاكرا"]["description"]),
    ]
    state.quests = [
        Quest(
            title="آثار على طريق الحدود",
            description="تحرّ عن آثار حركة مشبوهة قرب حدود أرض النار.",
            reward_ryo=150,
        )
    ]
    state.relationships = {
        name: Relationship(name=name, sentiment=0, note="لم يتحدد موقفه منك بعد.")
        for name in INITIAL_RELATIONSHIPS
    }
    add_log(state, f"بدأ {state.player.name} رحلته من قرية {state.player.village}.")
    return state


def add_log(state: GameState, message: str) -> None:
    state.log.append(message[:300])
    state.log = state.log[-100:]


def save_state(state: GameState, path: Path = SAVE_PATH) -> None:
    path.write_text(
        json.dumps(state.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_state(path: Path = SAVE_PATH) -> Optional[GameState]:
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return GameState.model_validate(raw)
    except (OSError, json.JSONDecodeError, ValueError):
        return None


def exp_to_next_level(level: int) -> int:
    return 100 + max(0, level - 1) * 50


def award_exp(state: GameState, amount: int) -> list[str]:
    messages = []
    state.exp += max(0, amount)
    while state.exp >= exp_to_next_level(state.level):
        state.exp -= exp_to_next_level(state.level)
        state.level += 1
        state.max_hp += 12
        state.max_chakra += 10
        state.hp = state.max_hp
        state.chakra = state.max_chakra
        messages.append(f"ارتقيت إلى المستوى {state.level}؛ زادت صحتك وتشاكراك.")
    return messages


def distribute_stat(state: GameState, stat: str, points: int = 1) -> bool:
    if stat not in {"ninjutsu", "taijutsu", "genjutsu", "defense", "speed"}:
        return False
    setattr(state.stats, stat, getattr(state.stats, stat) + max(1, points))
    return True


def find_item(state: GameState, item_name: str) -> Optional[InventoryItem]:
    return next((item for item in state.inventory if item.name == item_name), None)


def add_item(state: GameState, item_name: str, quantity: int = 1) -> None:
    if item_name in SHOP:
        description = SHOP[item_name]["description"]
    else:
        description = "عنصر من حقيبة النينجا."
    item = find_item(state, item_name)
    if item:
        item.quantity += quantity
    else:
        state.inventory.append(
            InventoryItem(name=item_name, quantity=max(1, quantity), description=description)
        )


def buy_item(state: GameState, item_name: str, quantity: int = 1) -> tuple[bool, str]:
    if item_name not in SHOP:
        return False, "هذا العنصر غير متوفر."
    quantity = max(1, min(int(quantity), 20))
    total = SHOP[item_name]["price"] * quantity
    if state.ryo < total:
        return False, "لا تملك ريو كافية."
    state.ryo -= total
    add_item(state, item_name, quantity)
    add_log(state, f"اشتريت {item_name} ×{quantity} مقابل {total} ريو.")
    return True, f"تم الشراء: {item_name} ×{quantity} مقابل {total} ريو."


def use_item(state: GameState, item_name: str) -> tuple[bool, str]:
    item = find_item(state, item_name)
    if not item or item.quantity < 1:
        return False, "العنصر غير موجود في الحقيبة."

    if item_name == "حبوب التشاكرا":
        restored = min(35, state.max_chakra - state.chakra)
        if restored <= 0:
            return False, "التشاكرا ممتلئة بالفعل."
        state.chakra += restored
        result = f"استعدت {restored} نقطة تشاكرا."
    elif item_name == "مرهم طبي":
        restored = min(35, state.max_hp - state.hp)
        if restored <= 0:
            return False, "صحتك ممتلئة بالفعل."
        state.hp += restored
        result = f"استعدت {restored} نقطة صحة."
    else:
        return False, "لا يمكن استخدام هذا العنصر خارج القتال."

    item.quantity -= 1
    add_log(state, result)
    return True, result


def rest(state: GameState) -> str:
    if state.defeated:
        return "لا تستطيع الراحة وأنت عاجز عن الحركة."
    state.hp = min(state.max_hp, state.hp + 20)
    state.chakra = min(state.max_chakra, state.chakra + 25)
    state.kawarimi = state.max_kawarimi
    add_log(state, "استراح اللاعب واستعاد جزءًا من صحته وتشاكراه.")
    if state.player.alignment == "نينجا مارق" and random.random() < 0.35:
        damage = random.randint(8, 18)
        state.hp = max(0, state.hp - damage)
        state.anbu_heat = min(100, state.anbu_heat + 5)
        state.defeated = state.hp <= 0
        add_log(state, f"قوطعت الراحة بهجوم صيادي النينجا؛ خسرت {damage} صحة.")
        return f"استعدت بعض قواك، لكن صيادي النينجا باغتوك وأصابوك بـ{damage} نقطة."
    return "استعدت بعض الصحة والتشاكرا، وأُعيد ملء خانات الكاواريمي."


def meditate(state: GameState) -> str:
    if state.defeated:
        return "لا تستطيع التأمل وأنت عاجز عن الحركة."
    restored = min(30, state.max_chakra - state.chakra)
    state.chakra += restored
    state.storm_gauge = min(100, state.storm_gauge + 12)
    if restored == 0:
        return "التشاكرا ممتلئة؛ عزز التأمل مقياس العاصفة."
    add_log(state, f"تأمل اللاعب واستعاد {restored} تشاكرا.")
    return f"استعدت {restored} تشاكرا، وارتفع مقياس العاصفة."


def become_rogue(state: GameState) -> str:
    state.player.alignment = "نينجا مارق"
    state.bounty = max(state.bounty, 500)
    state.anbu_heat = min(100, state.anbu_heat + 20)
    add_log(state, "غادر اللاعب صفوف القرية وأصبح نينجا مارقًا.")
    return "صرت نينجا مارقًا. أُدرج اسمك في سجل المطلوبين وارتفعت حرارة مطاردتك."


def attempt_awakening(state: GameState, form: str) -> tuple[bool, str]:
    forms = {
        "نمط الناسك": 35,
        "علامة اللعنة": 30,
        "طور التشاكرا": 45,
        "سوسانو": 60,
    }
    if form not in forms:
        return False, "حالة الاستيقاظ غير معروفة."
    cost = forms[form]
    if state.chakra < cost:
        return False, "لا تملك تشاكرا كافية."
    if state.storm_gauge < 60:
        return False, "مقياس العاصفة يجب أن يبلغ 60 على الأقل."
    state.chakra -= cost
    state.storm_gauge = max(0, state.storm_gauge - 25)
    state.awakening = form
    add_log(state, f"فعّل اللاعب حالة {form}.")
    return True, f"فعّلت {form}؛ استعد لتحمل كلفة هذه القوة."


def end_awakening(state: GameState) -> None:
    if state.awakening:
        add_log(state, f"انتهت حالة {state.awakening}.")
    state.awakening = None


def finish_quest(state: GameState, index: int = 0) -> tuple[bool, str]:
    active = [quest for quest in state.quests if quest.status == "نشطة"]
    if not active:
        return False, "لا توجد مهمة نشطة."
    quest = active[min(max(index, 0), len(active) - 1)]
    quest.status = "مكتملة"
    state.ryo += quest.reward_ryo
    level_messages = award_exp(state, 60)
    add_log(state, f"أُنجزت المهمة: {quest.title}.")
    result = f"اكتملت «{quest.title}». حصلت على {quest.reward_ryo} ريو و60 خبرة."
    if level_messages:
        result += " " + " ".join(level_messages)
    return True, result


def resolve_action(state: GameState, action: str) -> str:
    """Resolve a combat move with deterministic costs and bounded consequences."""
    if state.defeated:
        return "أنت عاجز عن القتال. اطلب النجدة أو أعد تحميل الحفظ."

    move = action.strip().lower()
    if move in {"kawarimi", "كاواريمي"}:
        if state.kawarimi < 1:
            return "نفدت خانات الكاواريمي؛ لا تملك بديلًا جاهزًا."
        state.kawarimi -= 1
        state.storm_gauge = min(100, state.storm_gauge + 15)
        add_log(state, "تفادى اللاعب الضربة بتقنية الكاواريمي.")
        return "استبدلت موضعك بجذع خشبي في اللحظة الأخيرة. استُهلكت خانة كاواريمي."

    costs = {
        "taijutsu": (0, 8, "هجوم تايجتسو"),
        "ninjutsu": (18, 12, "نينجتسو"),
        "ougi": (35, 20, "أوغي"),
    }
    if move not in costs:
        return "اختر هجوم تايجتسو أو نينجتسو أو أوغي أو كاواريمي."
    chakra_cost, base_damage, label = costs[move]
    if state.chakra < chakra_cost:
        return "تشاكراك لا تكفي لتنفيذ هذه الحركة."

    state.chakra -= chakra_cost
    power = {
        "taijutsu": state.stats.taijutsu,
        "ninjutsu": state.stats.ninjutsu,
        "ougi": state.stats.ninjutsu + state.stats.taijutsu,
    }[move]
    damage = base_damage + power // 3
    if move == "ougi":
        if state.storm_gauge < 50:
            state.chakra += chakra_cost
            return "الأوغي غير متاح قبل بلوغ مقياس العاصفة 50."
        state.storm_gauge = max(0, state.storm_gauge - 40)
    else:
        state.storm_gauge = min(100, state.storm_gauge + 12)

    if state.awakening:
        damage = int(damage * 1.3)
    enemy_damage = max(1, damage - random.randint(0, 5))

    # A successful strike can improve a key relationship only slightly.
    state.hp = max(0, state.hp - random.randint(4, 12))
    state.defeated = state.hp <= 0
    add_log(state, f"نفذ اللاعب {label} وألحق {enemy_damage} ضررًا، لكنه تلقى ضربة مقابلة.")
    if state.defeated:
        return f"أصبت خصمك بـ{enemy_damage} ضررًا، لكن الضربة المرتدة أسقطتك. لا توجد حماية من العواقب."
    return (
        f"نفذت {label} وألحقت {enemy_damage} ضررًا. "
        "لكن الخصم ردّ بضربة؛ خسرت بعض الصحة."
    )


def apply_relationship_delta(
    state: GameState, npc_name: str, delta: int, note: str = ""
) -> None:
    relationship = state.relationships.get(npc_name)
    if relationship is None:
        relationship = Relationship(name=npc_name)
        state.relationships[npc_name] = relationship
    relationship.sentiment = max(-100, min(100, relationship.sentiment + delta))
    if note:
        relationship.note = note[:240]
