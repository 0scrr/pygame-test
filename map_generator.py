import random
import math

TILE = 16
MAP_W, MAP_H = 160, 120   # 2560x1920
BORDER_LAND = 6           # bande de terre en bordure

WATER = 0
LAND  = 1

def _rand_grid(w, h):
    return [[random.random() for _ in range(w)] for __ in range(h)]

def _bilinear_sample(grid, x, y):
    h = len(grid); w = len(grid[0])
    x = max(0.0, min(w-1.0, x))
    y = max(0.0, min(h-1.0, y))
    x0 = int(x); y0 = int(y)
    x1 = min(w-1, x0+1); y1 = min(h-1, y0+1)
    sx = x - x0; sy = y - y0
    v00 = grid[y0][x0]; v10 = grid[y0][x1]
    v01 = grid[y1][x0]; v11 = grid[y1][x1]
    a = v00*(1-sx) + v10*sx
    b = v01*(1-sx) + v11*sx
    return a*(1-sy) + b*sy

def _fbm(x, y, octaves=4, scale=0.05, persistence=0.5):
    total = 0.0
    amp = 1.0
    freq = 1.0
    for _ in range(octaves):
        gw = 16; gh = 16
        grid = _rand_grid(gw, gh)
        sx = x * scale * freq
        sy = y * scale * freq
        val = _bilinear_sample(grid, (sx % 1.0)*(gw-1), (sy % 1.0)*(gh-1))
        total += val * amp
        amp *= persistence
        freq *= 2.0
    # normalisation approx
    return total / (2 - 2 * persistence)

def _distance(x0, y0, x1, y1):
    return math.hypot(x1-x0, y1-y0)

def _inside_bounds(x, y):
    return 0 <= x < MAP_W and 0 <= y < MAP_H

def generate_map(seed=None):
    if seed is not None:
        random.seed(seed)

    tiles = [[LAND for _ in range(MAP_W)] for __ in range(MAP_H)]

    # Mer/lac central (métaboules + bruit)
    cx, cy = MAP_W/2, MAP_H/2
    sea_centers = []
    main_r = min(MAP_W, MAP_H) * 0.28
    sea_centers.append((cx, cy, main_r))
    for _ in range(4):
        ang = random.random() * math.tau
        r = main_r * random.uniform(0.6, 0.9)
        dist = main_r * random.uniform(0.4, 0.85)
        sea_centers.append((cx + math.cos(ang)*dist, cy + math.sin(ang)*dist, r))

    for y in range(MAP_H):
        for x in range(MAP_W):
            # terre forcée en bordure
            if (x < BORDER_LAND or y < BORDER_LAND or
                x >= MAP_W-BORDER_LAND or y >= MAP_H-BORDER_LAND):
                continue

            potential = 0.0
            for (sx, sy, sr) in sea_centers:
                d = _distance(x, y, sx, sy)
                val = max(0.0, 1.0 - (d / sr))  # 1 au centre, 0 au bord
                potential += val

            noise = _fbm(x, y, octaves=4, scale=0.08, persistence=0.55)
            potential += (noise - 0.35) * 0.8

            if potential > 0.6:
                tiles[y][x] = WATER

    # Îlots irréguliers
    nb_islands = random.randint(6, 10)
    tries = 0
    created = 0
    while created < nb_islands and tries < 200:
        tries += 1
        ix = random.randint(BORDER_LAND+8, MAP_W-BORDER_LAND-9)
        iy = random.randint(BORDER_LAND+8, MAP_H-BORDER_LAND-9)
        if tiles[iy][ix] != WATER:
            continue
        base_r = random.randint(4, 10)
        for yy in range(iy-base_r-3, iy+base_r+4):
            for xx in range(ix-base_r-3, ix+base_r+4):
                if not _inside_bounds(xx, yy):
                    continue
                d = _distance(ix, iy, xx, yy)
                edge = _fbm(xx*1.3, yy*1.3, octaves=3, scale=0.1, persistence=0.55)
                r = base_r + (edge-0.5)*4.5
                if d <= r and tiles[yy][xx] == WATER:
                    tiles[yy][xx] = LAND
        created += 1

    return tiles

def find_shore_ports(tiles, want=4):
    """Trouve des tuiles 'port' (terre adjacente à l'eau), espacées angulairement."""
    candidates = []
    cx, cy = MAP_W/2, MAP_H/2
    for y in range(1, MAP_H-1):
        for x in range(1, MAP_W-1):
            if tiles[y][x] != LAND:
                continue
            neigh = [(x+1,y),(x-1,y),(x,y+1),(x,y-1)]
            if any(tiles[ny][nx] == WATER for nx,ny in neigh):
                ang = math.atan2(y-cy, x-cx)
                candidates.append(((x,y), ang))
    if not candidates:
        return []

    # trie par angle puis sélection espacée
    candidates.sort(key=lambda it: it[1])
    ports = []
    min_sep = (2*math.pi) / max(1, want) * 0.6  # espacement angulaire mini
    for (pos, ang) in candidates:
        if all(abs((ang - ua + math.pi) % (2*math.pi) - math.pi) > min_sep for ua in (a for _,a in ports)):
            ports.append((pos, ang))
            if len(ports) >= want:
                break
    # retourne juste les positions
    return [p for p,_ in ports] if ports else [pos for pos,_ in candidates[:want]]
