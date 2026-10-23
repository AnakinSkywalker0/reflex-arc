"""Angaraka mission-control presentation. Reads game state; never changes it.

All clickable controls return existing keyboard actions to main.py. Textures are
coordinate hashes, independent of the simulation's random numbers and terrain.
"""
import math
import textwrap
import pygame
import config as C
import settings as S

HEADER = 64
AMBER = (190, 177, 148)
CYAN = (111, 190, 183)
PANEL = (30, 34, 39)
BORDER = (53, 60, 67)
MEMORY_HANDLE_W = 92


def text(surf, font, value, pos, color=None, width=None):
    value = str(value)
    if width is not None and font.size(value)[0] > width:
        while value and font.size(value + "...")[0] > width:
            value = value[:-1]
        value += "..."
    surf.blit(font.render(value, True, color or C.INK), pos)


def card(surf, rect, title, f, accent=CYAN, badge=None):
    pygame.draw.rect(surf, PANEL, rect, border_radius=8)
    pygame.draw.rect(surf, BORDER, rect, 1, border_radius=8)
    pygame.draw.rect(surf, accent, (rect.x + 13, rect.y + 14, 3, 13), border_radius=1)
    text(surf, f.chat_head, title, (rect.x + 25, rect.y + 14), accent)
    if badge and f.chat_head.size(title)[0] + f.tiny.size(badge)[0] + 60 < rect.w:
        label = f.tiny.render(badge, True, C.MUTED)
        surf.blit(label, (rect.right - label.get_width() - 14, rect.y + 15))


def bar(surf, rect, amount, color=CYAN):
    pygame.draw.rect(surf, (47, 53, 58), rect, border_radius=4)
    fill = rect.copy()
    fill.width = round(rect.width * max(0, min(1, amount)))
    if fill.width:
        pygame.draw.rect(surf, color, fill, border_radius=4)


def header(surf, w, f):
    pygame.draw.rect(surf, (21, 24, 28), (0, 0, surf.get_width(), HEADER - 8))
    pygame.draw.line(surf, BORDER, (15, HEADER - 8), (surf.get_width(), HEADER - 8))
    x, y = 30, 28
    pygame.draw.polygon(surf, AMBER, [(x, y-15), (x-15, y+12), (x-5, y+8), (x, y-2)])
    pygame.draw.polygon(surf, AMBER, [(x+4, y-13), (x+17, y+12), (x+7, y+8), (x+4, y)])
    pygame.draw.polygon(surf, AMBER, [(x+2,y+4),(x-5,y+15),(x+9,y+15)])
    text(surf, f.brand, 'A N G A R A K A', (58, 10), AMBER)
    text(surf, f.tiny, 'MISSION CONTROL  /  REFLEX ARC', (60, 38), C.MUTED)
    if surf.get_width() > 520:
        text(surf, f.hud, f'SOL {w.day:02d}', (surf.get_width()-110, 20), CYAN)


def rover(surf, cx, cy, size=None, heading=-90):
    unit = max(2, (C.TILE if size is None else size) // 6)
    pygame.draw.circle(surf, (53, 73, 77), (cx,cy), unit*4, 1)
    for dx in (-2, 2):
        for dy in (-2, 0, 2):
            r = pygame.Rect(cx+dx*unit-2, cy+dy*unit-2, 4, 4)
            pygame.draw.rect(surf, (17,20,23), r.inflate(2,2), border_radius=2)
            pygame.draw.rect(surf, C.INK, r, border_radius=1)
    r = pygame.Rect(cx-unit, cy-unit*2, unit*2+1, unit*4+1)
    pygame.draw.rect(surf, C.INK, r, border_radius=2)
    pygame.draw.rect(surf, CYAN, r.inflate(-2,-4), border_radius=1)
    pygame.draw.line(surf, C.INK, (cx+unit,cy-unit), (cx+unit*2,cy-unit*4))
    pygame.draw.circle(surf, CYAN, (cx+unit*2,cy-unit*4), 2)
    # Independent camera turret: the bright lens and sight rays show its aim.
    angle = math.radians(heading)
    def point(forward, side=0):
        return (round(cx + math.cos(angle)*forward - math.sin(angle)*side),
                round(cy + math.sin(angle)*forward + math.cos(angle)*side))
    for side in (-1, 1):
        pygame.draw.line(surf, CYAN, point(unit*2, side*unit),
                         point(unit*5, side*unit*2), 1)
    pygame.draw.circle(surf, PANEL, (cx, cy), unit*2)
    pygame.draw.polygon(surf, C.INK, [point(-unit,-unit), point(unit*2,-unit),
                                    point(unit*2,unit), point(-unit,unit)])
    pygame.draw.line(surf, CYAN, point(unit*2,-unit), point(unit*2,unit), 3)


def map_telemetry(surf, w, f, view, ox, oy, tile, reel=None):
    """Floating grid coordinates follow the displayed bot and its route target."""
    pos = reel.where(w.pos) if reel else w.pos
    def label(cell, value, color, below=False):
        center = (ox + cell[0]*tile + tile//2, oy + cell[1]*tile + tile//2)
        rendered = f.tiny.render(value, True, color)
        box = rendered.get_rect().inflate(12, 8)
        box.midbottom = (center[0], center[1] - max(16, tile))
        if below:
            box.midtop = (center[0], center[1] + max(16, tile))
        box.clamp_ip(view.inflate(-8, -8))
        pygame.draw.line(surf, color, center, box.center, 1)
        pygame.draw.rect(surf, PANEL, box, border_radius=4)
        pygame.draw.rect(surf, color, box, 1, border_radius=4)
        surf.blit(rendered, (box.x+6, box.y+4))
    if reel and reel.destination is not None:
        target = reel.destination
        rect = pygame.Rect(ox+target[0]*tile, oy+target[1]*tile, tile, tile)
        pygame.draw.rect(surf, C.PLAN, rect.inflate(4, 4), 2)
        label(target, f'{reel.destination_status} ({target[0]}, {target[1]})', C.PLAN, True)
    label(pos, f'BOT ({pos[0]}, {pos[1]})', CYAN)


def map_overlay(surf, w, f, view, ox, oy, reel):
    # Grid over both surveyed and unknown regions conveys coordinates without
    # disclosing hidden geology. Labels are only attached to visible objects.
    old = surf.get_clip()
    surf.set_clip(view)
    grid = pygame.Surface(view.size, pygame.SRCALPHA)
    for x in range(w.here.w+1):
        px = ox + x*C.TILE - view.x
        pygame.draw.line(grid, (160,170,174,27), (px,0), (px,view.h))
    for y in range(w.here.h+1):
        py = oy + y*C.TILE - view.y
        pygame.draw.line(grid, (160,170,174,27), (0,py), (view.w,py))
    surf.blit(grid, view.topleft)
    for cell, obj in w.here.objectives.items():
        if not w.here.visible(*cell) or (reel and reel.veiled(cell)):
            continue
        x, y = ox+cell[0]*C.TILE, oy+cell[1]*C.TILE
        text(surf, f.tiny, f'{obj.glyph} / {obj.priority.upper()}', (x+C.TILE+3,y), AMBER)
    # Compact compass and map metadata sit inside the map's frame.
    cx, cy = view.left+38, view.top+43
    pygame.draw.circle(surf, PANEL, (cx,cy), 27)
    pygame.draw.circle(surf, BORDER, (cx,cy), 27, 1)
    pygame.draw.polygon(surf, CYAN, [(cx,cy-13),(cx-5,cy+9),(cx,cy+4)])
    pygame.draw.polygon(surf, C.INK, [(cx,cy-13),(cx+5,cy+9),(cx,cy+4)])
    text(surf, f.tiny, 'N', (cx-3,cy-27), C.INK)
    expand = pygame.Rect(view.right-117, view.top+12, 105, 28)
    pygame.draw.rect(surf, PANEL, expand, border_radius=4)
    pygame.draw.rect(surf, BORDER, expand, 1, border_radius=4)
    text(surf, f.tiny, 'F11 EXPAND', (expand.x+14, expand.y+8), CYAN)
    label = 'JEZERO / SURFACE TELEMETRY' 
    text(surf, f.tiny, label, (view.left+12,view.bottom-22), C.MUTED)
    pos = reel.where(w.pos) if reel else w.pos
    value = f'X {pos[0]:02.0f}  Y {pos[1]:02.0f}'
    tw = f.tiny.size(value)[0]
    text(surf, f.tiny, value, (view.right-tw-12,view.bottom-22), CYAN)
    # Floating coordinates take priority over compass, controls and metadata.
    map_telemetry(surf, w, f, view, ox, oy, C.TILE, reel)
    surf.set_clip(old)
    pygame.draw.rect(surf, BORDER, view.inflate(2,2), 1, border_radius=6)


def buttons(size):
    width, height = size
    y = height-C.HUD_H+44
    available = width-42
    bw = (available-16)//3
    return [(pygame.Rect(15+i*(bw+8),y,bw,34), label,key)
            for i,(label,key) in enumerate((('M  MAP',pygame.K_m),
                ('T  TERMINAL',pygame.K_t),('O  SETTINGS',pygame.K_o)))]


def bottom(surf, w, f, reel):
    y = surf.get_height()-C.HUD_H+8
    rect = pygame.Rect(15,y,surf.get_width()-30,C.HUD_H-18)
    card(surf,rect,'FLIGHT CONTROLS',f,badge=f'{S.ANIM_SPEED:g}x ANIMATION')
    for r,label,key in buttons(surf.get_size()):
        hover = pygame.display.get_init() and r.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(surf,(48,62,64) if hover else (33,38,43),r,border_radius=5)
        pygame.draw.rect(surf,AMBER if hover else BORDER,r,1,border_radius=5)
        label_s = f.chat_head.render(label,True,AMBER if hover else C.INK)
        surf.blit(label_s,label_s.get_rect(center=r.center))
    text(surf,f.tiny,'WASD drive   X mark   TAB chat   ESC quit',(28,y+79),C.MUTED)
    hint = 'SPACE confirm rover stopped' if w.awaiting_rover is not None else (
        'SPACE skip animation' if reel and reel.busy else 'Q end day   C comms   H reasoning   P notes')
    text(surf,f.tiny,hint,(28,y+96),CYAN,rect.w-24)


def telemetry(surf, conv, w, f, reel):
    width,height = surf.get_size()
    pygame.draw.rect(surf,(21,24,28),(0,0,width,HEADER-8))
    pygame.draw.line(surf,BORDER,(0,HEADER-8),(width-15,HEADER-8))
    link = 'FALLBACK' if conv.link.down else 'COMMS ON' if S.COMMS else 'COMMS OFF'
    color = AMBER if conv.link.down else C.GOOD if S.COMMS else C.MUTED
    pygame.draw.circle(surf,color,(22,27),4)
    text(surf,f.chat_head,link,(34,20),color)
    label = f'SOL {w.day:02d} / {w.phase.upper()}'
    text(surf,f.chat_head,label,(width-f.chat_head.size(label)[0]-20,20),AMBER)
    x,wide = 8,width-20
    status = pygame.Rect(x,HEADER,wide,113)
    card(surf,status,'ROVER STATUS',f)
    gap = wide//3
    seen = sum(1 for cell in w.here.seen if not reel or not reel.veiled(cell))
    coverage = seen/(w.here.w*w.here.h)
    left = x+16
    text(surf,f.tiny,'BATTERY',(left,HEADER+39),C.MUTED)
    text(surf,f.chat_head,f'{w.battery / max(1,S.BATTERY):.0%}',(left+gap-54,HEADER+39),CYAN)
    bar(surf,pygame.Rect(left,HEADER+58,gap-28,6),w.battery/max(1,S.BATTERY),C.GOOD if w.battery>S.BATTERY*.2 else C.BAD)
    text(surf,f.tiny,'SURVEYED',(left,HEADER+75),C.MUTED)
    text(surf,f.chat_head,f'{coverage:.0%}',(left+gap-54,HEADER+75),CYAN)
    bar(surf,pygame.Rect(left,HEADER+94,gap-28,6),coverage)
    for i in (1,2):
        pygame.draw.line(surf,BORDER,(x+i*gap,HEADER+39),(x+i*gap,HEADER+99))
    mins,secs=divmod(max(0,int(w.time_left)),60)
    pos = reel.where(w.pos) if reel else w.pos
    for i,heading,value,sub in ((1,'SOL REMAINING',f'{mins:02d}:{secs:02d}',w.phase.upper()),
                               (2,'POSITION',f'X {pos[0]:.0f}  Y {pos[1]:.0f}',
                                'STRANDED' if w.stranded else 'ROVER LOST' if w.lost else 'SURFACE ROVER')):
        xx=x+i*gap+14
        text(surf,f.tiny,heading,(xx,HEADER+39),C.MUTED,gap-20)
        text(surf,f.hud,value,(xx,HEADER+57),C.INK,gap-20)
        text(surf,f.tiny,sub,(xx,HEADER+84),C.GOOD,gap-20)
    # At laptop height retain room for the full, scrollable planner below.
    compact = height < 800
    objective_h = 104 if compact else 176
    top=HEADER+123
    rect=pygame.Rect(x,top,wide,objective_h)
    objectives=list(w.here.objectives.values())
    found=[o for o in w.here.interests.values() if o.found]
    done=len(w.finished)
    card(surf,rect,'SCRATCHPAD',f,AMBER)
    rows=[(f'Objective {o.glyph} / {o.priority} / ({o.cell[0]}, {o.cell[1]})',False) for o in objectives]
    rows += [(f'Examine site ({o.cell[0]}, {o.cell[1]})',False) for o in found]
    rows += [(t,struck) for t,struck in w.notes.todos]
    if not rows:
        text(surf,f.chat,'Explore and survey the terrain',(x+19,top+41),C.INK,wide-35)
        text(surf,f.tiny,'No objectives posted. T opens mission commands.',(x+19,top+65),C.MUTED,wide-35)
    else:
        fit=(objective_h-43)//23
        for i,(label,checked) in enumerate(rows[:fit]):
            yy=top+43+i*23
            pygame.draw.circle(surf,C.GOOD if checked else C.MUTED,(x+23,yy+5),6,1)
            if checked:
                pygame.draw.lines(surf,C.GOOD,False,[(x+20,yy+5),(x+22,yy+7),(x+26,yy+2)],2)
            text(surf,f.chat,label,(x+38,yy-2),C.GOOD if checked else C.INK,wide-55)
        if len(rows)>fit:
            text(surf,f.tiny,f'+{len(rows)-fit} more / P notes / T mission commands',
                 (x+19,top+objective_h-16),C.MUTED,wide-35)
    memory_drawer(surf, rect, w, f)
    top += objective_h+10
    rect=pygame.Rect(x,top,wide,73)
    card(surf,rect,'CURRENT ACTIVITY',f)
    if w.awaiting_rover is not None:
        activity='Physical rover driving / SPACE when stopped'
    elif reel and reel.work:
        cell,n,total = reel.work
        activity=f'Working at {cell} / {n}/{total} steps'
    elif reel and reel.busy:
        activity='Executing rover route'
    elif conv.busy:
        activity='Planner answering' if conv.say_buf else 'Planner thinking'
    else:
        activity=f'{w.phase.capitalize()} / awaiting next instruction'
    text(surf,f.chat,activity,(x+18,top+35),CYAN,wide-35)
    if reel and reel.work:
        bar(surf,pygame.Rect(x+18,top+58,wide-36,4),reel.work[1]/max(1,reel.work[2]))
    top += 83
    return top


def click(pos, game_size, pane_size):
    expand = pygame.Rect(game_size[0]-132, HEADER+27, 105, 28)
    if expand.collidepoint(pos):
        return pygame.K_F11
    for rect,label,key in buttons(game_size):
        if rect.collidepoint(pos):
            return key
    # Clicking the planner's existing input has the same effect as TAB.
    if pos[0] >= game_size[0]+8 and pos[1] >= pane_size[1]-82:
        return pygame.K_TAB
    return None


memory_fraction = 0.0
memory_dragging = False
memory_scroll = 0
memory_rect = pygame.Rect(0, 0, 0, 0)
memory_handle = pygame.Rect(0, 0, 0, 0)
memory_max_scroll = 0


def memory_event(event, offset):
    """Drag the handle left to reveal persistent model memory; wheel scrolls it."""
    global memory_dragging, memory_fraction, memory_scroll
    pos = pygame.mouse.get_pos() if event.type == pygame.MOUSEWHEEL else getattr(event, 'pos', (0, 0))
    pos = (pos[0] - offset, pos[1])
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and memory_handle.collidepoint(pos):
        memory_dragging = True
        return True
    if event.type == pygame.MOUSEMOTION and memory_dragging:
        memory_fraction = max(0., min(1., (memory_rect.right - pos[0] - MEMORY_HANDLE_W) / max(1, memory_rect.w - MEMORY_HANDLE_W)))
        return True
    if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and memory_dragging:
        memory_dragging = False
        return True
    if event.type == pygame.MOUSEWHEEL and memory_rect.collidepoint(pos) and memory_fraction > 0:
        memory_scroll = max(0, min(memory_max_scroll, memory_scroll - event.y * 3))
        return True
    return False


def memory_drawer(surf, rect, w, f):
    global memory_rect, memory_handle, memory_max_scroll, memory_scroll
    memory_rect = rect.copy()
    width = MEMORY_HANDLE_W + round((rect.w - MEMORY_HANDLE_W) * memory_fraction)
    drawer = pygame.Rect(rect.right - width, rect.y, width, rect.h)
    pygame.draw.rect(surf, PANEL, drawer, border_radius=7)
    pygame.draw.rect(surf, BORDER, drawer, 1, border_radius=7)
    memory_handle = pygame.Rect(drawer.x, drawer.y, MEMORY_HANDLE_W, drawer.h)
    text(surf, f.tiny, '< MEMORY', (drawer.x + 7, drawer.y + 16), CYAN)
    text(surf, f.tiny, 'drag', (drawer.x + 20, drawer.y + 36), C.MUTED)
    pygame.draw.line(surf, CYAN, (drawer.x+4,drawer.centery-10), (drawer.x+4,drawer.centery+10), 3)
    content = pygame.Rect(drawer.x + MEMORY_HANDLE_W + 8, drawer.y + 12, max(0, width - MEMORY_HANDLE_W - 20), drawer.h - 24)
    if content.w < 30:
        return
    lines = []
    for name, value in w.notes.memory.items():
        lines.extend(textwrap.wrap(f'{name}: {value}', max(1, content.w // f.memory.size('M')[0])))
        lines.append('')
    if not lines:
        lines = textwrap.wrap('No saved memories yet.', max(1, content.w // f.memory.size('M')[0]))
    line_height = f.memory.get_linesize() + 4
    rows = max(1, content.h // line_height)
    memory_max_scroll = max(0, len(lines) - rows)
    memory_scroll = min(memory_scroll, memory_max_scroll)
    old = surf.get_clip()
    surf.set_clip(content)
    for i, line in enumerate(lines[memory_scroll:memory_scroll+rows]):
        text(surf, f.memory, line, (content.x, content.y+i*line_height), (235, 239, 243))
    surf.set_clip(old)
    if memory_max_scroll:
        bar(surf, pygame.Rect(drawer.right-5, drawer.y+12, 3, drawer.h-24), (memory_scroll+1)/(memory_max_scroll+1))
