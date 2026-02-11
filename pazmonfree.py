import os
import random
import sys
import time
from typing import List, Optional, Tuple

import pygame as pg


# --------------------SettingsOfPazmon begin.--------------------
class SettingsOfPazmon:

    # ---------------- コンストラクタ ----------------

    def __init__(self):
        # ドラッグ演出
        self.DRAG_SCALE = 1.18
        self.DRAG_SHADOW = (0, 0, 0, 90)

    # ---------------- 定義 ----------------
        self.ELEMENT_SYMBOLS = {
            "火": "$",
            "水": "~",
            "風": "@",
            "土": "#",
            "命": "&",
            "無": " "
        }

        self.COLOR_RGB = {
            "火": (230, 70, 70), "水": (70, 150, 230), "風": (90, 200, 120),
            "土": (200, 150, 80), "命": (220, 90, 200), "無": (160, 160, 160)
        }

        self.GEMS = ["火", "水", "風", "土", "命"]
        self.SLOTS = [chr(ord('A')+i) for i in range(14)]

        # その他 可変パラメータ
        self.FRAME_DELAY = 0.2
        self.ENEMY_DELAY = 0.3
        self.WIN_W = 980
        self.WIN_H = 720
        self.FIELD_Y = 520
        self.SLOT_W = 60
        self.SLOT_PAD = 8
        self.LEFT_MARGIN = 30

    # ---------------- フォント解決 ----------------

    def get_jp_font(self, size: int) -> pg.font.Font:
        bundle = os.path.join("assets", "fonts", "NotoSansJP-Regular.ttf")
        if os.path.exists(bundle):
            return pg.font.Font(bundle, size)
        candidates = [
            "Noto Sans CJK JP", "Noto Sans JP",
            "Yu Gothic UI", "Yu Gothic",
            "Meiryo", "MS Gothic",
            "Hiragino Sans", "Hiragino Kaku Gothic ProN",
        ]
        for name in candidates:
            path = pg.font.match_font(name)
            if path:
                return pg.font.Font(path, size)
            return pg.font.SysFont(None, size)

    # ---------------- 画像 ----------------
    def load_monster_image(self, name: str) -> pg.Surface:
        self.m = {
            "スライム": "slime.png",
            "ゴブリン": "goblin.png",
            "オオコウモリ": "bat.png",
            "ウェアウルフ": "werewolf.png",
            "ドラゴン": "dragon.png"
        }
        fn = self.m.get(name)
        if fn:
            path = os.path.join("assets", "monsters", fn)
            if os.path.exists(path):
                img = pg.image.load(path).convert_alpha()
                return pg.transform.smoothscale(img, (256, 256))
        surf = pg.Surface((256, 256), pg.SRCALPHA)
        surf.fill((60, 60, 60, 200))
        return surf

# --------------------SettingsOfPazmon end.--------------------

# --------------GameSystemSettings begin--------------


class GameSystemSettings(SettingsOfPazmon):

    def __init__(self):
        super().__init__()

    def sp_bar_surf(self, sp: int, need_sp: int, color: Tuple, w: int, h: int) -> pg.Surface:
        ratio = max(0, min(1, sp / need_sp if need_sp > 0 else 0))
        bar_w = w
        fill_w = int(bar_w * ratio)
        # バー描画
        surf = pg.Surface((w, h), pg.SRCALPHA)
        # 背景（透明）
        bg = pg.Surface((bar_w, h), pg.SRCALPHA)
        bg.fill((0, 0, 0, 120))
        surf.blit(bg, (0, 0))
        # 黄色バー
        fg = pg.Surface((fill_w, h), pg.SRCALPHA)
        fg.fill(color)
        surf.blit(fg, (0, 0))
        return surf

    # ---------------- HPバー ----------------

    def hp_bar_surf(self, current: int, max_hp: int, w: int, h: int) -> pg.Surface:
        """HPバー（max600基準でスケーリング）"""
        # HP比（0〜1）
        ratio = max(0, min(1, current / max_hp if max_hp > 0 else 0))
        # 600を基準にスケール（例：max_hp=100なら1/6）
        scale = min(1.0, max_hp / 600.0)
        bar_w = int(w * scale)

        # HP割合で塗り幅を決定
        fill_w = int(bar_w * ratio)

    # 色（体力残量による）
        if ratio >= 0.6:
            col = (40, 200, 90)
        elif ratio >= 0.3:
            col = (230, 200, 60)
        else:
            col = (230, 70, 70)

    # バー描画
        surf = pg.Surface((w, h), pg.SRCALPHA)
    # 背景（透明）
        bg = pg.Surface((bar_w, h), pg.SRCALPHA)
        bg.fill((0, 0, 0, 120))
        surf.blit(bg, (0, 0))
    # 緑バー
        fg = pg.Surface((fill_w, h), pg.SRCALPHA)
        fg.fill(col)
        surf.blit(fg, (0, 0))
        return surf

    # ---------------- 盤面ロジック ----------------

    def init_field(self) -> List[str]:
        return [random.choice(self.GEMS) for _ in range(14)]

    def death_field(self) -> List[str]:
        return ["無" for _ in range(14)]

    def leftmost_run(self, field: List[str]) -> Optional[Tuple[int, int]]:
        n = len(field)
        i = 0
        while i < n:
            j = i+1
            while j < n and field[j] == field[i]:
                j += 1
            L = j-i
            if L >= 3 and field[i] in self.GEMS:
                return (i, L)
            i = j
        return None

    def collapse_left(self, field: List[str], start: int, length: int):
        # 消滅部分を '無' にしてから左詰め（簡略：一気に詰める）
        # n = len(field)
        for k in range(start, start+length):
            field[k] = "無"
        rest = [e for e in field if e != "無"]
        field[:] = rest + ["無"]*length

    def fill_random(self, field: List[str]):
        for i, e in enumerate(field):
            if e == "無":
                field[i] = random.choice(self.GEMS)

        # ---------------- ダメージ/回復 ----------------

    def jitter(self, v: float, r: float = 0.10) -> int:
        return max(1, int(v*random.uniform(1-r, 1+r)))

    def attr_coeff(self, att, defe):
        cyc = {"火": "風", "風": "土", "土": "水", "水": "火"}
        if att in cyc and cyc[att] == defe:
            return 2.0
        if defe in cyc and cyc[defe] == att:
            return 0.5
        return 1.0

    def party_attack_from_gems(self, elem: str, run_len: int, combo: int, party: dict, monster: dict) -> int:
        combo_coeff = 1.5 ** ((run_len - 3) + combo)

        if elem == "命":
            heal = self.jitter(20*combo_coeff)
            party["hp"] = min(party["max_hp"], party["hp"]+heal)
            return 0

        ally = next(
            (a for a in party["allies"] if a["element"] == elem), None)

        if not ally:
            return 0

        base = max(1, ally["ap"]-monster["dp"])
        dmg = self.jitter(
            base*self.attr_coeff(elem, monster["element"])*combo_coeff)
        monster["hp"] = max(0, monster["hp"]-dmg)

        return dmg

    def enemy_attack(self, party: dict, monster: dict) -> int:
        base = max(1, monster["ap"]-party["dp"])
        dmg = self.jitter(base)
        party["hp"] = max(0, party["hp"]-dmg)
        return dmg

        # ---------------- 描画ユーティリティ ----------------

    def slot_rect(self, i: int) -> pg.Rect:
        tx = self.LEFT_MARGIN + i * (self.SLOT_W + self.SLOT_PAD)
        return pg.Rect(tx, self.FIELD_Y, self.SLOT_W, self.SLOT_W)

    def draw_gem_at(self, screen, elem: str, x: int, y: int, scale=1.0, with_shadow=False, font=None):

        r = int((self.SLOT_W//2 - 10) * scale)

        if with_shadow:
            shadow = pg.Surface((r*2+6, r*2+6), pg.SRCALPHA)
            pg.draw.circle(shadow, self.DRAG_SHADOW, (r+3, r+3), r+3)
            screen.blit(shadow, (x-r-3, y-r-3))

        pg.draw.circle(screen, self.COLOR_RGB[elem], (x, y), r)

        sym = self.ELEMENT_SYMBOLS[elem]
        f = font if font else self.get_jp_font(int(26*scale))
        s = f.render(sym, True, (0, 0, 0))
        screen.blit(s, (x - s.get_width() // 2, y - s.get_height() // 2))

    def draw_field(self,
                   screen,
                   field: List[str],
                   font,
                   hover_idx: Optional[int] = None,
                   drag_src: Optional[int] = None,
                   drag_elem: Optional[str] = None,
                   x=0, y=0
                   ):
        # スロット見出し
        for i, slot in enumerate(self.SLOTS):
            tx = self.LEFT_MARGIN+i*(self.SLOT_W + self.SLOT_PAD)
            s = font.render(slot, True, (220, 220, 220))
            screen.blit(s, (tx, self.FIELD_Y-28))

        # スロット下地 & ホバー強調
        for i, _ in enumerate(field):
            rect = self.slot_rect(i)
            base = (35, 35, 40) if hover_idx != i else (60, 60, 80)
            rect[0] += x / 10
            rect[2] += x / -10
            rect[1] += y / 10
            rect[3] += y / -10
            pg.draw.rect(screen, base, rect, border_radius=8)

        # 宝石（ドラッグ開始スロットは空に見せる）
        for i, elem in enumerate(field):
            if drag_src is not None and i == drag_src:
                continue
            rect = self.slot_rect(i)
            cx, cy = rect.center

            pg.draw.circle(
                screen,
                self.COLOR_RGB[elem],
                (cx + x/10, cy + y/10),
                self.SLOT_W // 3
            )

            sym = self.ELEMENT_SYMBOLS[elem]
            s = font.render(sym, True, (0, 0, 0))
            screen.blit(s, (cx-s.get_width()//2 + x /
                        10, cy-s.get_height()//2 + y/10))

        # ドラッグ中の宝石（ゴースト）をカーソル位置に拡大表示
        if drag_elem is not None:

            mx, my = pg.mouse.get_pos()
            self.draw_gem_at(
                screen,
                drag_elem,
                mx + x,
                my-4,
                scale=self.DRAG_SCALE,
                with_shadow=True,
                font=font
            )

    def draw_top(self, screen, enemy, party, font, weakFont=None, gainX=0, gainY=0, alpha=200):

        weakElementList = {
            '火': '水',
            '水': '土',
            '土': '風',
            '風': '火',
        }
        # 敵画像/名前
        img = self.load_monster_image(enemy["name"])
        img.set_alpha(alpha)
        screen.blit(img, (40 + gainX/3.5, 40 + gainY/4.5))

        # 敵名とHPバー
        name = font.render(
            enemy["name"], True, (240, 240, 240))
        screen.blit(name, (320, 40))

        enemy_bar = self.hp_bar_surf(
            enemy["hp"],
            enemy["max_hp"],
            420,
            18
        )
        screen.blit(enemy_bar, (320, 80))
        if (weakFont is not None):
            weak = weakFont.render(
                f'[属性: {enemy["element"]} < {self.ELEMENT_SYMBOLS[enemy["element"]]} >   弱点: {weakElementList[enemy["element"]]} < {self.ELEMENT_SYMBOLS[weakElementList[enemy["element"]]]} >]', True, (143, 133, 233))
            screen.blit(weak, (635, 60))

        # 敵HP数値（バー右側に）
        enemy_hp_text = font.render(
            f"{enemy['hp']} / {enemy['max_hp']}",
            True,
            (240, 240, 240)
        )

        screen.blit(enemy_hp_text, (750, 78))

        # 「パーティ」ラベル
        label = font.render("パーティ", True, (240, 240, 240))
        screen.blit(label, (320, 110))

        # パーティHPバー
        party_bar = self.hp_bar_surf(
            party["hp"],
            party["max_hp"],
            420, 18
        )

        screen.blit(party_bar, (320, 140))

        # パーティHP数値
        party_hp_text = font.render(
            f"{int(party['hp'])}/{party['max_hp']}",
            True,
            (240, 240, 240)
        )
        screen.blit(party_hp_text, (750, 138))

        for (i, ally) in enumerate(party["allies"]):
            if "skill" in ally and "sp" in ally:

                # 1. 色は「常に」属性色を使う（これで誰のスキルか分かる！）
                ally_color = self.COLOR_RGB[ally["element"]]

                # 2. バーを描画 (中身は属性色)
                sp_bar = self.sp_bar_surf(
                    ally["sp"],
                    ally["skill"].need_sp,
                    ally_color,
                    300, 12,
                )
                y = 250 + i * 50
                screen.blit(sp_bar, (520, y))

                # 満タンなら「金色の枠」を描く
                if ally["sp"] >= ally["skill"].need_sp:
                    frame_rect = pg.Rect(520, y, 300, 12)
                    pg.draw.rect(screen, (255, 215, 0), frame_rect, 3)
                    ok_text = weakFont.render("OK!", True, (255, 215, 0))
                    screen.blit(ok_text, (830, y - 5))
                else:
                    # 満タンじゃない時はふつうの数値
                    sp_text = font.render(
                        f"{int(ally['sp'])}/{ally['skill'].need_sp}",
                        True,
                        (240, 240, 240)
                    )
                    screen.blit(sp_text, (830, y - 2))

    def draw_message(self, screen, text, font, x=40, y=460):
        surf = font.render(text, True, (230, 230, 230))
        screen.blit(surf, (x, y))


# --------------GameSystemSettings end--------------

# --------------GameItemSettings begin--------------
class Item:
    def __init__(self, item_num):
        self.number_of_item = item_num

    def draw_item_surface(self, screen, font, txt: list):
        for i in range(self.number_of_item):
            text = font.render("A", False, (255, 255, 240))
            pg.draw.rect(screen, (100, 85, 105),
                         (900 - (55 * i), 650, 50, 50))
            screen.blit(text, (900 - (55 * i), 650))

    def clickedItem(self, eventType, num, func=lambda: print("AAA")):
        x, y = pg.mouse.get_pos()
        if (eventType.type == pg.MOUSEBUTTONUP):
            if ((900 - (55 * num) <= x and 900 - (55 * num)+50 >= x) and 650 <= y and 700 >= y):
                func()


# --------------GameItemSettings end--------------

# --------------GameAnimation begin ---------------


class GameAnimation:
    def __init__(self):
        self.deviation_P = 0
        self.deviation_I = 0

    def PID_INIT(self):
        self.deviation_P = 0

    def P_Control(self, gain, input, objVal) -> int:
        self.deviation_P = objVal - input
        return gain * self.deviation_P

    def I_Control(self, gain, input, time=0.1):
        self.deviation_P += input*time
        return gain * self.deviation_P

    def D_Control(self):
        pass

    def PID(self):
        pass

    def abs(self, value):
        if (value >= 0):
            return value
        elif (value < 0):
            return value * -1

# --------------GameAnimation end ---------------

# ---------------- SkillSettings Begin ----------------


class Skill:
    def __init__(self,
                 skill_name: str,
                 need_sp: int,
                 dmg=None,  # 火:タプル、風・水:リスト
                 debuff_ratio: float = None,
                 debuff_turns: int = None,
                 stun_turns: int = None,
                 heal: int = None):
        self.skill_name = skill_name
        self.need_sp = need_sp
        self.dmg = dmg
        self.debuff_ratio = debuff_ratio
        self.debuff_turns = debuff_turns
        self.stun_turns = stun_turns
        self.heal = heal

    def execute(self, party, enemy):  # スキルのメイン処理
        message = []
        message.append(f"【{self.skill_name}】")
        dmg = self._calc_damage(enemy)
        if dmg is not None:
            message.append(f"{dmg}ダメージ！")
        heal = self._calc_heal(party)
        if heal is not None:
            message.append(f"{heal}回復！")
        debuff_res = self._apply_debuff(enemy)
        if debuff_res is not None:
            message.append(f"{enemy['name']}の攻撃力を{debuff_res}ダウン！")
        stun_res = self._apply_stun(enemy)
        if stun_res is not None:
            message.append(f"{enemy['name']}を{stun_res}ターンスタン！")
        return " ".join(message)

    def _calc_damage(self, enemy):  # ダメージ
        if type(self.dmg) == tuple:
            skill_dmg = int(self.dmg[0]+enemy["hp"]*self.dmg[1])
            enemy["hp"] = max(0, enemy["hp"]-skill_dmg)
            return skill_dmg
        if type(self.dmg) == list:
            skill_dmg = int(random.randint(self.dmg[0], self.dmg[1]))
            enemy["hp"] = max(0, enemy["hp"]-skill_dmg)
            return skill_dmg

    def _calc_heal(self, party):  # 回復
        if self.heal is not None:
            party["hp"] = min(party["max_hp"], party["hp"]+self.heal)
            return self.heal

    def _apply_debuff(self, enemy):  # デバフ
        if self.debuff_ratio is not None and self.debuff_turns is not None:
            enemy["status"] = {"type": "atk_down",
                               "turn": self.debuff_turns, "val": self.debuff_ratio}
            return enemy["ap"]-enemy["ap"]*self.debuff_ratio

    def _apply_stun(self, enemy):  # スタン
        if self.stun_turns is not None and self.stun_turns is not 0:
            enemy["status"] = {"type": "stun", "turn": self.stun_turns}
            return self.stun_turns


# ---------------- SkillSettings end ----------------

# ---------------- メイン ----------------


def main():
    pg.init()
    gss = GameSystemSettings()
    pid = GameAnimation()
    screen = pg.display.set_mode((gss.WIN_W, gss.WIN_H))
    pg.display.set_caption("Puzzle & Monsters - GUI Prototype")
    font = gss.get_jp_font(26)
    titleFont = gss.get_jp_font(73)
    weakFont = gss.get_jp_font(17)
    item = Item(4)
    secret = []
    command_list = [
        [1073741906, 1073741906, 1073741905, 1073741905,
            1073741904, 1073741903, 1073741904, 1073741903, 97, 98],
    ]

    itemList = ["力の粉", "お守り", "薬草", "きまぐれ石"]


# スキルインスタンス生成
    skill_wind = Skill("青龍のスキル", 10, [20, 50], stun_turns=3)
    skill_fire = Skill("朱雀のスキル", 10, (30, 0.1))
    skill_earth = Skill("白虎のスキル", 10, heal=50)
    skill_water = Skill(
        "玄武のスキル", 10, [20, 50], debuff_ratio=0.5, debuff_turns=3)

    party = {
        "player_name": "Player",
        "allies": [
            {"name": "青龍", "element": "風", "hp": 150,
             "max_hp": 150, "ap": 15, "dp": 10, "skill": skill_wind, "sp": 0},
            {"name": "朱雀", "element": "火", "hp": 150,
             "max_hp": 150, "ap": 25, "dp": 10, "skill": skill_fire, "sp": 0},
            {"name": "白虎", "element": "土", "hp": 150,
             "max_hp": 150, "ap": 20, "dp": 5, "skill": skill_earth, "sp": 0},
            {"name": "玄武", "element": "水", "hp": 150,
             "max_hp": 150, "ap": 20, "dp": 15, "skill": skill_water, "sp": 0},
        ],
        "hp": 600, "max_hp": 600, "dp": (10+10+5+15)/4
    }

    enemies = [
        {"name": "スライム", "element": "水", "hp": 100,
         "max_hp": 100, "ap": 10, "dp": 1, "status": {"type": None, "turn": 0, "val": None}},
        {"name": "ゴブリン", "element": "土", "hp": 200,
         "max_hp": 200, "ap": 20, "dp": 5, "status": {"type": None, "turn": 0, "val": None}},
        {"name": "オオコウモリ", "element": "風", "hp": 300,
         "max_hp": 300, "ap": 30, "dp": 10, "status": {"type": None, "turn": 0, "val": None}},
        {"name": "ウェアウルフ", "element": "風", "hp": 400,
         "max_hp": 400, "ap": 40, "dp": 15, "status": {"type": None, "turn": 0, "val": None}},
        {"name": "ドラゴン", "element": "火", "hp": 600,
         "max_hp": 600, "ap": 50, "dp": 20, "status": {"type": None, "turn": 0, "val": None}},
    ]

    enemy_idx = 0
    enemy = enemies[enemy_idx]
    field = gss.init_field()

    drag_src: Optional[int] = None
    drag_elem: Optional[str] = None
    hover_idx: Optional[int] = None
    message = "ドラッグで A..N の宝石を移動（例：A→F）"
    clock = pg.time.Clock()
    gameStarting = False

    running = True
    while running:
        for e in pg.event.get():

            if (party["hp"] > 0 and gameStarting == True):
                if e.type == pg.QUIT:
                    running = False

                elif e.type == pg.MOUSEBUTTONDOWN and e.button == 1:
                    mx, my = e.pos
                    if gss.FIELD_Y <= my <= gss.FIELD_Y+gss.SLOT_W:
                        i = (mx-gss.LEFT_MARGIN)//(gss.SLOT_W+gss.SLOT_PAD)
                        if 0 <= i < 14:
                            drag_src = i
                            drag_elem = field[i]
                            message = f"{gss.SLOTS[i]} を掴んだ"
                    else:
                        for i, ally in enumerate(party["allies"]):
                            if "skill" in ally:
                                # 当たり判定を作る (draw_topの座標計算と同じにする)
                                bar_y = 250 + i * 50
                                bar_rect = pg.Rect(520, bar_y, 300, 40)
                                # クリックした場所がバーの中か
                                if bar_rect.collidepoint(mx, my):
                                    skill = ally["skill"]

                                    # SP確認
                                    if ally["sp"] >= skill.need_sp:
                                        # 発動
                                        skill_res = skill.execute(party, enemy)
                                        ally["sp"] -= skill.need_sp
                                        message = skill_res

                                        # 攻撃スキルなら画面を揺らす
                                        if skill.dmg is not None:
                                            # PID（敵の攻撃の時と同じ設定）
                                            pid.PID_INIT()
                                            dev = pid.P_Control(
                                                1.4, 30, 0) + pid.I_Control(0.2, 30)

                                            # 揺れが収まるまでループ
                                            while (pid.abs(pid.deviation_P) > 2):
                                                screen.fill((22, 22, 28))

                                                # 揺れ幅を計算
                                                x = pid.P_Control(
                                                    0.7, dev, 0) + pid.I_Control(0.2, dev)
                                                y = pid.P_Control(
                                                    0.7, dev, 0) + pid.I_Control(0.2, dev)

                                                gss.draw_top(
                                                    screen, enemy, party, font, weakFont, x, y)
                                                gss.draw_field(
                                                    screen, field, font, None, None, None, 0, 0)

                                                gss.draw_message(
                                                    screen, message, font)

                                                pg.display.flip()
                                                dev = x

                                        # 敵が倒れたかチェック
                                        if enemy["hp"] <= 0:
                                            pid.PID_INIT()

                                            dev = pid.P_Control(
                                                1.4, 30, 0) + pid.I_Control(0.2, 30)

                                            # 揺れが収まるまでループ
                                            while (pid.abs(pid.deviation_P) > 2):
                                                screen.fill((22, 22, 28))

                                                # 揺れ幅を計算
                                                x = pid.P_Control(
                                                    0.7, dev, 0) + pid.I_Control(0.2, dev)
                                                y = pid.P_Control(
                                                    0.7, dev, 0) + pid.I_Control(0.2, dev)

                                                gss.draw_top(
                                                    screen, enemy, party, font, weakFont, x, y)
                                                gss.draw_field(
                                                    screen, field, font, None, None, None, 0, 0)

                                                gss.draw_message(
                                                    screen, message, font)

                                                pg.display.flip()
                                                dev = x

                                        # 敵が倒れたかチェック
                                        if enemy["hp"] <= 0:
                                            message = f"{enemy['name']} を倒した！"
                elif e.type == pg.MOUSEMOTION:
                    mx, my = e.pos
                    hi = (mx-gss.LEFT_MARGIN)//(gss.SLOT_W+gss.SLOT_PAD)
                    hy = (gss.SLOT_W+gss.SLOT_PAD)
                    hover_idx = hi if 0 <= hi < 14 else None
                    nowPosX = max(0, min(len(field)-1, hi))
                    if (drag_src is not None):

                        posX = drag_src
                        if (hover_idx is not None and hover_idx != drag_src and hy > abs(my - gss.FIELD_Y)):

                            if (nowPosX - posX <= 1):
                                field[nowPosX], field[posX] = field[posX], field[nowPosX]
                                drag_src = hi

                elif e.type == pg.MOUSEBUTTONUP and e.button == 1:
                    if drag_src is not None:
                        mx, my = e.pos
                        j = (mx-gss.LEFT_MARGIN)//(gss.SLOT_W+gss.SLOT_PAD)
                        if 0 <= j < 14:
                            i = drag_src
                            if i != j:
                                step = 1 if j > i else -1
                                k = i
                                while k != j:
                                    nxt = k + step
                                    field[k], field[nxt] = field[nxt], field[k]
                                    k = nxt
                                    message = f"{gss.SLOTS[k-step]}↔{gss.SLOTS[k]} を交換"
                                    screen.fill((22, 22, 28))
                                    gss.draw_top(
                                        screen, enemy, party, font, weakFont)
                                    gss.draw_field(
                                        screen, field, font, hover_idx=None, drag_src=None, drag_elem=None)
                                    gss.draw_message(screen, message, font)
                                    pg.display.flip()
                                    time.sleep(gss.FRAME_DELAY)

                            # 評価ループ
                            combo = 0
                            while True:
                                run = gss.leftmost_run(field)
                                if not run:
                                    break
                                start, L = run
                                combo += 1
                                elem = field[start]
                                if elem == "命":
                                    heal = gss.jitter(
                                        22.5*(1.4**((L-3)+combo)))
                                    party["hp"] = min(
                                        party["max_hp"], party["hp"]+heal)
                                    message = f"HP +{heal}"
                                else:
                                    dmg = gss.party_attack_from_gems(
                                        elem, L, combo, party, enemy)
                                    message = f"{elem}攻撃！ {dmg} ダメージ"
                                                                       # 攻撃した味方の属性について、宝石を消した分だけその属性のspをためる
                                    for ally in party["allies"]:
                                        if ally["element"] == elem:
                                            ally["sp"] += L
                                            ally["sp"] = min(
                                            ally["sp"], ally["skill"].need_sp)

  
                                    pid.PID_INIT()
                                    dev = pid.P_Control(
                                        1.4, 30, 0) + pid.I_Control(0.2, 30)
                                    cnt = 200
                                    while (pid.abs(pid.deviation_P) > 2):
                                        screen.fill((22, 22, 28))
                                        x = pid.P_Control(
                                            0.7, dev, 0) + pid.I_Control(0.2, dev)
                                        y = pid.P_Control(
                                            0.7, dev, 0) + pid.I_Control(0.2, dev)
                                        if (enemy["hp"] > 0):
                                            gss.draw_top(
                                                screen, enemy, party, font, weakFont, x, 0)
                                        else:
                                            gss.draw_top(
                                                screen, enemy, party, font, weakFont, x, 0, cnt)
                                            cnt -= 10
                                        gss.draw_field(screen, field, font)
                                        gss.draw_message(screen, "消滅！", font)
                                        pg.display.flip()
                                        dev = x

                                gss.collapse_left(field, start, L)
                                screen.fill((22, 22, 28))
                                if (enemy["hp"] > 0):
                                    gss.draw_top(
                                        screen, enemy, party, font, weakFont)
                                else:
                                    gss.draw_top(
                                        screen, enemy, party, font, weakFont, 0, 0, 0)
                                gss.draw_field(screen, field, font)
                                gss.draw_message(screen, "消滅！", font)
                                pg.display.flip()
                                time.sleep(gss.FRAME_DELAY)
                                gss.fill_random(field)
                                screen.fill((22, 22, 28))
                                if (enemy["hp"] > 0):
                                    gss.draw_top(
                                        screen, enemy, party, font, weakFont)
                                else:
                                    gss.draw_top(
                                        screen, enemy, party, font, weakFont, 0, 0, 0)
                                gss.draw_field(screen, field, font)
                                gss.draw_message(screen, "湧き！", font)
                                pg.display.flip()
                                time.sleep(gss.FRAME_DELAY)
                                if enemy["hp"] <= 0:
                                    message = f"{enemy['name']} を倒した！"

                                    break

                            # 敵ターン or 撃破後処理
                            if enemy["hp"] > 0:

                                # 準備
                                status = enemy["status"]
                                act_type = "normal"

                                # 行動パターン決定
                                if status["type"] == "atk_down":
                                    act_type = "weak_atk"
                                if status["type"] == "stun":
                                    act_type = "stun"

                                # 実行
                                edmg = 0
                                if act_type == "normal":
                                    base_dmg = gss.enemy_attack(party, enemy)
                                    edmg = base_dmg
                                    message = f"{enemy['name']}の攻撃！ -{edmg}"
                                if act_type == "atk_down":
                                    base_dmg = gss.enemy_attack(party, enemy)
                                    edmg = int(base_dmg*status["val"])
                                    diff = base_dmg - edmg
                                    party["hp"] += diff
                                    message = f"{enemy['name']}の攻撃(弱)！ -{edmg}(残り{status['turn']}ターン)"
                                if act_type == "stun":
                                    message = f"{enemy['name']}は動けない！残り{status['turn']}ターン"
                                if act_type != "stun":
                                    dev = pid.P_Control(
                                        0.7, 30, 0) + pid.I_Control(0.2, 30)
                                while (pid.abs(pid.deviation_P) > 2):
                                    screen.fill((22, 22, 28))
                                    x = pid.P_Control(
                                        0.7, dev, 0) + pid.I_Control(0.2, dev)
                                    y = pid.P_Control(
                                        0.7, dev, 0) + pid.I_Control(0.2, dev)
                                    gss.draw_top(
                                        screen, enemy, party, font, weakFont)
                                    gss.draw_field(
                                        screen, field, font, None, None, None, x, y)
                                    pg.display.flip()
                                    dev = x
                                screen.fill((22, 22, 28))
                                gss.draw_top(screen, enemy, party,
                                             font, weakFont)
                                gss.draw_field(
                                    screen, field, font, None, None, None)
                                gss.draw_message(screen, message, font)
                                pg.display.flip()
                                time.sleep(gss.ENEMY_DELAY)

                                # ターン処理
                                if status["turn"] is not None and status["turn"] > 0:
                                    status["turn"] -= 1
                                    if status["turn"] == 0:
                                        status["type"] = None
                                        status["val"] = None

                                if party["hp"] <= 0:
                                    message = "パーティは力尽きた…（ESCで終了）"
                            else:
                                enemy_idx += 1
                                if enemy_idx < len(enemies):
                                    enemy = enemies[enemy_idx]
                                    field = gss.init_field()
                                    message = f"さらに奥へ… 次は {enemy['name']}"
                                else:
                                    message = "ダンジョン制覇！おめでとう！（ESCで終了）"

                    drag_src = None
                    drag_elem = None
                    hover_idx = None

            if (e.type == pg.KEYDOWN):
                secret.append(e.key)
# print(secret)  # debug
# print(command_list[0])  # debug

            if (set(command_list[0]) <= set(secret)):
                party["hp"] = 700
                secret.clear()

            # ドラッグ終了
    # 常時描画
        if (party["hp"] > 0 and gameStarting == True):
            screen.fill((22, 22, 28))
            gss.draw_top(screen, enemy, party, font, weakFont)
            gss.draw_field(screen, field, font, hover_idx, drag_src, drag_elem)
            item.draw_item_surface(screen, font, itemList)
            item.clickedItem(e, 1)
            gss.draw_message(screen, message, font)
        elif (party["hp"] <= 0 and gameStarting == True):
            screen.fill((0, 0, 0))
            message = "パーティは力尽きた…（ESCで終了）"
            gss.draw_message(screen, message, font, 300, 360)
        else:
            screen.fill((0, 0, 0))
            messag = "Puzzle AND Monsters"
            gss.draw_message(screen, messag, titleFont, 110, 260)
            msg = "（spaceでスタート）"
            gss.draw_message(screen, msg, weakFont, 600, 360)
        pg.display.flip()
        clock.tick(60)

        keys = pg.key.get_pressed()
        if len(secret) > 16:
            secret.clear()

        if keys[pg.K_ESCAPE]:
            running = False
        elif keys[pg.K_0]:
            party["hp"] = 0

        elif (keys[pg.K_SPACE]):
            gameStarting = True

    pg.quit()
    sys.exit()


if __name__ == "__main__":
    main()
