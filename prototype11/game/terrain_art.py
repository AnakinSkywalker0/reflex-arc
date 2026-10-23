"""Connected, rounded terrain adapted from prototype12b; visual state only."""
from functools import lru_cache
from collections import OrderedDict
import math
import random
import pygame

SEED = 1224

# Rust-red Martian regolith; the reference palette applies to the dashboard.
_GROUND = (178, 98, 62)
_GROUND_DIM = (162, 158, 155)       # multiplier: ground the rover has seen and left
# Neutral basalt, distinct from unexplored fog.
_ROCK = (102, 103, 98)
_ROCK_DIM = (178, 172, 168)         # multiplier, the same idea


def _clamp(v):
    return max(0, min(255, int(v)))


def _noise(w, h, step, rnd, lo, hi, tint=0):
    """Smooth value noise: random grey on a coarse lattice, stretched up bilinearly.

    `step` is the lattice spacing in pixels. `tint` lets g and b drift below r, which
    turns a brightness field into a slight change of hue as well.
    """
    nx, ny = max(2, w // step + 2), max(2, h // step + 2)
    small = pygame.Surface((nx, ny), 0, 32)
    for y in range(ny):
        for x in range(nx):
            v = rnd.randint(lo, hi)
            small.set_at((x, y), (_clamp(v), _clamp(v - rnd.randint(0, tint)),
                                  _clamp(v - rnd.randint(0, tint))))
    return pygame.transform.smoothscale(small, (w, h))


def _grain(w, h, rnd, lo, hi):
    """Per-pixel speckle, built as a small tile and repeated. 160 px does not read as a
    repeat because everything else on the ground is smooth."""
    size = 160
    tile = pygame.Surface((size, size), 0, 32)
    for y in range(size):
        for x in range(size):
            v = rnd.randint(lo, hi)
            tile.set_at((x, y), (v, _clamp(v - rnd.randint(0, 4)), _clamp(v - rnd.randint(0, 6))))
    out = pygame.Surface((w, h), 0, 32)
    for y in range(0, h, size):
        for x in range(0, w, size):
            out.blit(tile, (x, y))
    return out


def _ground(cols, rows, T, rnd):
    W, H = cols * T, rows * T
    g = pygame.Surface((W, H), 0, 32)
    g.fill(_GROUND)
    # Broad patches of paler dust and darker, iron-richer ground, then finer mottling.
    g.blit(_noise(W, H, T * 8, rnd, 196, 255, 22), (0, 0), special_flags=pygame.BLEND_RGB_MULT)
    g.blit(_noise(W, H, int(T * 2.2), rnd, 222, 255, 10), (0, 0),
           special_flags=pygame.BLEND_RGB_MULT)
    g.blit(_grain(W, H, rnd, 228, 255), (0, 0), special_flags=pygame.BLEND_RGB_MULT)

    # Wind ripples: short low arcs, darker in the trough and a little lighter on the crest.
    k = max(1, T // 30)
    dark = pygame.Surface((W, H), 0, 32)
    dark.fill((255, 255, 255))
    light = pygame.Surface((W, H), 0, 32)
    light.fill((0, 0, 0))
    for _ in range(int(cols * rows * 1.4)):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        ln = rnd.uniform(0.5, 1.6) * T
        sl = rnd.uniform(-0.25, 0.1)
        pts = [(x + ln * t / 3, y + ln * t / 3 * sl + math.sin(t * 1.3 + x) * 1.2 * k)
               for t in range(4)]
        pygame.draw.lines(dark, (226, 214, 208), False, pts, 1)
        pygame.draw.lines(light, (20, 11, 6), False, [(a, b - k - 1) for a, b in pts], 1)
    g.blit(dark, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
    g.blit(light, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

    # Pebbles and the odd cobble, each with a lit side and a shadow.
    for _ in range(int(cols * rows * 1.3)):
        x, y = rnd.randint(0, W - 1), rnd.randint(0, H - 1)
        r = rnd.choice((1, 1, 1, 2, 2, 3)) * k
        pygame.draw.circle(g, (66, 33, 22), (x + 1 + k // 2, y + 1 + k // 2), r)
        pygame.draw.circle(g, rnd.choice(((124, 72, 50), (101, 60, 43), (141, 88, 62),
                                          (96, 66, 56))), (x, y), r)
        if r >= 2:
            pygame.draw.circle(g, (186, 126, 96), (x - r // 3, y - r // 3), max(1, r // 3))
    return g


def _rock_layer(cols, rows, T, rocks, rnd):
    """The rocks as one painted layer plus the mask that cuts it out.

    The cell grid is upsampled bilinearly and cut at half, which rounds every corner into
    a boulder rather than a square; low noise on top roughens the outline. The outline
    stays within a few pixels of the real cell edge, so what you see is what the world
    treats as solid.
    """
    W, H = cols * T, rows * T
    cells = pygame.Surface((cols, rows), 0, 32)
    cells.fill((0, 0, 0))
    for (x, y) in rocks:
        cells.set_at((x, y), (255, 255, 255))
    soft = pygame.transform.smoothscale(cells, (W, H))
    soft.blit(_noise(W, H, max(3, T // 3), rnd, 0, 84), (0, 0), special_flags=pygame.BLEND_RGB_ADD)
    soft.fill((42, 42, 42), special_flags=pygame.BLEND_RGB_SUB)
    mask = pygame.mask.from_threshold(soft, (255, 255, 255), (127, 127, 127, 255))

    # A height field: a narrow bevel from the outline, plus hard-edged facets from noise
    # that is pushed to high contrast, so the surface breaks into planes that catch light
    # on one side and not the other. Light from the upper left.
    small = pygame.transform.smoothscale(soft, (max(2, W // 4), max(2, H // 4)))
    height = pygame.transform.smoothscale(small, (W, H))
    height.fill((120, 120, 120), special_flags=pygame.BLEND_RGB_MULT)
    facets = _noise(W, H, max(4, int(T * 0.45)), rnd, 40, 215)
    facets.fill((70, 70, 70), special_flags=pygame.BLEND_RGB_SUB)
    facets.blit(facets, (0, 0), special_flags=pygame.BLEND_RGB_ADD)       # double the contrast
    facets.fill((140, 140, 140), special_flags=pygame.BLEND_RGB_MULT)
    height.blit(facets, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
    d = max(1, T // 15)
    lit = height.copy()
    lit.blit(height, (d, d), special_flags=pygame.BLEND_RGB_SUB)      # faces the light
    shade = height.copy()
    shade.blit(height, (-d, -d), special_flags=pygame.BLEND_RGB_SUB)  # faces away
    lit.blit(lit, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
    lit.fill((225, 230, 220), special_flags=pygame.BLEND_RGB_MULT)
    shade.blit(shade, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
    shade.fill((235, 235, 235), special_flags=pygame.BLEND_RGB_MULT)

    paint = pygame.Surface((W, H), pygame.SRCALPHA)
    paint.fill(_ROCK)
    paint.blit(_noise(W, H, int(T * 1.1), rnd, 150, 255, 5), (0, 0),
               special_flags=pygame.BLEND_RGB_MULT)
    paint.blit(_grain(W, H, rnd, 200, 255), (0, 0), special_flags=pygame.BLEND_RGB_MULT)
    k = max(1, T // 30)
    for _ in range(int(len(rocks) * T * 0.9)):        # mineral flecks, pale and dark
        x, y = rnd.randint(0, W - 1), rnd.randint(0, H - 1)
        paint.set_at((x, y), rnd.choice(((165, 168, 155), (145, 149, 138), (43, 46, 42),
                                         (34, 37, 35))))
        if k > 1:
            pygame.draw.circle(paint, paint.get_at((x, y)), (x, y), k // 2)
    for _ in range(int(len(rocks) * 0.9)):            # cracks
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        ang = rnd.uniform(0, math.tau)
        pts = [(x, y)]
        for _ in range(3):
            ang += rnd.uniform(-0.8, 0.8)
            x, y = x + math.cos(ang) * T * 0.25, y + math.sin(ang) * T * 0.25
            pts.append((x, y))
        pygame.draw.lines(paint, (26, 29, 27), False, pts, 1)
    paint.blit(lit, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
    paint.blit(shade, (0, 0), special_flags=pygame.BLEND_RGB_SUB)

    layer = pygame.Surface((W, H), pygame.SRCALPHA)
    mask.to_surface(layer, setsurface=paint, unsetcolor=(0, 0, 0, 0))
    for part in mask.connected_components():       # a dark edge so each rock reads as an object
        pts = part.outline()
        if len(pts) > 2:
            pygame.draw.lines(layer, (25, 28, 26, 255), True, pts, max(1, T // 20))
    return layer, mask


def _cast_shadow(W, H, T, mask):
    """Ground darkened to the lower right of every rock, as a multiplier image."""
    m = mask.to_surface(setcolor=(255, 255, 255), unsetcolor=(0, 0, 0))
    off = max(3, T // 6)
    s = pygame.Surface((W, H), 0, 32)
    s.fill((0, 0, 0))
    s.blit(m, (off, off + 1))
    s = pygame.transform.smoothscale(pygame.transform.smoothscale(s, (max(2, W // 5), max(2, H // 5))),
                                     (W, H))
    s.fill((112, 118, 124), special_flags=pygame.BLEND_RGB_MULT)       # strength, ~45%
    out = pygame.Surface((W, H), 0, 32)
    out.fill((255, 255, 255))
    out.blit(s, (0, 0), special_flags=pygame.BLEND_RGB_SUB)
    return out


# Keep dashboard and expanded-map scales warm without retaining unbounded surfaces.
_cache = OrderedDict()


def arena(a, T):
    """(lit, dim): the whole arena painted once at tile size `T`, as two surfaces.

    Both are the same picture; `dim` is darker, for ground and rock the rover has seen
    and walked away from. `render.draw_world` blits a cell's square from whichever fits.
    """
    rocks = frozenset((x, y) for y in range(a.h) for x in range(a.w) if a.at(x, y) == "#")
    key = (a.w, a.h, T, rocks)
    if key not in _cache:
        rnd = random.Random(SEED)
        W, H = a.w * T, a.h * T
        ground = _ground(a.w, a.h, T, rnd)
        if rocks:
            layer, mask = _rock_layer(a.w, a.h, T, rocks, rnd)
            ground.blit(_cast_shadow(W, H, T, mask), (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        else:
            layer = None
        lit = ground
        dim = ground.copy()
        dim.fill(_GROUND_DIM, special_flags=pygame.BLEND_RGB_MULT)
        if layer is not None:
            lit.blit(layer, (0, 0))
            rock_dim = layer.copy()
            rock_dim.fill(_ROCK_DIM + (255,), special_flags=pygame.BLEND_RGBA_MULT)
            dim.blit(rock_dim, (0, 0))
        _cache[key] = (lit, dim)
        if len(_cache) > 3:
            _cache.popitem(last=False)
    _cache.move_to_end(key)
    return _cache[key]



@lru_cache(maxsize=16)
def cloud(size):
    surf=pygame.Surface((size,size),pygame.SRCALPHA)
    for y in range(size):
        for x in range(size):
            nx=(x-size/2)/(size/2)
            ny=(y-size/2)/(size/2)
            r=nx*nx+ny*ny
            alpha=int(22*max(0,1-r)**2)
            surf.set_at((x,y),(202,145,82,alpha))
    return surf


def storm(surf,cells,ox,oy,size,time=None):
    if not cells:
        return
    t=pygame.time.get_ticks()/1000 if time is None else time
    puff=cloud(max(12,size*4))
    old=surf.get_clip()
    # Soft swirling dust travels across the real storm footprint. Ground remains
    # visible; only the real storm cells emit dust.
    for x,y in sorted(cells):
        cx,cy=ox+(x+.5)*size,oy+(y+.5)*size
        for layer in range(3):
            phase=x*2.1+y*1.7+layer*2.4
            dx=math.sin(t*.8+phase)*size*.45
            dy=math.cos(t*.55+phase)*size*.28
            surf.blit(puff,(round(cx+dx-puff.get_width()/2),round(cy+dy-puff.get_height()/2)))
        for j in range(3):
            drift=(t*.55+j*.31+x*.17+y*.23)%1
            xx=cx+(drift-.5)*size
            yy=cy+math.sin(drift*4+j+x)*size*.35
            pygame.draw.aaline(surf,(158,111,67),(xx,yy),(xx+max(2,size*.15),yy-1))
    surf.set_clip(old)
