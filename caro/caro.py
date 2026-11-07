#!/usr/bin/env python3
"""Cờ Caro - phần mềm chơi cờ caro (gomoku) trên máy tính.

Chạy:  python caro.py
Yêu cầu: Python 3.8+ và pygame  (pip install pygame)

Luật: bàn 15x15, ai có 5 quân liên tiếp (ngang, dọc, chéo) trước là thắng.
Phím tắt: N = ván mới, U = đi lại, M = đổi chế độ, Esc = thoát.
"""
import random
import sys

import pygame

SIZE = 15            # số ô mỗi cạnh
CELL = 40            # kích thước một ô (pixel)
MARGIN = 30          # lề bàn cờ
PANEL_W = 260        # bảng điều khiển bên phải
BOARD_PX = SIZE * CELL
WIN_W = MARGIN * 2 + BOARD_PX + PANEL_W
WIN_H = MARGIN * 2 + BOARD_PX

EMPTY, X, O = 0, 1, 2
NAMES = {X: "X", O: "O"}
DIRS = ((1, 0), (0, 1), (1, 1), (1, -1))

BG = (245, 233, 208)
GRID = (170, 140, 100)
PANEL_BG = (52, 58, 70)
X_COLOR = (205, 45, 45)
O_COLOR = (35, 90, 200)
LAST_COLOR = (255, 215, 90)
WIN_COLOR = (60, 190, 90)
TEXT = (240, 240, 240)
BTN = (80, 90, 108)
BTN_HOVER = (105, 118, 140)


# ---------------------------------------------------------------- luật chơi
def in_board(r, c):
    return 0 <= r < SIZE and 0 <= c < SIZE


def winning_line(board, r, c):
    """Trả về danh sách 5+ ô thắng đi qua (r, c), hoặc None."""
    p = board[r][c]
    if p == EMPTY:
        return None
    for dr, dc in DIRS:
        cells = [(r, c)]
        for sgn in (1, -1):
            rr, cc = r + dr * sgn, c + dc * sgn
            while in_board(rr, cc) and board[rr][cc] == p:
                cells.append((rr, cc))
                rr += dr * sgn
                cc += dc * sgn
        if len(cells) >= 5:
            return cells
    return None


# ---------------------------------------------------------------- máy chơi
# Điểm cho một chuỗi theo (số quân liên tiếp, số đầu bị chặn)
ATTACK = {(5, 0): 10**7, (5, 1): 10**7, (5, 2): 10**7,
          (4, 0): 10**5, (4, 1): 5000, (3, 0): 3000, (3, 1): 300,
          (2, 0): 200, (2, 1): 30, (1, 0): 10, (1, 1): 2}


def line_score(board, r, c, player):
    """Điểm nếu `player` đặt quân tại (r, c)."""
    total = 0
    fours = threes = 0
    for dr, dc in DIRS:
        count = 1
        blocked = 0
        gap_bonus = 0
        for sgn in (1, -1):
            rr, cc = r + dr * sgn, c + dc * sgn
            while in_board(rr, cc) and board[rr][cc] == player:
                count += 1
                rr += dr * sgn
                cc += dc * sgn
            if not in_board(rr, cc) or board[rr][cc] != EMPTY:
                blocked += 1
            else:
                # Mẫu có khoảng trống: X X _ X
                r2, c2 = rr + dr * sgn, cc + dc * sgn
                if in_board(r2, c2) and board[r2][c2] == player:
                    gap_bonus += 1
        if count >= 5:
            return 10**7
        if blocked == 2:
            continue
        s = ATTACK.get((count, blocked), 0)
        if gap_bonus and count + 1 >= 4:
            s = max(s, 4000 if blocked == 0 else 1500)
        elif gap_bonus:
            s += 100
        total += s
        if count == 4 or (count == 3 and gap_bonus):
            fours += 1
        if count == 3 and blocked == 0:
            threes += 1
    # Nước đôi (4-3, 3-3, 4-4) gần như chắc thắng
    if fours >= 2 or (fours and threes):
        total += 50000
    elif threes >= 2:
        total += 20000
    return total


def ai_move(board, me):
    opp = X if me == O else O
    stones = [(r, c) for r in range(SIZE) for c in range(SIZE) if board[r][c]]
    if not stones:
        return SIZE // 2, SIZE // 2
    cand = set()
    for r, c in stones:
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                rr, cc = r + dr, c + dc
                if in_board(rr, cc) and board[rr][cc] == EMPTY:
                    cand.add((rr, cc))
    best, best_moves = -1, []
    for r, c in cand:
        attack = line_score(board, r, c, me)
        defend = line_score(board, r, c, opp)
        score = attack * 1.1 + defend
        if score > best:
            best, best_moves = score, [(r, c)]
        elif score == best:
            best_moves.append((r, c))
    return random.choice(best_moves)


# ---------------------------------------------------------------- giao diện
class Button:
    def __init__(self, rect, label, action):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.action = action

    def draw(self, surf, font):
        hover = self.rect.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(surf, BTN_HOVER if hover else BTN, self.rect, border_radius=8)
        txt = font.render(self.label, True, TEXT)
        surf.blit(txt, txt.get_rect(center=self.rect.center))


def load_font(size, bold=False):
    for name in ("segoeui", "arial", "dejavusans", "notosans", "helvetica"):
        path = pygame.font.match_font(name, bold=bold)
        if path:
            return pygame.font.Font(path, size)
    return pygame.font.Font(None, size + 6)


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Cờ Caro")
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        self.clock = pygame.time.Clock()
        self.font = load_font(18)
        self.font_big = load_font(30, bold=True)
        self.font_small = load_font(15)
        self.vs_ai = True
        self.human = X           # người chơi cầm X (đi trước)
        self.score = {X: 0, O: 0}
        px = MARGIN * 2 + BOARD_PX + 20
        w = PANEL_W - 40
        self.buttons = [
            Button((px, 300, w, 42), "Ván mới (N)", self.new_game),
            Button((px, 352, w, 42), "Đi lại (U)", self.undo),
            Button((px, 404, w, 42), "Đổi chế độ (M)", self.toggle_mode),
            Button((px, 456, w, 42), "Đổi bên đi trước", self.swap_side),
        ]
        self.new_game()

    # ---- điều khiển
    def new_game(self):
        self.board = [[EMPTY] * SIZE for _ in range(SIZE)]
        self.history = []
        self.turn = X
        self.winner = None
        self.win_cells = []
        self.ai_wait = 0
        if self.vs_ai and self.human == O:
            self.ai_wait = pygame.time.get_ticks() + 300

    def toggle_mode(self):
        self.vs_ai = not self.vs_ai
        self.new_game()

    def swap_side(self):
        self.human = O if self.human == X else X
        self.new_game()

    def undo(self):
        steps = 2 if self.vs_ai else 1
        if self.vs_ai and self.history and self.board[self.history[-1][0]][self.history[-1][1]] == self.human:
            steps = 1
        for _ in range(steps):
            if not self.history:
                break
            r, c = self.history.pop()
            if self.winner and self.winner != "draw":
                self.score[self.winner] -= 1
            self.turn = self.board[r][c]
            self.board[r][c] = EMPTY
            self.winner = None
            self.win_cells = []

    def place(self, r, c):
        if self.winner or self.board[r][c] != EMPTY:
            return
        self.board[r][c] = self.turn
        self.history.append((r, c))
        line = winning_line(self.board, r, c)
        if line:
            self.winner = self.turn
            self.win_cells = line
            self.score[self.turn] += 1
        elif len(self.history) == SIZE * SIZE:
            self.winner = "draw"
        else:
            self.turn = X if self.turn == O else O
            if self.vs_ai and self.turn != self.human:
                self.ai_wait = pygame.time.get_ticks() + 250

    # ---- vẽ
    def cell_center(self, r, c):
        return MARGIN + c * CELL + CELL // 2, MARGIN + r * CELL + CELL // 2

    def draw(self):
        s = self.screen
        s.fill(BG)
        board_rect = pygame.Rect(MARGIN, MARGIN, BOARD_PX, BOARD_PX)
        for i in range(SIZE + 1):
            pygame.draw.line(s, GRID, (MARGIN, MARGIN + i * CELL), (MARGIN + BOARD_PX, MARGIN + i * CELL))
            pygame.draw.line(s, GRID, (MARGIN + i * CELL, MARGIN), (MARGIN + i * CELL, MARGIN + BOARD_PX))
        pygame.draw.rect(s, (120, 90, 60), board_rect, 3)

        # ô đang trỏ chuột
        mx, my = pygame.mouse.get_pos()
        if board_rect.collidepoint(mx, my) and not self.winner:
            c, r = (mx - MARGIN) // CELL, (my - MARGIN) // CELL
            if self.board[r][c] == EMPTY:
                hl = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
                hl.fill((0, 0, 0, 25))
                s.blit(hl, (MARGIN + c * CELL, MARGIN + r * CELL))

        if self.history:
            r, c = self.history[-1]
            pygame.draw.rect(s, LAST_COLOR, (MARGIN + c * CELL + 1, MARGIN + r * CELL + 1, CELL - 1, CELL - 1))
        for r, c in self.win_cells:
            pygame.draw.rect(s, WIN_COLOR, (MARGIN + c * CELL + 1, MARGIN + r * CELL + 1, CELL - 1, CELL - 1))

        for r in range(SIZE):
            for c in range(SIZE):
                p = self.board[r][c]
                cx, cy = self.cell_center(r, c)
                d = CELL // 2 - 8
                if p == X:
                    pygame.draw.line(s, X_COLOR, (cx - d, cy - d), (cx + d, cy + d), 5)
                    pygame.draw.line(s, X_COLOR, (cx - d, cy + d), (cx + d, cy - d), 5)
                elif p == O:
                    pygame.draw.circle(s, O_COLOR, (cx, cy), d + 1, 4)

        # bảng bên phải
        px = MARGIN * 2 + BOARD_PX
        pygame.draw.rect(s, PANEL_BG, (px, 0, PANEL_W, WIN_H))
        x0 = px + 20
        s.blit(self.font_big.render("CỜ CARO", True, TEXT), (x0, 28))
        mode = "Người vs Máy" if self.vs_ai else "2 người chơi"
        s.blit(self.font.render("Chế độ: " + mode, True, TEXT), (x0, 80))
        if self.vs_ai:
            s.blit(self.font_small.render(f"Bạn cầm {NAMES[self.human]}  (X đi trước)", True, (200, 200, 210)), (x0, 106))

        if self.winner == "draw":
            msg, col = "Hòa!", TEXT
        elif self.winner:
            if self.vs_ai:
                msg = "Bạn thắng!" if self.winner == self.human else "Máy thắng!"
            else:
                msg = f"{NAMES[self.winner]} thắng!"
            col = X_COLOR if self.winner == X else O_COLOR
        else:
            if self.vs_ai:
                msg = "Lượt của bạn" if self.turn == self.human else "Máy đang nghĩ..."
            else:
                msg = f"Lượt: {NAMES[self.turn]}"
            col = X_COLOR if self.turn == X else O_COLOR
        box = pygame.Rect(x0, 140, PANEL_W - 40, 56)
        pygame.draw.rect(s, (235, 235, 240), box, border_radius=10)
        t = self.font_big.render(msg, True, col)
        if t.get_width() > box.width - 10:
            t = self.font.render(msg, True, col)
        s.blit(t, t.get_rect(center=box.center))

        s.blit(self.font.render(f"Tỉ số   X {self.score[X]}  -  {self.score[O]} O", True, TEXT), (x0, 220))
        s.blit(self.font_small.render(f"Số nước đã đi: {len(self.history)}", True, (200, 200, 210)), (x0, 252))

        for b in self.buttons:
            b.draw(s, self.font)
        s.blit(self.font_small.render("5 quân liên tiếp để thắng", True, (180, 180, 190)), (x0, WIN_H - 40))
        pygame.display.flip()

    # ---- vòng lặp chính
    def run(self):
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                    pygame.quit()
                    sys.exit()
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_n:
                        self.new_game()
                    elif e.key == pygame.K_u:
                        self.undo()
                    elif e.key == pygame.K_m:
                        self.toggle_mode()
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    for b in self.buttons:
                        if b.rect.collidepoint(e.pos):
                            b.action()
                            break
                    else:
                        mx, my = e.pos
                        c, r = (mx - MARGIN) // CELL, (my - MARGIN) // CELL
                        if MARGIN <= mx < MARGIN + BOARD_PX and MARGIN <= my < MARGIN + BOARD_PX:
                            if not self.vs_ai or self.turn == self.human:
                                self.place(r, c)

            if (self.vs_ai and not self.winner and self.turn != self.human
                    and pygame.time.get_ticks() >= self.ai_wait):
                self.place(*ai_move(self.board, self.turn))

            self.draw()
            self.clock.tick(60)


if __name__ == "__main__":
    Game().run()
