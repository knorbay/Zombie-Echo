import pygame
import math
import random
import sys
import os
import numpy as np

BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
ASSET_DIR = os.path.join(BASE_DIR, "assets")

pygame.mixer.pre_init(
    44100,
    -16,
    2,
    512
)
pygame.init()

try:
    pygame.mixer.music.load(os.path.join(ASSET_DIR, "game_music6.mp3"))
    pygame.mixer.music.set_volume(0.34)
    pygame.mixer.music.play(-1)
except (pygame.error, OSError):
    pass

WIDTH, HEIGHT = 1280, 720
WORLD_W, WORLD_H = 3000, 3000
FPS = 120
BOSS_INTERVAL = 5

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Zombie Echo: Those Left in the Dark")
clock = pygame.time.Clock()

C_BG = (20, 22, 28)
C_WHITE = (240, 240, 240)
C_BLACK = (0, 0, 0)
C_RED = (220, 40, 40)
C_DARK_RED = (120, 20, 20)
C_GREEN = (40, 200, 70)
C_BLUE = (50, 150, 250)
C_YELLOW = (255, 220, 50)
C_ORANGE = (255, 120, 30)
C_PURPLE = (150, 50, 200)
C_ACID = (100, 255, 50)
C_CYAN = (80, 220, 255)
C_WALL = (34, 40, 51)
C_WALL_TOP = (53, 63, 82)

try:
    FONT_SM = pygame.font.SysFont("trebuchetms", 18, True)
    FONT_MD = pygame.font.SysFont("trebuchetms", 28, True)
    FONT_LG = pygame.font.SysFont("trebuchetms", 64, True)
except:
    FONT_SM = pygame.font.Font(None, 24)
    FONT_MD = pygame.font.Font(None, 36)
    FONT_LG = pygame.font.Font(None, 72)


class SoundManager:
    def __init__(self):
        self.sounds = {}
        self.path = ASSET_DIR

        files = {
            "pistol_fire": "pistolfire.mp3",
            "pistol_reload": "pistolreload.mp3",
            "rifle_fire": "riflefire.mp3",
            "rifle_reload": "riflereload.mp3",
            "shotgun_fire": "shotgunfire.mp3",
            "shotgun_reload": "shotgunreload.mp3",
            "footsteps": "footsteps.mp3",
            "explosion": "explosion.mp3",
            "zombie1": "zombiesound1.mp3",
            "zombie2": "zombiesound2.mp3",
            "zombie3": "zombiesound3.mp3",
            "pickup": os.path.join("sfx", "kenney", "pickup.ogg"),
            "select": os.path.join("sfx", "kenney", "select.ogg"),
            "error": os.path.join("sfx", "kenney", "error.ogg"),
            "empty": os.path.join("sfx", "kenney", "empty.ogg"),
            "melee": os.path.join("sfx", "kenney", "melee.ogg"),
            "loot": os.path.join("sfx", "kenney", "loot.ogg")
        }

        for name, filename in files.items():
            path = os.path.join(self.path, filename)
            if os.path.exists(path):
                self.sounds[name] = pygame.mixer.Sound(path)

    def play(self, name, volume=1.0, maxtime=0):
        sound = self.sounds.get(name)
        if sound:
            sound.set_volume(volume)
            if maxtime > 0:
                sound.play(maxtime=maxtime)
            else:
                sound.play()


def build_vignette(w, h, strength=140):
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 255))
    cx, cy = w / 2, h / 2
    maxdist = math.hypot(cx, cy)
    yy, xx = np.mgrid[0:h, 0:w]
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / maxdist
    t = np.clip((dist - 0.55) / 0.45, 0, 1) ** 1.6
    alpha = (t * strength).astype(np.uint8)
    arr = pygame.surfarray.pixels_alpha(surf)
    arr[:, :] = alpha.T
    del arr
    return surf


VIGNETTE = build_vignette(WIDTH, HEIGHT, 65)


def build_dust_sprite(size):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(surf, (90, 95, 100, 90), (size // 2, size // 2), size // 2)
    return surf


DUST_SPRITES = {s: build_dust_sprite(s) for s in (4, 6, 8)}


def draw_shadow(surf, pos, radius, alpha=90):
    w = int(radius * 2)
    h = max(2, int(radius * 0.85))
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (0, 0, 0, alpha), s.get_rect())
    surf.blit(s, (pos.x - radius, pos.y + radius * 0.35))


class Camera:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.shake_amount = 0

    def update(self, target_pos, dt):
        target_x = target_pos.x - WIDTH / 2
        target_y = target_pos.y - HEIGHT / 2
        self.x += (target_x - self.x) * 5 * dt
        self.y += (target_y - self.y) * 5 * dt
        self.x = max(0, min(self.x, WORLD_W - WIDTH))
        self.y = max(0, min(self.y, WORLD_H - HEIGHT))
        if self.shake_amount > 0:
            self.shake_amount -= 100 * dt
            if self.shake_amount < 0: self.shake_amount = 0

    def get_offset(self):
        sx = random.uniform(-self.shake_amount, self.shake_amount) if self.shake_amount > 0 else 0
        sy = random.uniform(-self.shake_amount, self.shake_amount) if self.shake_amount > 0 else 0
        return pygame.Vector2(self.x + sx, self.y + sy)

    def shake(self, amount):
        self.shake_amount = min(amount, 30)


class Particle:
    def __init__(self, pos, vel, color, life, size=3, shrink=True):
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(vel)
        self.color = color
        self.life = life
        self.max_life = life
        self.size = size
        self.shrink = shrink

    def update(self, dt):
        self.pos += self.vel * dt
        self.vel *= 0.95
        self.life -= dt
        return self.life > 0

    def draw(self, surf, offset):
        if self.shrink:
            current_size = max(0.5, self.size * (self.life / self.max_life))
        else:
            current_size = self.size
        pygame.draw.circle(surf, self.color, self.pos - offset, current_size)


class DamageNumber:
    def __init__(self, pos, value, color=C_WHITE, big=False):
        self.pos = pygame.Vector2(pos) + pygame.Vector2(random.uniform(-8, 8), -10)
        self.vel = pygame.Vector2(random.uniform(-15, 15), -75)
        self.life = 0.7
        self.max_life = 0.7
        self.value = value
        self.color = color
        self.big = big

    def update(self, dt):
        self.pos += self.vel * dt
        self.vel.y += 60 * dt
        self.life -= dt
        return self.life > 0

    def draw(self, surf, offset):
        alpha = max(0, min(255, int(255 * (self.life / self.max_life))))
        font = FONT_MD if self.big else FONT_SM
        txt = font.render(str(int(self.value)), True, self.color)
        txt.set_alpha(alpha)
        draw_pos = self.pos - offset
        surf.blit(txt, (draw_pos.x - txt.get_width() / 2, draw_pos.y))


class ComboPopup:
    def __init__(self, pos, mult):
        self.pos = pygame.Vector2(pos) + pygame.Vector2(0, -35)
        self.life = 0.9
        self.max_life = 0.9
        self.mult = mult

    def update(self, dt):
        self.pos.y -= 45 * dt
        self.life -= dt
        return self.life > 0

    def draw(self, surf, offset):
        alpha = max(0, min(255, int(255 * (self.life / self.max_life))))
        txt = FONT_MD.render(f"x{self.mult} COMBO", True, C_YELLOW)
        txt.set_alpha(alpha)
        draw_pos = self.pos - offset
        surf.blit(txt, (draw_pos.x - txt.get_width() / 2, draw_pos.y))


class MuzzleFlash:
    def __init__(self, pos, dir_vec, color=None):
        self.pos = pygame.Vector2(pos)
        self.dir = pygame.Vector2(dir_vec)
        self.life = 0.05
        self.color = color if color else C_YELLOW

    def update(self, dt):
        self.life -= dt
        return self.life > 0

    def draw(self, surf, offset):
        p1 = self.pos + self.dir * 30 - offset
        p2 = self.pos + self.dir.rotate(20) * 10 - offset
        p3 = self.pos + self.dir.rotate(-20) * 10 - offset
        pygame.draw.polygon(surf, self.color, [p1, p2, p3])


class BloodStain:
    def __init__(self, pos):
        self.pos = pygame.Vector2(pos)
        self.radius = random.uniform(6, 20)
        self.color = (random.randint(50, 90), 8, 8)

    def draw(self, surf, offset):
        pygame.draw.circle(surf, self.color, self.pos - offset, self.radius)


class Wall:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = C_WALL
        self.top_color = C_WALL_TOP

    def draw(self, surf, offset):
        draw_rect = pygame.Rect(self.rect.x - offset.x, self.rect.y - offset.y, self.rect.width, self.rect.height)
        shadow_rect = pygame.Rect(draw_rect.x + 8, draw_rect.y + 8, draw_rect.width, draw_rect.height)
        pygame.draw.rect(surf, (10, 10, 14), shadow_rect, border_radius=4)
        pygame.draw.rect(surf, self.color, draw_rect, border_radius=4)
        top_rect = pygame.Rect(draw_rect.x, draw_rect.y, draw_rect.width, 12)
        pygame.draw.rect(surf, self.top_color, top_rect, border_radius=4)
        inner = draw_rect.inflate(-8, -8)
        pygame.draw.rect(surf, (36, 43, 54), inner, 1, border_radius=2)
        pygame.draw.rect(surf, (13, 16, 22), draw_rect, 2, border_radius=4)


class LightSource:
    def __init__(self, pos, radius=320):
        self.pos = pygame.Vector2(pos)
        self.radius = radius

    def draw(self, surf, offset):
        draw_pos = self.pos - offset
        halo = pygame.Surface((54, 54), pygame.SRCALPHA)
        pygame.draw.circle(halo, (90, 160, 255, 22), (27, 27), 26)
        surf.blit(halo, draw_pos - pygame.Vector2(27, 27))
        pygame.draw.circle(surf, (255, 240, 180), draw_pos, 6)
        pygame.draw.circle(surf, (255, 255, 220), draw_pos, 3)


class ExplosiveBarrel:
    def __init__(self, pos):
        self.pos = pygame.Vector2(pos)
        self.radius = 16
        self.hp = 25
        self.alive = True

    def hit(self, dmg):
        self.hp -= dmg
        if self.hp <= 0:
            self.alive = False
            return True
        return False

    def draw(self, surf, offset):
        draw_pos = self.pos - offset
        draw_shadow(surf, draw_pos, self.radius, 85)
        pygame.draw.circle(surf, (75, 18, 18), draw_pos, self.radius + 2)
        pygame.draw.circle(surf, C_RED, draw_pos, self.radius)
        pygame.draw.circle(surf, (145, 28, 24), draw_pos, self.radius - 6)
        pygame.draw.rect(surf, C_ORANGE, (draw_pos.x - 9, draw_pos.y - 2, 18, 4), border_radius=2)


WEAPON_STATS = {
    "Pistol": {"dmg": 30, "mag": 15, "reload": 1.2, "delay": 0.20, "spread": 3, "pellets": 1, "auto": False, "pierce": False, "color": (255, 220, 50)},
    "Revolver": {"dmg": 72, "mag": 6, "reload": 1.6, "delay": 0.42, "spread": 2, "pellets": 1, "auto": False, "pierce": True, "color": (255, 190, 70)},
    "SMG": {"dmg": 14, "mag": 42, "reload": 1.7, "delay": 0.065, "spread": 9, "pellets": 1, "auto": True, "pierce": False, "color": (255, 235, 150)},
    "Rifle": {"dmg": 22, "mag": 35, "reload": 2.0, "delay": 0.10, "spread": 5, "pellets": 1, "auto": True, "pierce": False, "color": (255, 240, 190)},
    "Shotgun": {"dmg": 22, "mag": 8, "reload": 2.5, "delay": 0.70, "spread": 15, "pellets": 8, "auto": False, "pierce": False, "color": (255, 150, 60)},
    "LMG": {"dmg": 25, "mag": 75, "reload": 3.4, "delay": 0.085, "spread": 7, "pellets": 1, "auto": True, "pierce": False, "color": (255, 205, 105)},
    "Launcher": {"dmg": 240, "mag": 1, "reload": 2.6, "delay": 0.95, "spread": 1, "pellets": 1, "auto": False, "pierce": False, "color": C_ORANGE, "speed": 720, "explosive": 205},
}

class Weapon:
    def __init__(self, name):
        self.name = name
        stats = WEAPON_STATS[name]
        self.damage = stats["dmg"]
        self.mag_size = stats["mag"]
        self.ammo = self.mag_size
        self.reserve = self.mag_size * 2
        self.reload_time = stats["reload"]
        self.fire_delay = stats["delay"]
        self.spread = stats["spread"]
        self.pellets = stats["pellets"]
        self.auto = stats["auto"]
        self.pierce = stats["pierce"]
        self.color = stats["color"]
        self.projectile_speed = stats.get("speed", 1850)
        self.explosive_radius = stats.get("explosive", 0)
        self.fire_timer = 0
        self.reload_timer = 0
        self.is_reloading = False
        self.just_started_reload = False

    def update(self, dt):
        if self.fire_timer > 0: self.fire_timer -= dt
        if self.is_reloading:
            self.reload_timer -= dt
            if self.reload_timer <= 0:
                needed = self.mag_size - self.ammo
                taken = min(needed, self.reserve)
                self.ammo += taken
                self.reserve -= taken
                self.is_reloading = False
        elif self.ammo <= 0 and self.reserve > 0:
            self.is_reloading = True
            self.reload_timer = self.reload_time
            self.just_started_reload = True

    def shoot(self, fire_rate_mult=1.0):
        if self.is_reloading or self.fire_timer > 0: return False
        if self.ammo <= 0: return False
        self.ammo -= 1
        self.fire_timer = self.fire_delay * fire_rate_mult
        return True

    def reload(self):
        if self.ammo < self.mag_size and self.reserve > 0 and not self.is_reloading:
            self.is_reloading = True
            self.reload_timer = self.reload_time
            return True
        return False


class Bullet:
    def __init__(self, pos, dir_vec, damage, pierce, weapon_name, color=None, speed=1850, explosive_radius=0):
        self.pos = pygame.Vector2(pos)
        self.start_pos = pygame.Vector2(pos)
        self.prev_pos = pygame.Vector2(pos)
        self.dir = pygame.Vector2(dir_vec)
        self.damage = damage
        self.pierce = pierce
        self.weapon_name = weapon_name
        self.color = color if color else C_YELLOW
        self.speed = speed
        self.explosive_radius = explosive_radius
        self.alive = True
        self.hit_targets = []
        self.trail = []

    def get_actual_damage(self):
        dist = self.pos.distance_to(self.start_pos)
        if self.weapon_name == "Shotgun":
            if dist > 350:
                return int(max(1, self.damage * 0.2))
            elif dist > 100:
                factor = 1.0 - ((dist - 100) / 250) * 0.8
                return int(max(1, self.damage * factor))
        return int(self.damage)

    def update(self, dt):
        self.trail.append(pygame.Vector2(self.pos))
        if len(self.trail) > 3: self.trail.pop(0)
        self.prev_pos = pygame.Vector2(self.pos)
        self.pos += self.dir * self.speed * dt
        if not (0 <= self.pos.x <= WORLD_W and 0 <= self.pos.y <= WORLD_H):
            self.alive = False

    def draw(self, surf, offset):
        if len(self.trail) > 1:
            points = [p - offset for p in self.trail]
            pygame.draw.lines(surf, self.color, False, points, 1)
        pygame.draw.circle(surf, C_WHITE, self.pos - offset, 2)


class AcidProjectile:
    def __init__(self, pos, target_pos):
        self.pos = pygame.Vector2(pos)
        self.start_pos = pygame.Vector2(pos)
        self.target = pygame.Vector2(target_pos)
        self.dir = (self.target - self.pos).normalize()
        self.speed = 300
        self.alive = True

    def update(self, dt):
        self.pos += self.dir * self.speed * dt
        if self.pos.distance_to(self.start_pos) >= self.target.distance_to(self.start_pos):
            self.alive = False

    def draw(self, surf, offset):
        pygame.draw.circle(surf, C_ACID, self.pos - offset, 6)


class AcidPool:
    def __init__(self, pos):
        self.pos = pygame.Vector2(pos)
        self.radius = 30
        self.life = 5.0
        self.damage = 15

    def update(self, dt):
        self.life -= dt
        return self.life > 0

    def draw(self, surf, offset):
        s = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        alpha = int(min(1.0, self.life) * 150)
        pygame.draw.circle(s, (*C_ACID[:3], alpha), (self.radius, self.radius), self.radius)
        surf.blit(s, self.pos - offset - pygame.Vector2(self.radius, self.radius))


class Item:
    def __init__(self, pos, type_name):
        self.pos = pygame.Vector2(pos)
        self.type = type_name
        self.float_t = random.uniform(0, math.pi * 2)
        self.radius = 12

    def update(self, dt):
        self.float_t += dt * 3

    def draw(self, surf, offset):
        y_off = math.sin(self.float_t) * 5
        draw_pos = self.pos - offset + pygame.Vector2(0, y_off)
        draw_shadow(surf, self.pos - offset, 12, 70)
        if self.type == "Medkit":
            color = C_GREEN
        elif self.type == "Ammo":
            color = C_YELLOW
        elif self.type == "Damage Boost":
            color = C_RED
        elif self.type == "Overdrive":
            color = C_PURPLE
        else:
            color = (185, 190, 200)
        pygame.draw.rect(surf, color, (draw_pos.x - 11, draw_pos.y - 11, 22, 22), border_radius=5)
        pygame.draw.rect(surf, C_WHITE, (draw_pos.x - 11, draw_pos.y - 11, 22, 22), 1, border_radius=5)
        icon = {"Damage Boost": "D", "Overdrive": "O"}.get(self.type, self.type[0])
        txt = FONT_SM.render(icon, True, C_BLACK)
        surf.blit(txt, txt.get_rect(center=draw_pos))


class Player:
    def __init__(self, sound_manager):
        self.sound = sound_manager
        self.pos = pygame.Vector2(WORLD_W / 2, WORLD_H / 2)
        self.radius = 18
        self.base_speed = 180
        self.speed = 180
        self.max_hp = 100
        self.hp = self.max_hp
        self.weapons = [Weapon("Pistol")]
        self.current_weapon_idx = 0
        self.i_frames = 0
        self.slow_timer = 0
        self.score = 0
        self.kills = 0
        self.dash_timer = 0
        self.dash_cooldown = 0
        self.dash_dir = pygame.Vector2(0, 0)
        self.dash_hit_targets = set()
        self.step_timer = 0
        self.combo = 0
        self.combo_timer = 0
        self.dmg_mult = 1.0
        self.reload_mult = 1.0
        self.dash_cd_mult = 1.0
        self.melee_damage = 32
        self.melee_cooldown = 0
        self.melee_cooldown_mult = 1.0
        self.medkits = 1
        self.damage_boost_timer = 0
        self.overdrive_timer = 0
        self.velocity = pygame.Vector2()

    @property
    def weapon(self):
        return self.weapons[self.current_weapon_idx]

    def play_reload_sound(self, name):
        if name in ("Pistol", "Revolver"):
            self.sound.play("pistol_reload", 0.6)
        elif name in ("Rifle", "SMG", "LMG"):
            self.sound.play("rifle_reload", 0.6)
        elif name in ("Shotgun", "Launcher"):
            self.sound.play("shotgun_reload", 0.7)

    def update(self, dt, walls, sound_manager):
        for w in self.weapons:
            w.update(dt)
            if w.just_started_reload:
                if w is self.weapon:
                    self.play_reload_sound(w.name)
                w.just_started_reload = False
        if self.i_frames > 0: self.i_frames -= dt
        if self.slow_timer > 0: self.slow_timer -= dt
        if self.dash_cooldown > 0: self.dash_cooldown -= dt
        if self.melee_cooldown > 0: self.melee_cooldown -= dt
        if self.damage_boost_timer > 0: self.damage_boost_timer -= dt
        if self.overdrive_timer > 0: self.overdrive_timer -= dt

        keys = pygame.key.get_pressed()
        move = pygame.Vector2(0, 0)
        previous_pos = pygame.Vector2(self.pos)

        current_base = self.base_speed * 0.70 if self.slow_timer > 0 else self.base_speed

        if self.dash_timer > 0:
            self.dash_timer -= dt
            move = self.dash_dir
            self.speed = current_base * 3
            self.i_frames = 0.1
        else:
            self.speed = current_base
            if keys[pygame.K_w]: move.y -= 1
            if keys[pygame.K_s]: move.y += 1
            if keys[pygame.K_a]: move.x -= 1
            if keys[pygame.K_d]: move.x += 1

            if keys[pygame.K_SPACE] and self.dash_cooldown <= 0 and move.length_squared() > 0:
                self.dash_timer = 0.2
                self.dash_cooldown = 1.5 * self.dash_cd_mult
                self.dash_dir = move
                self.dash_hit_targets.clear()
                self.i_frames = 0.3

        if move.length_squared() > 0:
            move.normalize_ip()
            self.step_timer -= dt
            if self.step_timer <= 0:
                self.sound.play("footsteps", 0.4)
                self.step_timer = 0.45
            self.pos.x += move.x * self.speed * dt
            self.resolve_collisions(walls, is_x=True)
            self.pos.y += move.y * self.speed * dt
            self.resolve_collisions(walls, is_x=False)

        self.pos.x = max(self.radius, min(WORLD_W - self.radius, self.pos.x))
        self.pos.y = max(self.radius, min(WORLD_H - self.radius, self.pos.y))
        measured_velocity = (self.pos - previous_pos) / max(dt, 0.001)
        self.velocity = self.velocity.lerp(measured_velocity, min(1.0, dt * 12))

    def resolve_collisions(self, walls, is_x):
        player_rect = pygame.Rect(self.pos.x - self.radius, self.pos.y - self.radius, self.radius * 2, self.radius * 2)
        for wall in walls:
            if player_rect.colliderect(wall.rect):
                if is_x:
                    if self.pos.x > wall.rect.centerx:
                        self.pos.x = wall.rect.right + self.radius
                    else:
                        self.pos.x = wall.rect.left - self.radius
                        player_rect.x = int(self.pos.x - self.radius)
                else:
                    if self.pos.y > wall.rect.centery:
                        self.pos.y = wall.rect.bottom + self.radius
                    else:
                        self.pos.y = wall.rect.top - self.radius
                    player_rect.y = int(self.pos.y - self.radius)

    def switch_weapon(self, index):
        if 0 <= index < len(self.weapons) and index != self.current_weapon_idx:
            self.current_weapon_idx = index
            self.sound.play("select", 0.25)

    def take_damage(self, amount):
        if self.i_frames <= 0:
            self.hp -= amount
            self.i_frames = 0.5
            self.slow_timer = 0.35
            return True
        return False

    def draw(self, surf, offset, mouse_pos):
        draw_pos = self.pos - offset
        draw_shadow(surf, draw_pos, self.radius, 100)

        aim_dir = (mouse_pos - draw_pos)
        if aim_dir.length_squared() > 0:
            aim_dir.normalize_ip()
        else:
            aim_dir = pygame.Vector2(1, 0)

        if self.dash_timer > 0:
            pygame.draw.circle(surf, (90, 210, 255), draw_pos, self.radius + 8, 3)

        body_color = C_WHITE if self.i_frames > 0 and int(self.i_frames * 20) % 2 == 0 else C_BLUE
        pygame.draw.circle(surf, (15, 45, 90), draw_pos, self.radius + 2)
        pygame.draw.circle(surf, body_color, draw_pos, self.radius)
        pygame.draw.circle(surf, (25, 85, 185), draw_pos, self.radius - 7)

        gun_length = 31 if self.weapon.name in ("Shotgun", "Rifle", "LMG", "Launcher") else 25
        gun_end = draw_pos + aim_dir * gun_length
        pygame.draw.line(surf, (15, 18, 24), draw_pos + aim_dir * 5, gun_end, 7)
        pygame.draw.line(surf, self.weapon.color, draw_pos + aim_dir * 8, gun_end, 3)
        pygame.draw.circle(surf, C_WHITE, draw_pos + aim_dir * 7, 3)

        if self.dash_cooldown > 0:
            pygame.draw.arc(surf, C_WHITE, (draw_pos.x - self.radius - 5, draw_pos.y - self.radius - 5, (self.radius + 5) * 2, (self.radius + 5) * 2), 0, (math.pi * 2) * (1 - self.dash_cooldown / 1.5), 2)


class Zombie:
    def __init__(self, z_type, player_pos, wave=1):
        angle = random.uniform(0, math.pi * 2)
        dist = random.uniform(800, 1200)
        self.pos = player_pos + pygame.Vector2(math.cos(angle), math.sin(angle)) * dist
        self.pos.x = max(50, min(WORLD_W - 50, self.pos.x))
        self.pos.y = max(50, min(WORLD_H - 50, self.pos.y))

        self.type = z_type
        self.buff_timer = 0
        self.action_timer = 0
        self.hit_flash = 0
        self.alpha = 255
        self.lit = False
        self.sound_timer = random.uniform(2.0, 5.0)
        self.facing = pygame.Vector2(1, 0)
        self.orbit_sign = random.choice((-1, 1))
        self.nav_waypoint = None

        self.wobble_speed = random.uniform(1.5, 4.0)
        self.wobble_amount = random.uniform(15, 40)
        self.wobble_offset = random.uniform(0, 100)

        if z_type == "Normal":
            self.hp = 60; self.max_hp = 60; self.speed = 120; self.damage = 15; self.radius = 20; self.color = C_GREEN
        elif z_type == "Runner":
            self.hp = 30; self.max_hp = 30; self.speed = 180; self.damage = 10; self.radius = 16; self.color = C_DARK_RED
        elif z_type == "Tank":
            self.hp = 400; self.max_hp = 400; self.speed = 60; self.damage = 55; self.radius = 35; self.color = (80, 80, 80); self.wobble_amount = 5
        elif z_type == "Screamer":
            self.hp = 50; self.max_hp = 50; self.speed = 110; self.damage = 10; self.radius = 18; self.color = C_PURPLE
        elif z_type == "Stalker":
            self.hp = 40; self.max_hp = 40; self.speed = 135; self.damage = 25; self.radius = 18; self.color = (35, 35, 35)
        elif z_type == "Spitter":
            self.hp = 50; self.max_hp = 50; self.speed = 105; self.damage = 10; self.radius = 20; self.color = C_ACID
        elif z_type == "Exploder":
            self.hp = 45; self.max_hp = 45; self.speed = 120; self.damage = 0; self.radius = 19; self.color = C_ORANGE; self.fuse = None
        elif z_type == "Boss":
            stage = max(1, wave // BOSS_INTERVAL)
            self.boss_variant = ("Juggernaut", "Broodmother", "Reaper")[(stage - 1) % 3]
            if self.boss_variant == "Juggernaut":
                self.hp = 2500; self.speed = 90; self.damage = 50; self.radius = 60; self.color = C_RED
            elif self.boss_variant == "Broodmother":
                self.hp = 2200; self.speed = 78; self.damage = 35; self.radius = 58; self.color = C_PURPLE
            else:
                self.hp = 1900; self.speed = 125; self.damage = 38; self.radius = 52; self.color = C_ORANGE
            self.max_hp = self.hp
            self.wobble_amount = 0; self.boss_state = "chase"; self.state_timer = 0
            self.charge_dir = pygame.Vector2(0, 0); self.charge_cooldown = random.uniform(3, 5); self.slam_cooldown = random.uniform(4, 6)
            self.summon_cooldown = 4.5
            self.volley_cooldown = 2.8
            self.enraged = False

        if z_type == "Boss":
            stage = max(1, wave // BOSS_INTERVAL)
            hp_mult = 1 + (stage - 1) * 0.5
            speed_mult = 1 + (stage - 1) * 0.04
        else:
            hp_mult = 1 + (wave - 1) * 0.06
            speed_mult = 1 + (wave - 1) * 0.01

        self.hp = int(self.hp * hp_mult)
        self.max_hp = self.hp
        self.speed *= speed_mult

    def navigation_direction(self, target, walls):
        target = pygame.Vector2(target)
        direct = target - self.pos
        if direct.length_squared() == 0:
            return pygame.Vector2()

        if self.nav_waypoint is not None:
            waypoint_delta = self.nav_waypoint - self.pos
            if waypoint_delta.length() > 6:
                return waypoint_delta.normalize()
            self.nav_waypoint = None

        start = (int(self.pos.x), int(self.pos.y))
        end = (int(target.x), int(target.y))
        blockers = []
        padding = int(self.radius + 10)
        for wall in walls:
            expanded = wall.rect.inflate(padding * 2, padding * 2)
            if expanded.clipline(start, end):
                blockers.append((self.pos.distance_squared_to(expanded.center), expanded))

        if not blockers:
            self.nav_waypoint = None
            return direct.normalize()

        blocker = min(blockers, key=lambda entry: entry[0])[1]
        clearance = 18
        candidates = [
            pygame.Vector2(blocker.left - clearance, blocker.top - clearance),
            pygame.Vector2(blocker.right + clearance, blocker.top - clearance),
            pygame.Vector2(blocker.left - clearance, blocker.bottom + clearance),
            pygame.Vector2(blocker.right + clearance, blocker.bottom + clearance),
        ]
        valid = []
        for candidate in candidates:
            if not (self.radius < candidate.x < WORLD_W - self.radius and self.radius < candidate.y < WORLD_H - self.radius):
                continue
            if any(wall.rect.inflate(padding, padding).collidepoint(candidate) for wall in walls):
                continue
            candidate_end = (int(candidate.x), int(candidate.y))
            if blocker.clipline(start, candidate_end):
                continue
            if self.pos.distance_to(candidate) < 7:
                continue
            route = self.pos.distance_to(candidate) + candidate.distance_to(target)
            turn = abs(direct.angle_to(candidate - self.pos)) if candidate != self.pos else 180
            valid.append((route + turn * 1.5, candidate))

        waypoint = min(valid, key=lambda entry: entry[0])[1] if valid else target
        self.nav_waypoint = pygame.Vector2(waypoint) if waypoint != target else None
        direction = waypoint - self.pos
        return direction.normalize() if direction.length_squared() else direct.normalize()

    def separation_direction(self, zombies):
        force = pygame.Vector2()
        for other in zombies:
            if other is self:
                continue
            delta = self.pos - other.pos
            distance = delta.length()
            comfort = self.radius + other.radius + 8
            if 0 < distance < comfort:
                pressure = 1.0 - distance / comfort
                force += delta.normalize() * pressure
                force += self.facing.rotate(90 * self.orbit_sign) * pressure * 0.45
        return force

    def has_line_of_sight(self, target, walls):
        start = (int(self.pos.x), int(self.pos.y))
        end = (int(target.x), int(target.y))
        return not any(wall.rect.clipline(start, end) for wall in walls)

    def update(self, dt, player, walls, sound_manager, zombies=None):
        if self.buff_timer > 0: self.buff_timer -= dt
        if self.hit_flash > 0: self.hit_flash -= dt

        dist = self.pos.distance_to(player.pos)

        if dist < 300:
            self.sound_timer -= dt
            if self.sound_timer <= 0:
                sound_manager.play(random.choice(["zombie1", "zombie2", "zombie3"]), 0.12)
                self.sound_timer = random.uniform(4.0, 8.0)

        ideal_dir = pygame.Vector2(1, 0)
        dir_vec = pygame.Vector2()
        if dist > 0:
            ideal_dir = (player.pos - self.pos).normalize()
            self.facing = ideal_dir
            prediction_time = min(0.42, dist / 900)
            target = player.pos + player.velocity * prediction_time
            if self.type in ("Runner", "Stalker"):
                flank = ideal_dir.rotate(90) * self.orbit_sign
                target += flank * (95 if self.type == "Runner" else 145)
            dir_vec = self.navigation_direction(target, walls)

        if zombies and self.type != "Boss":
            separation = self.separation_direction(zombies)
            if separation.length_squared() > 0:
                dir_vec += separation * (0.95 if self.type == "Runner" else 0.65)
                if dir_vec.length_squared() > 0:
                    dir_vec.normalize_ip()

        current_speed = self.speed * (1.5 if self.buff_timer > 0 else 1.0)
        move = True

        if self.type == "Screamer":
            if dist < 400 and self.action_timer <= 0 and self.has_line_of_sight(player.pos, walls):
                self.action_timer = 5.0
                move = False
                return "scream"
            if self.action_timer > 3.5: move = False
            elif dist < 260:
                dir_vec = -ideal_dir
            elif 300 <= dist <= 390:
                dir_vec = ideal_dir.rotate(90 * self.orbit_sign)
            self.action_timer -= dt

        elif self.type == "Spitter":
            if dist < 450 and self.action_timer <= 0 and self.has_line_of_sight(player.pos, walls):
                self.action_timer = 3.0
                move = False
                return "spit"
            if self.action_timer > 2.5: move = False
            elif dist < 245:
                dir_vec = (-ideal_dir + ideal_dir.rotate(90 * self.orbit_sign) * 0.35).normalize()
            elif dist < 390:
                dir_vec = ideal_dir.rotate(90 * self.orbit_sign)
            self.action_timer -= dt

        elif self.type == "Stalker":
            if dist > 300:
                self.alpha = 10
            elif dist < 100:
                self.alpha = 255
            else:
                self.alpha = int(255 - ((dist - 100) / 200) * 245)
            if 120 < dist < 260:
                dir_vec = (ideal_dir + ideal_dir.rotate(90 * self.orbit_sign) * 0.55).normalize()

        elif self.type == "Exploder":
            if self.fuse is not None:
                self.fuse -= dt
                move = False
                if self.fuse <= 0:
                    return "explode"
            elif dist < 70:
                self.fuse = 0.55
                move = False

        elif self.type == "Boss":
            self.enraged = self.hp < self.max_hp * 0.4
            if self.enraged:
                current_speed *= 1.3

            if self.boss_variant == "Broodmother":
                self.summon_cooldown -= dt
                self.volley_cooldown -= dt
                if self.summon_cooldown <= 0:
                    self.summon_cooldown = 5.0 if self.enraged else 7.0
                    return "summon"
                if self.volley_cooldown <= 0 and dist < 620 and self.has_line_of_sight(player.pos, walls):
                    self.volley_cooldown = 1.8 if self.enraged else 3.0
                    return "boss_spit"
                if dist < 180:
                    dir_vec = -ideal_dir
                elif dist < 360:
                    dir_vec = ideal_dir.rotate(90 * self.orbit_sign)
            else:
                self.charge_cooldown -= dt
                self.slam_cooldown -= dt
                if self.boss_state == "chase":
                    if self.charge_cooldown <= 0 and dist > 180:
                        self.boss_state = "charge_windup"
                        self.state_timer = 0.38 if self.boss_variant == "Reaper" else 0.6
                        move = False
                    elif self.slam_cooldown <= 0 and dist < 165:
                        self.boss_state = "slam_windup"
                        self.state_timer = 0.32 if self.boss_variant == "Reaper" else 0.5
                        move = False
                elif self.boss_state == "charge_windup":
                    move = False
                    self.state_timer -= dt
                    if self.state_timer <= 0:
                        self.boss_state = "charging"
                        self.state_timer = 1.05 if self.boss_variant == "Reaper" else 0.9
                        self.charge_dir = ideal_dir
                elif self.boss_state == "charging":
                    self.state_timer -= dt
                    dir_vec = self.charge_dir
                    speed_factor = 3.8 if self.boss_variant == "Reaper" else 3.2
                    current_speed = self.speed * speed_factor * (1.3 if self.enraged else 1.0)
                    if self.state_timer <= 0:
                        self.boss_state = "chase"
                        self.charge_cooldown = random.uniform(2.2, 3.5) if self.enraged else random.uniform(3.5, 6)
                elif self.boss_state == "slam_windup":
                    move = False
                    self.state_timer -= dt
                    if self.state_timer <= 0:
                        self.boss_state = "slam"
                        self.state_timer = 0.15
                elif self.boss_state == "slam":
                    move = False
                    self.state_timer -= dt
                    if self.state_timer <= 0:
                        self.boss_state = "chase"
                        self.slam_cooldown = random.uniform(2.5, 4) if self.enraged else random.uniform(4, 7)
                        return "reaper_burst" if self.boss_variant == "Reaper" else "slam"

        if move:
            self.pos.x += dir_vec.x * current_speed * dt
            self.resolve_collisions(walls, is_x=True)
            self.pos.y += dir_vec.y * current_speed * dt
            self.resolve_collisions(walls, is_x=False)

        self.pos.x = max(self.radius, min(WORLD_W - self.radius, self.pos.x))
        self.pos.y = max(self.radius, min(WORLD_H - self.radius, self.pos.y))
        return None

    def resolve_collisions(self, walls, is_x):
        z_rect = pygame.Rect(self.pos.x - self.radius, self.pos.y - self.radius, self.radius * 2, self.radius * 2)
        for wall in walls:
            if z_rect.colliderect(wall.rect):
                if is_x:
                    if self.pos.x > wall.rect.centerx:
                        self.pos.x = wall.rect.right + self.radius
                    else:
                        self.pos.x = wall.rect.left - self.radius
                    z_rect.x = self.pos.x - self.radius
                else:
                    if self.pos.y > wall.rect.centery:
                        self.pos.y = wall.rect.bottom + self.radius
                    else:
                        self.pos.y = wall.rect.top - self.radius
                    z_rect.y = self.pos.y - self.radius

    def resolve_static_overlaps(self, walls):
        for wall in walls:
            z_rect = pygame.Rect(
                self.pos.x - self.radius,
                self.pos.y - self.radius,
                self.radius * 2,
                self.radius * 2,
            )
            if not z_rect.colliderect(wall.rect):
                continue
            if self.pos.x < wall.rect.centerx:
                push_x = wall.rect.left - z_rect.right
            else:
                push_x = wall.rect.right - z_rect.left
            if self.pos.y < wall.rect.centery:
                push_y = wall.rect.top - z_rect.bottom
            else:
                push_y = wall.rect.bottom - z_rect.top
            if abs(push_x) < abs(push_y):
                self.pos.x += push_x
            else:
                self.pos.y += push_y

    def hit(self, dmg, bullet_dir):
        self.hp -= dmg
        self.hit_flash = 0.1
        if self.type not in ["Boss", "Tank"]:
            self.pos += bullet_dir * 15

    def draw(self, surf, offset):
        draw_pos = self.pos - offset

        shadow_alpha = int(90 * (self.alpha / 255)) if self.type == "Stalker" else 90
        if shadow_alpha > 4:
            draw_shadow(surf, draw_pos, self.radius, shadow_alpha)

        body_color = C_WHITE if self.hit_flash > 0 else self.color
        dark_color = tuple(max(0, channel - 60) for channel in body_color)
        alpha = self.alpha if self.type == "Stalker" else 255
        size = self.radius * 2 + 10
        body = pygame.Surface((size, size), pygame.SRCALPHA)
        center = pygame.Vector2(size / 2, size / 2)
        pygame.draw.circle(body, (*dark_color, alpha), center, self.radius + 2)
        pygame.draw.circle(body, (*body_color, alpha), center, self.radius)
        pygame.draw.circle(body, (*dark_color, alpha), center, max(4, self.radius - 7))

        eye_forward = self.facing * max(4, self.radius * 0.35)
        eye_side = self.facing.rotate(90) * max(2, self.radius * 0.17)
        eye_color = (255, 235, 190, alpha)
        eye_radius = max(2, int(self.radius * 0.08))
        pygame.draw.circle(body, eye_color, center + eye_forward + eye_side, eye_radius)
        pygame.draw.circle(body, eye_color, center + eye_forward - eye_side, eye_radius)
        surf.blit(body, draw_pos - center)

        if self.type == "Runner":
            back = draw_pos - self.facing * (self.radius + 4)
            side = self.facing.rotate(90) * 5
            pygame.draw.line(surf, C_DARK_RED, back + side, back - self.facing * 8 + side, 2)
            pygame.draw.line(surf, C_DARK_RED, back - side, back - self.facing * 6 - side, 2)
        elif self.type == "Tank":
            pygame.draw.circle(surf, (150, 150, 155), draw_pos, self.radius - 5, 3)
        elif self.type == "Screamer":
            pygame.draw.circle(surf, C_PURPLE, draw_pos, self.radius + 4, 2)
        elif self.type == "Spitter":
            pygame.draw.circle(surf, (205, 255, 120), draw_pos, max(4, self.radius // 4))
        elif self.type == "Boss":
            ring_color = {"Juggernaut": C_RED, "Broodmother": C_PURPLE, "Reaper": C_ORANGE}.get(self.boss_variant, C_RED)
            pygame.draw.circle(surf, ring_color, draw_pos, self.radius + 5, 3)

        if self.buff_timer > 0:
            pygame.draw.circle(surf, C_RED, draw_pos, self.radius + 4, 2)

        if self.type == "Exploder" and self.fuse is not None:
            pulse = abs(math.sin(pygame.time.get_ticks() * 0.03))
            pygame.draw.circle(surf, C_ORANGE, draw_pos, self.radius + 4 + pulse * 8, 3)

        if self.type == "Boss":
            if self.boss_state in ("charge_windup", "slam_windup"):
                pulse = abs(math.sin(pygame.time.get_ticks() * 0.02))
                pygame.draw.circle(surf, C_RED, draw_pos, self.radius + 6 + pulse * 12, 3)
            if self.boss_state == "slam":
                s = pygame.Surface((340, 340), pygame.SRCALPHA)
                pygame.draw.circle(s, (220, 40, 40, 90), (170, 170), 170)
                surf.blit(s, draw_pos - pygame.Vector2(170, 170))

        if self.type != "Boss" and self.alpha > 80:
            bar_w = self.radius * 2
            hp_ratio = max(0, self.hp / self.max_hp)
            pygame.draw.rect(surf, (40, 40, 40), (draw_pos.x - bar_w / 2, draw_pos.y - self.radius - 10, bar_w, 4))
            pygame.draw.rect(surf, C_RED, (draw_pos.x - bar_w / 2, draw_pos.y - self.radius - 10, bar_w * hp_ratio, 4))

        if self.type == "Boss":
            w = 120
            hp_ratio = max(0, self.hp / self.max_hp)
            pygame.draw.rect(surf, (50, 50, 50), (draw_pos.x - w / 2, draw_pos.y - self.radius - 20, w, 10))
            pygame.draw.rect(surf, C_RED, (draw_pos.x - w / 2, draw_pos.y - self.radius - 20, w * hp_ratio, 10))


class Game:
    def __init__(self):
        self.state = "MENU"
        self.sound = SoundManager()
        pygame.mouse.set_visible(False)
        self.reset_game()

    def generate_background(self):
        bg = pygame.Surface((WORLD_W, WORLD_H))
        bg.fill(C_BG)
        texture_rng = random.Random(731)
        tile_size = 192
        for y in range(0, WORLD_H, tile_size):
            for x in range(0, WORLD_W, tile_size):
                variation = texture_rng.choice((0, 0, 1, 1, 2))
                tile_color = (C_BG[0] + variation, C_BG[1] + variation, C_BG[2] + variation)
                pygame.draw.rect(bg, tile_color, (x, y, tile_size, tile_size))
                pygame.draw.line(bg, (17, 20, 26), (x, y), (x + tile_size, y))
                pygame.draw.line(bg, (6, 8, 11), (x, y + tile_size - 1), (x + tile_size, y + tile_size - 1))

        for _ in range(70):
            x = texture_rng.randint(40, WORLD_W - 40)
            y = texture_rng.randint(40, WORLD_H - 40)
            width = texture_rng.randint(28, 90)
            height = texture_rng.randint(8, 24)
            pygame.draw.ellipse(bg, (7, 9, 12), (x, y, width, height))

        for _ in range(95):
            start = pygame.Vector2(texture_rng.randint(0, WORLD_W), texture_rng.randint(0, WORLD_H))
            bend = start + pygame.Vector2(texture_rng.randint(-28, 28), texture_rng.randint(-28, 28))
            end = bend + pygame.Vector2(texture_rng.randint(-22, 22), texture_rng.randint(-22, 22))
            pygame.draw.lines(bg, (18, 21, 27), False, (start, bend, end), 1)

        speckle_count = 8000
        for _ in range(speckle_count):
            x = texture_rng.randint(0, WORLD_W - 1)
            y = texture_rng.randint(0, WORLD_H - 1)
            shade = texture_rng.randint(-2, 5)
            c = max(0, min(252, C_BG[0] + shade))
            pygame.draw.circle(bg, (c, c + 1, c + 3), (x, y), 1)
        return bg

    def reset_game(self):
        self.camera = Camera()
        self.player = Player(self.sound)
        self.zombies = []
        self.bullets = []
        self.particles = []
        self.items = []
        self.acid_projs = []
        self.acid_pools = []
        self.flashes = []
        self.blood_stains = []
        self.barrels = []
        self.walls = []
        self.lights = []
        self.hit_effect_timer = 0
        self.hitstop_timer = 0
        self.damage_numbers = []
        self.combo_popups = []
        self.between_waves = False
        self.messages = []
        self.inventory_return_state = "PLAYING"

        self.ambient_dust = []
        for _ in range(50):
            self.ambient_dust.append({
                'pos': pygame.Vector2(random.uniform(0, WORLD_W), random.uniform(0, WORLD_H)),
                'speed': random.uniform(2, 5),
                'dir': pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize(),
                'size': random.uniform(1, 2.0)
            })

        placement_attempts = 0
        while len(self.walls) < 14 and placement_attempts < 120:
            placement_attempts += 1
            wx = random.randint(300, WORLD_W - 500)
            wy = random.randint(300, WORLD_H - 500)
            ww = random.choice([140, 220, 300])
            wh = random.choice([45, 110])
            candidate = Wall(wx, wy, ww, wh)
            safe_center = pygame.Rect(WORLD_W / 2 - 260, WORLD_H / 2 - 220, 520, 440)
            if candidate.rect.colliderect(safe_center):
                continue
            if any(candidate.rect.inflate(90, 90).colliderect(wall.rect) for wall in self.walls):
                continue
            self.walls.append(candidate)

        self.lights = [
            LightSource((WORLD_W * 0.3, WORLD_H * 0.3), 320),
            LightSource((WORLD_W * 0.7, WORLD_H * 0.3), 320),
            LightSource((WORLD_W * 0.5, WORLD_H * 0.7), 350)
        ]

        for _ in range(8):
            bx = random.randint(200, WORLD_W - 200)
            by = random.randint(200, WORLD_H - 200)
            self.barrels.append(ExplosiveBarrel((bx, by)))

        self.wave = 1
        self.wave_timer = 2.0
        self.zombies_to_spawn = 0
        self.spawn_timer = 0
        self.zombies_remaining = 0
        self.wave_reward_given = False

        self.bg_surface = self.generate_background()
        self.start_wave()
        self.push_message("LOCK AND LOAD", C_YELLOW, 2.5)

    def start_wave(self):
        self.wave_reward_given = False
        if self.wave % BOSS_INTERVAL == 0:
            self.zombies_to_spawn = 1
            self.zombies_remaining = 1
        else:
            self.zombies_to_spawn = 6 + int(self.wave * 2.0)
            self.zombies_remaining = self.zombies_to_spawn
        if hasattr(self, "messages"):
            if self.wave % BOSS_INTERVAL == 0:
                stage = max(1, self.wave // BOSS_INTERVAL)
                variant = ("JUGGERNAUT", "BROODMOTHER", "REAPER")[(stage - 1) % 3]
                label = f"BOSS INBOUND: {variant}"
            else:
                label = f"WAVE {self.wave}"
            self.push_message(label, C_RED if self.wave % BOSS_INTERVAL == 0 else C_WHITE, 2.2)

    def spawn_zombie(self):
        if self.wave % BOSS_INTERVAL == 0:
            return Zombie("Boss", self.player.pos, self.wave)

        r = random.random()
        tank_chance = min(0.12, self.wave * 0.01)
        runner_chance = min(0.28, self.wave * 0.02)
        exploder_chance = min(0.18, self.wave * 0.012)
        special_chance = min(0.25, self.wave * 0.015)

        if r < tank_chance and self.wave >= 3:
            return Zombie("Tank", self.player.pos, self.wave)
        elif r < tank_chance + runner_chance and self.wave >= 2:
            return Zombie("Runner", self.player.pos, self.wave)
        elif r < tank_chance + runner_chance + exploder_chance and self.wave >= 3:
            return Zombie("Exploder", self.player.pos, self.wave)
        elif r < tank_chance + runner_chance + exploder_chance + special_chance and self.wave >= 2:
            s_type = random.choice(["Screamer", "Stalker", "Spitter"])
            return Zombie(s_type, self.player.pos, self.wave)
        else:
            return Zombie("Normal", self.player.pos, self.wave)

    def spawn_particles(self, pos, color, count, speed=150, life=0.5):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            vel = pygame.Vector2(math.cos(angle), math.sin(angle)) * random.uniform(speed * 0.2, speed)
            self.particles.append(Particle(pos, vel, color, random.uniform(life * 0.5, life)))

    def push_message(self, text, color=C_WHITE, duration=2.0):
        self.messages.append({"text": text, "color": color, "life": duration, "max_life": duration})
        self.messages = self.messages[-4:]

    def get_aim_direction(self):
        mouse_world = pygame.Vector2(pygame.mouse.get_pos()) + pygame.Vector2(self.camera.x, self.camera.y)
        direction = mouse_world - self.player.pos
        if direction.length_squared() == 0:
            return pygame.Vector2(1, 0)
        return direction.normalize()

    def finish_zombie(self, zombie):
        if zombie not in self.zombies:
            return
        self.spawn_particles(zombie.pos, C_RED, 20, 250, 0.6)
        for _ in range(3):
            offset = pygame.Vector2(random.uniform(-14, 14), random.uniform(-14, 14))
            self.blood_stains.append(BloodStain(zombie.pos + offset))
        self.sound.play(random.choice(["zombie1", "zombie2", "zombie3"]), 0.15)
        if zombie.type == "Boss":
            self.items.append(Item(zombie.pos + pygame.Vector2(-25, 0), "Medkit"))
            self.items.append(Item(zombie.pos + pygame.Vector2(25, 0), "Ammo"))
            self.items.append(Item(zombie.pos + pygame.Vector2(0, 28), "Damage Boost"))
            boss_weapon = random.choice(["Revolver", "SMG", "Rifle", "Shotgun", "LMG", "Launcher"])
            self.items.append(Item(zombie.pos + pygame.Vector2(0, -32), boss_weapon))
            self.push_message(f"{zombie.boss_variant.upper()} ELIMINATED", C_YELLOW, 3.0)
        else:
            self.drop_loot(zombie.pos)
        self.award_kill(zombie.type, zombie.pos)
        self.zombies.remove(zombie)
        self.hitstop_timer = max(self.hitstop_timer, 0.10 if zombie.type == "Boss" else 0.025)

    def melee_attack(self):
        if self.player.melee_cooldown > 0:
            return
        self.player.melee_cooldown = 0.9 * self.player.melee_cooldown_mult
        self.sound.play("melee", 0.45)
        aim_dir = self.get_aim_direction()
        hit_any = False
        self.camera.shake(5)
        self.spawn_particles(self.player.pos + aim_dir * 35, C_WHITE, 8, 120, 0.25)
        for zombie in self.zombies[:]:
            to_zombie = zombie.pos - self.player.pos
            if to_zombie.length_squared() == 0:
                angle = 0
            else:
                angle = abs(aim_dir.angle_to(to_zombie))
            if to_zombie.length() <= 96 + zombie.radius and angle <= 58:
                hit_any = True
                damage = int(self.player.melee_damage * self.player.dmg_mult)
                zombie.hit(damage, aim_dir)
                zombie.pos += aim_dir * 42
                self.damage_numbers.append(DamageNumber(zombie.pos, damage, C_CYAN, zombie.hp <= 0))
                if zombie.hp <= 0:
                    self.finish_zombie(zombie)
        if hit_any:
            self.camera.shake(10)

    def use_medkit(self):
        if self.player.medkits <= 0 or self.player.hp >= self.player.max_hp:
            self.sound.play("error", 0.35)
            return
        self.player.medkits -= 1
        self.player.hp = min(self.player.max_hp, self.player.hp + 45)
        self.sound.play("pickup", 0.5)
        self.spawn_particles(self.player.pos, C_GREEN, 18, 100, 0.7)
        self.push_message("MEDKIT USED", C_GREEN, 1.2)

    def award_kill(self, z_type, pos):
        base = 1000 if z_type == "Boss" else 100
        self.player.combo_timer = 3.2
        self.player.combo += 1
        mult = min(5, 1 + self.player.combo // 3)
        self.player.score += base * mult
        self.player.kills += 1
        self.zombies_remaining -= 1
        if mult > 1:
            self.combo_popups.append(ComboPopup(pos, mult))
        if self.player.combo > 0 and self.player.combo % 10 == 0:
            self.items.append(Item(pos, random.choice(["Ammo", "Medkit", "Damage Boost", "Overdrive"])))
            self.push_message("10-KILL DROP", C_YELLOW, 1.2)

    def drop_loot(self, pos):
        if random.random() < 0.36:
            r = random.random()
            if r < 0.25:
                item = "Ammo"
            elif r < 0.48:
                item = "Medkit"
            elif r < 0.61:
                item = "Damage Boost"
            elif r < 0.73:
                item = "Overdrive"
            else:
                weapon_pool = ["SMG", "Revolver", "Rifle", "Shotgun"]
                if self.wave >= 5:
                    weapon_pool.append("LMG")
                if self.wave >= 7:
                    weapon_pool.append("Launcher")
                item = random.choice(weapon_pool)
            self.items.append(Item(pos, item))

    def collect_item(self, item):
        if item not in self.items:
            return False
        if item.type == "Medkit":
            self.player.medkits += 1
        elif item.type == "Ammo":
            for weapon in self.player.weapons:
                weapon.reserve += max(1, int(weapon.mag_size * 0.55))
        elif item.type == "Damage Boost":
            self.player.damage_boost_timer = 14.0
        elif item.type == "Overdrive":
            self.player.overdrive_timer = 12.0
        else:
            owned = [w.name for w in self.player.weapons]
            if item.type not in owned:
                new_weapon = Weapon(item.type)
                new_weapon.reload_time *= self.player.reload_mult
                self.player.weapons.append(new_weapon)
            else:
                for weapon in self.player.weapons:
                    if weapon.name == item.type:
                        weapon.reserve += weapon.mag_size
        self.sound.play("pickup", 0.45)
        self.push_message(f"+ {item.type.upper()}", C_GREEN, 0.9)
        self.items.remove(item)
        return True

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if self.state == "MENU" or self.state == "GAMEOVER":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    self.reset_game()
                    self.state = "PLAYING"

            elif self.state == "PLAYING":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.state = "PAUSED"
                    elif event.key == pygame.K_r:
                        if self.player.weapon.reload():
                            self.player.play_reload_sound(self.player.weapon.name)
                    elif event.key in (pygame.K_i, pygame.K_TAB):
                        self.state = "INVENTORY"
                        self.sound.play("select", 0.35)
                    elif event.key == pygame.K_h:
                        self.use_medkit()
                    elif event.key == pygame.K_q:
                        self.melee_attack()
                    elif event.key == pygame.K_1:
                        self.player.switch_weapon(0)
                    elif event.key == pygame.K_2:
                        self.player.switch_weapon(1)
                    elif event.key == pygame.K_3:
                        self.player.switch_weapon(2)
                    elif event.key == pygame.K_4:
                        self.player.switch_weapon(3)
                    elif event.key == pygame.K_5:
                        self.player.switch_weapon(4)
                    elif event.key == pygame.K_6:
                        self.player.switch_weapon(5)
                    elif event.key == pygame.K_7:
                        self.player.switch_weapon(6)
                    elif event.key == pygame.K_e:
                        for item in self.items[:]:
                            if self.player.pos.distance_to(item.pos) < 60:
                                self.collect_item(item)
                                break

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                    self.melee_attack()
                elif event.type == pygame.MOUSEWHEEL and self.player.weapons:
                    self.player.current_weapon_idx = (self.player.current_weapon_idx - event.y) % len(self.player.weapons)
                    self.sound.play("select", 0.25)

            elif self.state == "PAUSED":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state = "PLAYING"

            elif self.state == "INVENTORY":
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_i, pygame.K_TAB, pygame.K_ESCAPE):
                        self.state = "PLAYING"
                    elif pygame.K_1 <= event.key <= pygame.K_7:
                        self.player.switch_weapon(event.key - pygame.K_1)
                        self.sound.play("select", 0.35)

        if self.state == "PLAYING" and pygame.mouse.get_pressed()[0]:
            wp = self.player.weapon
            if wp.auto or wp.fire_timer <= 0:
                mouse_pos = pygame.Vector2(pygame.mouse.get_pos()) + self.camera.get_offset()
                dir_vec = (mouse_pos - self.player.pos)
                if dir_vec.length_squared() > 0:
                    dir_vec.normalize_ip()
                    fire_rate_mult = 0.62 if self.player.overdrive_timer > 0 else 1.0
                    if wp.shoot(fire_rate_mult):
                        if wp.name in ("Pistol", "Revolver"):
                            self.sound.play("pistol_fire", 0.7)
                        elif wp.name in ("Rifle", "SMG", "LMG"):
                            self.sound.play("rifle_fire", 0.6, maxtime=150)
                        elif wp.name in ("Shotgun", "Launcher"):
                            self.sound.play("shotgun_fire", 1.0)

                        self.camera.shake(wp.damage * 0.1)
                        self.flashes.append(MuzzleFlash(self.player.pos, dir_vec, wp.color))

                        boost_mult = 1.55 if self.player.damage_boost_timer > 0 else 1.0
                        base_dmg = wp.damage * self.player.dmg_mult * boost_mult

                        for _ in range(wp.pellets):
                            spread_angle = random.uniform(-wp.spread, wp.spread)
                            b_dir = dir_vec.rotate(spread_angle)
                            final_dmg = base_dmg * random.uniform(0.9, 1.1)
                            self.bullets.append(Bullet(
                                self.player.pos, b_dir, final_dmg, wp.pierce, wp.name, wp.color,
                                speed=wp.projectile_speed, explosive_radius=wp.explosive_radius
                            ))
                    elif wp.ammo <= 0 and wp.reserve <= 0 and wp.fire_timer <= 0:
                        self.sound.play("empty", 0.4)
                        wp.fire_timer = 0.35

    def trigger_explosion(self, pos, radius, damage, player_damage_scale=0.5):
        try:
            self.sound.play("explosion", 0.8)
        except:
            pass
        self.camera.shake(30)
        self.spawn_particles(pos, C_ORANGE, 40, 400, 1.0)
        self.spawn_particles(pos, (100, 100, 100), 20, 200, 1.5)

        if self.player.pos.distance_to(pos) < radius + self.player.radius:
            self.player.take_damage(damage * player_damage_scale)
            self.hit_effect_timer = 0.4
            if self.player.hp <= 0:
                self.state = "GAMEOVER"

        for z in self.zombies[:]:
            if z.pos.distance_to(pos) < radius + z.radius:
                z.hit(damage, (z.pos - pos).normalize() if z.pos != pos else pygame.Vector2(1, 0))
                if z.hp <= 0:
                    self.finish_zombie(z)

        for _ in range(5):
            self.blood_stains.append(BloodStain(pos + pygame.Vector2(random.uniform(-40, 40), random.uniform(-40, 40))))
        if len(self.blood_stains) > 400:
            self.blood_stains = self.blood_stains[-400:]

    def update(self, dt):
        if self.state != "PLAYING": return

        if self.hitstop_timer > 0:
            self.hitstop_timer -= dt
            return

        if self.hit_effect_timer > 0:
            self.hit_effect_timer -= dt

        for message in self.messages[:]:
            message["life"] -= dt
            if message["life"] <= 0:
                self.messages.remove(message)

        if self.player.combo_timer > 0:
            self.player.combo_timer -= dt
            if self.player.combo_timer <= 0:
                self.player.combo = 0

        for d in self.ambient_dust:
            d['pos'] += d['dir'] * d['speed'] * dt
            if d['pos'].x < 0: d['pos'].x = WORLD_W
            if d['pos'].x > WORLD_W: d['pos'].x = 0
            if d['pos'].y < 0: d['pos'].y = WORLD_H
            if d['pos'].y > WORLD_H: d['pos'].y = 0

        self.player.update(dt, self.walls, self.sound)

        for item in self.items[:]:
            if item.type not in WEAPON_STATS and self.player.pos.distance_to(item.pos) < 34:
                self.collect_item(item)

        if self.player.dash_timer > 0:
            dash_dir = self.player.dash_dir.normalize() if self.player.dash_dir.length_squared() else pygame.Vector2(1, 0)
            for zombie in self.zombies[:]:
                if zombie in self.player.dash_hit_targets:
                    continue
                if self.player.pos.distance_to(zombie.pos) < self.player.radius + zombie.radius + 12:
                    self.player.dash_hit_targets.add(zombie)
                    damage = int(60 * self.player.dmg_mult)
                    zombie.hit(damage, dash_dir)
                    zombie.pos += dash_dir * 55
                    self.damage_numbers.append(DamageNumber(zombie.pos, damage, C_CYAN, zombie.hp <= 0))
                    self.spawn_particles(zombie.pos, C_CYAN, 10, 180, 0.35)
                    self.camera.shake(10)
                    if zombie.hp <= 0:
                        self.finish_zombie(zombie)

        self.camera.update(self.player.pos, dt)

        self.between_waves = self.zombies_remaining <= 0 and not self.zombies
        if self.between_waves:
            if not self.wave_reward_given:
                self.wave_reward_given = True
                self.items.append(Item(self.player.pos + pygame.Vector2(-45, 35), "Ammo"))
                if self.wave == 1 or self.wave % 2 == 0:
                    reward_pool = ["SMG", "Revolver", "Rifle", "Shotgun"]
                    if self.wave >= 5: reward_pool.append("LMG")
                    if self.wave >= 7: reward_pool.append("Launcher")
                    self.items.append(Item(
                        self.player.pos + pygame.Vector2(45, 35),
                        random.choice(reward_pool)
                    ))
                else:
                    self.items.append(Item(self.player.pos + pygame.Vector2(45, 35), random.choice(["Medkit", "Damage Boost", "Overdrive"])))
                self.sound.play("loot", 0.45)
                self.push_message("WAVE REWARD DROPPED", C_YELLOW, 2.0)
            self.wave_timer -= dt
            if self.wave_timer <= 0:
                self.wave += 1
                self.start_wave()
                self.wave_timer = 2.0

        if self.zombies_to_spawn > 0 and len(self.zombies) < 26:
            self.spawn_timer -= dt
            if self.spawn_timer <= 0:
                zombie = self.spawn_zombie()
                for _ in range(7):
                    spawn_rect = pygame.Rect(
                        zombie.pos.x - zombie.radius, zombie.pos.y - zombie.radius,
                        zombie.radius * 2, zombie.radius * 2
                    )
                    if not any(spawn_rect.colliderect(wall.rect) for wall in self.walls):
                        break
                    zombie = self.spawn_zombie()
                self.zombies.append(zombie)
                self.zombies_to_spawn -= 1
                self.spawn_timer = random.uniform(0.22, 0.75)

        for p in self.acid_pools[:]:
            if not p.update(dt):
                self.acid_pools.remove(p)
            elif self.player.pos.distance_to(p.pos) < p.radius + self.player.radius:
                self.player.hp -= p.damage * dt
                self.hit_effect_timer = max(self.hit_effect_timer, 0.08)
                if self.player.hp <= 0:
                    self.state = "GAMEOVER"

        for ap in self.acid_projs[:]:
            ap.update(dt)
            if self.player.pos.distance_to(ap.pos) < self.player.radius:
                if self.player.take_damage(20):
                    self.hit_effect_timer = 0.4
                self.acid_pools.append(AcidPool(ap.pos))
                self.acid_projs.remove(ap)
                if self.player.hp <= 0:
                    self.state = "GAMEOVER"
            elif not ap.alive:
                self.acid_pools.append(AcidPool(ap.pos))
                self.acid_projs.remove(ap)

        for z in self.zombies[:]:
            action = z.update(dt, self.player, self.walls, self.sound, self.zombies)

            if action == "scream":
                self.sound.play(random.choice(["zombie1", "zombie2", "zombie3"]), 0.2)
                self.camera.shake(10)
                self.spawn_particles(z.pos, C_WHITE, 20, 300, 1.0)
                for other_z in self.zombies:
                    if other_z.pos.distance_to(z.pos) < 300:
                        other_z.buff_timer = 5.0
            elif action == "spit":
                self.acid_projs.append(AcidProjectile(z.pos, self.player.pos))
            elif action == "summon":
                self.camera.shake(12)
                self.spawn_particles(z.pos, C_PURPLE, 28, 260, 0.8)
                for idx in range(4 if not z.enraged else 6):
                    minion_type = "Runner" if idx % 2 else "Normal"
                    minion = Zombie(minion_type, self.player.pos, self.wave)
                    angle = idx * (360 / (4 if not z.enraged else 6))
                    minion.pos = z.pos + pygame.Vector2(95, 0).rotate(angle)
                    self.zombies.append(minion)
                    self.zombies_remaining += 1
                self.push_message("BROODMOTHER: REINFORCEMENTS", C_PURPLE, 1.8)
            elif action == "boss_spit":
                base_dir = self.player.pos - z.pos
                if base_dir.length_squared() == 0:
                    base_dir = pygame.Vector2(1, 0)
                base_dir.normalize_ip()
                for angle in (-24, -12, 0, 12, 24):
                    target = z.pos + base_dir.rotate(angle) * 560
                    self.acid_projs.append(AcidProjectile(z.pos, target))
            elif action == "reaper_burst":
                self.camera.shake(26)
                self.spawn_particles(z.pos, C_ORANGE, 42, 420, 0.8)
                if self.player.pos.distance_to(z.pos) < 215 + self.player.radius:
                    if self.player.take_damage(55):
                        self.hit_effect_timer = 0.4
            elif action == "slam":
                self.camera.shake(22)
                self.spawn_particles(z.pos, C_RED, 30, 300, 0.6)
                self.sound.play(random.choice(["zombie1", "zombie2", "zombie3"]), 0.25)
                if self.player.pos.distance_to(z.pos) < 150 + self.player.radius:
                    if self.player.take_damage(65):
                        self.hit_effect_timer = 0.4
                        if self.player.hp <= 0:
                            self.state = "GAMEOVER"
            elif action == "explode":
                self.camera.shake(20)
                self.spawn_particles(z.pos, C_ORANGE, 30, 350, 0.7)
                self.sound.play("explosion", 0.8)
                if self.player.pos.distance_to(z.pos) < 130 + self.player.radius:
                    if self.player.take_damage(45):
                        self.hit_effect_timer = 0.4
                        if self.player.hp <= 0:
                            self.state = "GAMEOVER"
                for _ in range(4):
                    self.blood_stains.append(BloodStain(z.pos + pygame.Vector2(random.uniform(-25, 25), random.uniform(-25, 25))))
                self.award_kill(z.type, z.pos)
                if z in self.zombies:
                    self.zombies.remove(z)
                continue

            if z.pos.distance_to(self.player.pos) < z.radius + self.player.radius:
                if self.player.take_damage(z.damage):
                    self.camera.shake(15)
                    self.spawn_particles(self.player.pos, C_RED, 15)
                    self.blood_stains.append(BloodStain(self.player.pos))
                    self.hit_effect_timer = 0.4
                    if self.player.hp <= 0:
                        self.state = "GAMEOVER"

        for _ in range(2):
            for i, z1 in enumerate(self.zombies):
                for z2 in self.zombies[i + 1:]:
                    delta = z1.pos - z2.pos
                    dist = delta.length()
                    min_dist = z1.radius + z2.radius + 4
                    if dist >= min_dist:
                        continue
                    if dist == 0:
                        delta = pygame.Vector2(1, 0).rotate((i * 137) % 360)
                        dist = 1
                    normal = delta / dist
                    overlap = min_dist - dist
                    mass1 = 3.0 if z1.type in ("Tank", "Boss") else 1.0
                    mass2 = 3.0 if z2.type in ("Tank", "Boss") else 1.0
                    total_mass = mass1 + mass2
                    z1.pos += normal * overlap * (mass2 / total_mass)
                    z2.pos -= normal * overlap * (mass1 / total_mass)

            for zombie in self.zombies:
                zombie.resolve_static_overlaps(self.walls)
                zombie.pos.x = max(zombie.radius, min(WORLD_W - zombie.radius, zombie.pos.x))
                zombie.pos.y = max(zombie.radius, min(WORLD_H - zombie.radius, zombie.pos.y))

        for b in self.bullets[:]:
            b.update(dt)
            if not b.alive:
                self.bullets.remove(b)
                continue

            hit_something = False

            for wall in self.walls:
                if wall.rect.clipline(b.prev_pos, b.pos):
                    hit_something = True
                    self.spawn_particles(b.pos, (150, 150, 150), 4, 120, 0.25)
                    if b.explosive_radius > 0:
                        self.trigger_explosion(b.pos, b.explosive_radius, b.damage, player_damage_scale=0.08)
                    break

            if hit_something and not b.pierce:
                self.bullets.remove(b)
                continue

            for barrel in self.barrels[:]:
                if b.pos.distance_to(barrel.pos) < barrel.radius:
                    hit_something = True
                    self.spawn_particles(b.pos, C_ORANGE, 4, 150, 0.25)
                    if barrel.hit(b.damage):
                        self.trigger_explosion(barrel.pos, 180, 250)
                        self.barrels.remove(barrel)
                    break

            if hit_something and not b.pierce:
                self.bullets.remove(b)
                continue

            for z in self.zombies:
                if z not in b.hit_targets and b.pos.distance_to(z.pos) < z.radius:
                    if b.explosive_radius > 0:
                        self.trigger_explosion(b.pos, b.explosive_radius, b.damage, player_damage_scale=0.08)
                        hit_something = True
                        break
                    actual_dmg = b.get_actual_damage()
                    z.hit(actual_dmg, b.dir)
                    self.spawn_particles(b.pos, C_DARK_RED, 5, 200, 0.3)
                    self.blood_stains.append(BloodStain(z.pos))
                    if len(self.blood_stains) > 400: self.blood_stains.pop(0)
                    self.damage_numbers.append(DamageNumber(b.pos, actual_dmg, C_YELLOW, big=z.hp <= 0))

                    b.hit_targets.append(z)
                    hit_something = True

                    if z.hp <= 0:
                        self.finish_zombie(z)

                    if not b.pierce: break

            if hit_something and not b.pierce:
                self.bullets.remove(b)

        self.particles = [p for p in self.particles if p.update(dt)]
        self.flashes = [f for f in self.flashes if f.update(dt)]
        self.damage_numbers = [d for d in self.damage_numbers if d.update(dt)]
        self.combo_popups = [c for c in self.combo_popups if c.update(dt)]
        for i in self.items: i.update(dt)

    def draw_hud(self):
        left_panel = pygame.Surface((238, 184), pygame.SRCALPHA)
        left_panel.fill((5, 7, 11, 205))
        pygame.draw.rect(left_panel, (45, 52, 64, 230), left_panel.get_rect(), 1, border_radius=7)
        screen.blit(left_panel, (11, 11))

        right_panel = pygame.Surface((265, 108), pygame.SRCALPHA)
        right_panel.fill((5, 7, 11, 190))
        pygame.draw.rect(right_panel, (45, 52, 64, 220), right_panel.get_rect(), 1, border_radius=7)
        screen.blit(right_panel, (WIDTH - 276, 11))

        pygame.draw.rect(screen, (50, 50, 50), (20, 20, 200, 25))
        hp_ratio = max(0, self.player.hp / self.player.max_hp)
        pygame.draw.rect(screen, C_RED, (20, 20, 200 * hp_ratio, 25))
        pygame.draw.rect(screen, C_WHITE, (20, 20, 200, 25), 2)

        hp_txt = FONT_SM.render(f"HP: {int(max(0, self.player.hp))}/{self.player.max_hp}", True, C_WHITE)
        screen.blit(hp_txt, (30, 23))

        wp = self.player.weapon
        w_txt = FONT_MD.render(wp.name, True, C_WHITE)
        ammo_txt = FONT_MD.render(f"{wp.ammo} / {wp.reserve}", True, C_YELLOW)
        screen.blit(w_txt, (20, 60))
        screen.blit(ammo_txt, (20, 90))

        if wp.is_reloading:
            rel_txt = FONT_SM.render(f"Reloading... {wp.reload_timer:.1f}", True, C_WHITE)
            screen.blit(rel_txt, (20, 120))

        gear_txt = FONT_SM.render(
            f"Medkit {self.player.medkits} [H]   Weapons [TAB]",
            True, (190, 196, 207)
        )
        screen.blit(gear_txt, (20, 148))

        boost_y = 173
        if self.player.damage_boost_timer > 0:
            boost = FONT_SM.render(f"DAMAGE BOOST {self.player.damage_boost_timer:.1f}s", True, C_RED)
            screen.blit(boost, (20, boost_y)); boost_y += 23
        if self.player.overdrive_timer > 0:
            boost = FONT_SM.render(f"OVERDRIVE {self.player.overdrive_timer:.1f}s", True, C_PURPLE)
            screen.blit(boost, (20, boost_y))

        wave_txt = FONT_MD.render(f"WAVE {self.wave}", True, C_WHITE)
        if self.wave % BOSS_INTERVAL == 0:
            bosses = [z for z in self.zombies if z.type == "Boss"]
            boss_label = bosses[0].boss_variant.upper() if bosses else "BOSS WAVE"
            wave_txt = FONT_MD.render(boss_label, True, C_RED)

        score_txt = FONT_SM.render(f"Score: {self.player.score} | Kills: {self.player.kills}", True, C_WHITE)
        z_txt = FONT_SM.render(f"Enemies Left: {self.zombies_remaining}", True, C_WHITE)

        screen.blit(wave_txt, (WIDTH - wave_txt.get_width() - 20, 20))
        screen.blit(score_txt, (WIDTH - score_txt.get_width() - 20, 60))
        screen.blit(z_txt, (WIDTH - z_txt.get_width() - 20, 90))

        active_bosses = [z for z in self.zombies if z.type == "Boss"]
        if active_bosses:
            boss = active_bosses[0]
            bar_w = 500
            x = WIDTH / 2 - bar_w / 2
            ratio = max(0, boss.hp / boss.max_hp)
            pygame.draw.rect(screen, (22, 24, 30), (x, 22, bar_w, 18), border_radius=5)
            pygame.draw.rect(screen, boss.color, (x, 22, bar_w * ratio, 18), border_radius=5)
            pygame.draw.rect(screen, C_WHITE, (x, 22, bar_w, 18), 2, border_radius=5)
            boss_name = FONT_SM.render(boss.boss_variant.upper(), True, C_WHITE)
            screen.blit(boss_name, (WIDTH / 2 - boss_name.get_width() / 2, 45))

        if self.player.combo_timer > 0 and self.player.combo >= 3:
            mult = min(5, 1 + self.player.combo // 3)
            combo_txt = FONT_SM.render(f"Combo x{mult} ({self.player.combo} kills)", True, C_YELLOW)
            screen.blit(combo_txt, (WIDTH - combo_txt.get_width() - 20, 118))

        if self.between_waves:
            clear_txt = FONT_MD.render(f"WAVE {self.wave} CLEARED", True, C_GREEN)
            next_txt = FONT_SM.render(f"Next wave in {max(0, self.wave_timer):.1f}", True, C_WHITE)
            screen.blit(clear_txt, (WIDTH / 2 - clear_txt.get_width() / 2, 130))
            screen.blit(next_txt, (WIDTH / 2 - next_txt.get_width() / 2, 168))

        if len(self.player.weapons) > 1:
            switch_txt = FONT_SM.render("Mouse wheel / 1-7: switch weapon", True, (150, 155, 165))
            screen.blit(switch_txt, (20, HEIGHT - 30))

        for item in self.items:
            if item.type in WEAPON_STATS and self.player.pos.distance_to(item.pos) < 60:
                p_txt = FONT_MD.render(f"Press E: {item.type}", True, C_WHITE)
                screen.blit(p_txt, (WIDTH / 2 - p_txt.get_width() / 2, HEIGHT / 2 + 50))
                break

        if self.player.dash_cooldown <= 0:
            dash_txt = FONT_SM.render("DASH READY (SPACE)", True, C_GREEN)
            screen.blit(dash_txt, (WIDTH / 2 - dash_txt.get_width() / 2, HEIGHT - 30))

        for idx, message in enumerate(reversed(self.messages)):
            alpha = int(255 * min(1.0, message["life"] / min(0.4, message["max_life"])))
            txt = FONT_MD.render(message["text"], True, message["color"])
            txt.set_alpha(alpha)
            screen.blit(txt, (WIDTH / 2 - txt.get_width() / 2, 75 + idx * 32))

    def draw(self):
        offset = self.camera.get_offset()
        mouse_pos = pygame.Vector2(pygame.mouse.get_pos())

        screen.blit(self.bg_surface, (-offset.x, -offset.y))

        for d in self.ambient_dust:
            d_pos = d['pos'] - offset
            if 0 <= d_pos.x <= WIDTH and 0 <= d_pos.y <= HEIGHT:
                bucket = 4 if d['size'] < 1.35 else (6 if d['size'] < 1.75 else 8)
                sprite = DUST_SPRITES[bucket]
                screen.blit(sprite, (d_pos.x - bucket / 2, d_pos.y - bucket / 2))

        for b in self.blood_stains: b.draw(screen, offset)
        for ap in self.acid_pools: ap.draw(screen, offset)
        for wall in self.walls: wall.draw(screen, offset)
        for light in self.lights: light.draw(screen, offset)
        for barrel in self.barrels: barrel.draw(screen, offset)
        for i in self.items: i.draw(screen, offset)
        for z in self.zombies: z.draw(screen, offset)
        for b in self.bullets: b.draw(screen, offset)
        for ap in self.acid_projs: ap.draw(screen, offset)
        self.player.draw(screen, offset, mouse_pos)
        for p in self.particles: p.draw(screen, offset)
        for f in self.flashes: f.draw(screen, offset)
        for d in self.damage_numbers: d.draw(screen, offset)
        for c in self.combo_popups: c.draw(screen, offset)

        screen.blit(VIGNETTE, (0, 0))

        if self.state == "PLAYING" and self.player.hp > 0 and self.player.hp / self.player.max_hp < 0.25:
            pulse = (math.sin(pygame.time.get_ticks() * 0.006) + 1) / 2
            alpha = int(35 + pulse * 45)
            danger = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            danger.fill((160, 0, 0, alpha))
            screen.blit(danger, (0, 0))

        if self.hit_effect_timer > 0:
            blood_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            alpha_val = int(min(1.0, self.hit_effect_timer * 2.5) * 160)
            pygame.draw.circle(blood_overlay, (180, 20, 20, alpha_val), (WIDTH // 2, HEIGHT // 2), max(WIDTH, HEIGHT) * 0.7, int(max(WIDTH, HEIGHT) * 0.3))
            screen.blit(blood_overlay, (0, 0))

        self.draw_hud()

        mx, my = pygame.mouse.get_pos()
        pygame.draw.line(screen, C_WHITE, (mx - 10, my), (mx + 10, my), 1)
        pygame.draw.line(screen, C_WHITE, (mx, my - 10), (mx, my + 10), 1)

        if self.state == "MENU":
            self.draw_menu("ZOMBIE ECHO", "Press SPACE to Deploy", True)

        elif self.state == "PAUSED":
            self.draw_menu("PAUSED", "Press ESC to Resume", False)

        elif self.state == "GAMEOVER":
            self.draw_menu(
                "YOU DIED",
                f"Wave Reached: {self.wave} | Press SPACE to Restart",
                True
            )

        elif self.state == "INVENTORY":
            self.draw_inventory()

        pygame.display.flip()

    def draw_inventory(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 10, 14, 220))
        screen.blit(overlay, (0, 0))
        panel = pygame.Rect(WIDTH / 2 - 330, 55, 660, 610)
        pygame.draw.rect(screen, (24, 28, 35), panel, border_radius=8)
        pygame.draw.rect(screen, (85, 92, 104), panel, 2, border_radius=8)
        screen.blit(FONT_MD.render("WEAPONS", True, C_WHITE), (panel.x + 24, panel.y + 20))
        info = f"Medkit {self.player.medkits}   |   Aktif silah: {self.player.weapon.name}"
        screen.blit(FONT_SM.render(info, True, (175, 180, 188)), (panel.x + 24, panel.y + 58))

        for idx, weapon in enumerate(self.player.weapons):
            y = panel.y + 100 + idx * 64
            row = pygame.Rect(panel.x + 20, y, panel.width - 40, 52)
            if idx == self.player.current_weapon_idx:
                pygame.draw.rect(screen, (48, 60, 75), row, border_radius=5)
            screen.blit(FONT_MD.render(f"[{idx + 1}]  {weapon.name}", True, C_WHITE), (row.x + 14, row.y + 10))
            stat_text = f"DMG {int(weapon.damage)}   MAG {weapon.mag_size}   AMMO {weapon.ammo}/{weapon.reserve}"
            stat = FONT_SM.render(stat_text, True, (175, 180, 188))
            screen.blit(stat, (row.right - stat.get_width() - 14, row.y + 15))

        hint = FONT_SM.render("1-7 equip    TAB / ESC close", True, (150, 155, 165))
        screen.blit(hint, (panel.centerx - hint.get_width() / 2, panel.bottom - 34))

    def draw_menu(self, title, subtitle, draw_bg):
        if draw_bg:
            bg = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            bg.fill((17, 20, 26, 255))
            screen.blit(bg, (0, 0))

        t_surf = FONT_LG.render(title, True, C_RED if self.state == "GAMEOVER" else C_WHITE)
        s_surf = FONT_MD.render(subtitle, True, C_WHITE)

        screen.blit(t_surf, (WIDTH / 2 - t_surf.get_width() / 2, HEIGHT / 2 - 60))
        screen.blit(s_surf, (WIDTH / 2 - s_surf.get_width() / 2, HEIGHT / 2 + 20))

        if self.state == "MENU":
            controls = FONT_SM.render(
                "WASD Move  |  Mouse Fire  |  Q/RMB Melee  |  H Medkit  |  I Inventory  |  SPACE Dash",
                True, (180, 185, 195)
            )
            screen.blit(controls, (WIDTH / 2 - controls.get_width() / 2, HEIGHT / 2 + 72))


if __name__ == "__main__":
    game = Game()
    while True:
        dt = clock.tick(FPS) / 1000.0
        game.handle_input()
        game.update(dt)
        game.draw()
