"""Capture deterministic release screenshots using the real game renderer."""

import os
import random
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

import pygame

import main


OUTPUT_DIR = os.path.join(ROOT_DIR, "screenshots")


def focus_camera(game):
    game.camera.x = game.player.pos.x - main.WIDTH / 2
    game.camera.y = game.player.pos.y - main.HEIGHT / 2
    game.camera.shake_amount = 0


def add_zombie(game, zombie_type, position, wave):
    zombie = main.Zombie(zombie_type, game.player.pos, wave)
    zombie.pos = pygame.Vector2(position)
    game.zombies.append(zombie)
    return zombie


def save(game, filename):
    game.draw()
    pygame.image.save(main.screen, os.path.join(OUTPUT_DIR, filename))


def capture_menu():
    random.seed(11)
    game = main.Game()
    game.state = "MENU"
    save(game, "menu.png")


def capture_combat():
    random.seed(29)
    game = main.Game()
    game.state = "PLAYING"
    game.player.weapons = [main.Weapon("Rifle")]
    game.player.current_weapon_idx = 0
    game.player.pos = pygame.Vector2(1500, 1500)
    game.player.score = 8450
    game.player.kills = 37
    game.wave = 4
    game.zombies = []
    game.zombies_to_spawn = 0
    game.messages = []

    positions = [
        (1710, 1490), (1660, 1390), (1590, 1660), (1390, 1650),
        (1320, 1450), (1440, 1340), (1780, 1600), (1240, 1580),
    ]
    types = ["Normal", "Runner", "Spitter", "Tank", "Stalker", "Exploder", "Screamer", "Runner"]
    for zombie_type, position in zip(types, positions):
        add_zombie(game, zombie_type, position, game.wave)
    game.zombies_remaining = len(game.zombies)

    game.items = [
        main.Item((1390, 1430), "Ammo"),
        main.Item((1600, 1580), "Damage Boost"),
    ]
    aim = pygame.Vector2(1, -0.05).normalize()
    for distance in (60, 125, 190):
        bullet = main.Bullet(game.player.pos, aim, 22, False, "Rifle", main.C_YELLOW)
        bullet.pos = game.player.pos + aim * distance
        bullet.trail = [bullet.pos - aim * 25, bullet.pos - aim * 10]
        game.bullets.append(bullet)
    game.flashes.append(main.MuzzleFlash(game.player.pos, aim, main.C_YELLOW))
    game.spawn_particles((1710, 1490), main.C_DARK_RED, 15, 100, 1.0)
    game.player.combo = 7
    game.player.combo_timer = 3.0
    focus_camera(game)
    save(game, "combat.png")


def capture_boss():
    random.seed(47)
    game = main.Game()
    game.state = "PLAYING"
    game.player.weapons = [main.Weapon("Shotgun")]
    game.player.current_weapon_idx = 0
    game.player.pos = pygame.Vector2(1450, 1500)
    game.player.score = 12800
    game.player.kills = 61
    game.wave = 5
    game.zombies = []
    game.zombies_to_spawn = 0
    game.messages = []

    boss = add_zombie(game, "Boss", (1710, 1490), game.wave)
    boss.hp = int(boss.max_hp * 0.68)
    add_zombie(game, "Runner", (1600, 1350), game.wave)
    add_zombie(game, "Normal", (1580, 1650), game.wave)
    game.zombies_remaining = len(game.zombies)
    game.acid_pools = [main.AcidPool((1800, 1630))]
    game.items = [main.Item((1350, 1600), "Medkit")]
    game.spawn_particles(boss.pos, main.C_RED, 25, 150, 1.0)
    focus_camera(game)
    save(game, "boss.png")


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    capture_menu()
    capture_combat()
    capture_boss()
    pygame.quit()
