import pygame
import math
import random
import sys

# --- INICIALIZACIÓN Y CONFIGURACIÓN ---
pygame.init()
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Apocalypse 2D: Level Survival")
clock = pygame.time.Clock()

# --- PALETA DE COLORES RETRO/SURVIVAL ---
DARK_GROUND = (25, 28, 36)
GRID_LINE = (35, 40, 50)
WHITE = (240, 240, 240)
BLACK = (10, 10, 12)
RED = (220, 50, 50)
GREEN = (46, 204, 113)
AMBER = (241, 196, 15)
ORANGE = (230, 126, 34)
DARK_GRAY = (30, 30, 35)
LIGHT_GRAY = (180, 180, 190)

# --- CLASES VISUALES Y EFECTOS ---

class Particle:
    def __init__(self, x, y, color, size=3, speed=3):
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        angle = random.uniform(0, math.pi * 2)
        sp = random.uniform(0.5, speed)
        self.vx = math.cos(angle) * sp
        self.vy = math.sin(angle) * sp
        self.lifetime = random.randint(10, 25)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1

    def draw(self, surface):
        if self.lifetime > 0:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.size)


class ShellCasing:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        eject_angle = angle + math.pi / 2 + random.uniform(-0.2, 0.2)
        speed = random.uniform(2, 4)
        self.vx = math.cos(eject_angle) * speed
        self.vy = math.sin(eject_angle) * speed
        self.lifetime = 120

    def update(self):
        if self.lifetime > 100:
            self.x += self.vx
            self.y += self.vy
            self.vx *= 0.85
            self.vy *= 0.85
        self.lifetime -= 1

    def draw(self, surface):
        if self.lifetime > 0:
            pygame.draw.rect(surface, AMBER, (int(self.x), int(self.y), 3, 2))


class Bullet:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.speed = 16
        self.vx = math.cos(angle) * self.speed
        self.vy = math.sin(angle) * self.speed
        self.rect = pygame.Rect(x - 2, y - 2, 4, 4)
        self.lifetime = 60

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.rect.center = (int(self.x), int(int(self.y)))
        self.lifetime -= 1

    def draw(self, surface):
        end_x = self.x - self.vx * 0.8
        end_y = self.y - self.vy * 0.8
        pygame.draw.line(surface, AMBER, (int(self.x), int(self.y)), (int(end_x), int(end_y)), 3)


class SupplyCrate:
    def __init__(self, x, y, crate_type):
        self.rect = pygame.Rect(x - 12, y - 12, 24, 24)
        self.type = crate_type  # "health" o "ammo"

    def draw(self, surface):
        color = GREEN if self.type == "health" else AMBER
        pygame.draw.rect(surface, color, self.rect, border_radius=3)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=3)


# --- ENTIDADES PRINCIPALES ---

class Enemy:
    def __init__(self, x, y, level):
        self.rect = pygame.Rect(x - 14, y - 14, 28, 28)
        self.speed = random.uniform(1.8, 2.4) + (level * 0.15)
        self.health = 25 + (level * 10)
        self.max_health = self.health
        self.color = (random.randint(180, 230), 40, 40)

    def update(self, player_rect):
        angle = math.atan2(player_rect.centery - self.rect.centery, player_rect.centerx - self.rect.centerx)
        self.rect.x += math.cos(angle) * self.speed
        self.rect.y += math.sin(angle) * self.speed

    def draw(self, surface):
        # Cuerpo
        pygame.draw.circle(surface, self.color, self.rect.center, 14)
        pygame.draw.circle(surface, BLACK, self.rect.center, 14, 2)
        
        # Barra de vida enemiga
        if self.health < self.max_health:
            bar_w = 24
            hp_w = max(0, int(bar_w * (self.health / self.max_health)))
            pygame.draw.rect(surface, RED, (self.rect.centerx - 12, self.rect.top - 8, bar_w, 4))
            pygame.draw.rect(surface, GREEN, (self.rect.centerx - 12, self.rect.top - 8, hp_w, 4))


class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x - 16, y - 16, 32, 32)
        self.speed = 4
        self.health = 100
        self.max_health = 100
        self.ammo_in_clip = 15
        self.clip_size = 15
        self.reserve_ammo = 90
        self.reloading = False
        self.reload_timer = 0
        self.recoil = 0

    def move(self, dx, dy):
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071
        self.rect.x = max(20, min(WIDTH - 50, self.rect.x + dx * self.speed))
        self.rect.y = max(20, min(HEIGHT - 50, self.rect.y + dy * self.speed))

    def reload(self):
        if not self.reloading and self.ammo_in_clip < self.clip_size and self.reserve_ammo > 0:
            self.reloading = True
            self.reload_timer = 60  # 1 segundo a 60 FPS

    def update(self):
        if self.reloading:
            self.reload_timer -= 1
            if self.reload_timer <= 0:
                needed = self.clip_size - self.ammo_in_clip
                to_reload = min(needed, self.reserve_ammo)
                self.ammo_in_clip += to_reload
                self.reserve_ammo -= to_reload
                self.reloading = False

        if self.recoil > 0:
            self.recoil -= 0.5

    def draw(self, surface, mouse_pos):
        angle = math.atan2(mouse_pos[1] - self.rect.centery, mouse_pos[0] - self.rect.centerx)
        
        # Arma
        gun_len = 22 - self.recoil
        gun_x = self.rect.centerx + math.cos(angle) * gun_len
        gun_y = self.rect.centery + math.sin(angle) * gun_len
        pygame.draw.line(surface, LIGHT_GRAY, self.rect.center, (int(gun_x), int(gun_y)), 6)
        
        # Cuerpo del jugador
        pygame.draw.circle(surface, GREEN, self.rect.center, 16)
        pygame.draw.circle(surface, BLACK, self.rect.center, 16, 2)


# --- SISTEMA DE DIFICULTAD Y NIVEL ---

class LevelManager:
    def __init__(self):
        self.level = 1
        self.kills_this_level = 0
        self.kills_required = 10
        self.enemies_spawned = 0

    def enemy_killed(self):
        self.kills_this_level += 1
        if self.kills_this_level >= self.kills_required:
            self.advance_level()

    def advance_level(self):
        self.level += 1
        self.kills_this_level = 0
        self.kills_required = 10 + (self.level * 5)
        self.enemies_spawned = 0


# --- DIBUJADO DE HUD INTERFAZ ---

def draw_hud(surface, player, level_mgr, mouse_pos):
    # Panel superior de Estado
    pygame.draw.rect(surface, DARK_GRAY, (10, 10, 320, 90), border_radius=6)
    pygame.draw.rect(surface, LIGHT_GRAY, (10, 10, 320, 90), 2, border_radius=6)

    font = pygame.font.SysFont("Consolas", 16, bold=True)

    # Nivel y Progreso
    lvl_txt = font.render(f"NIVEL {level_mgr.level} | OBJETIVO: {level_mgr.kills_this_level}/{level_mgr.kills_required}", True, AMBER)
    surface.blit(lvl_txt, (20, 20))

    # Barra de Salud
    pygame.draw.rect(surface, BLACK, (20, 42, 200, 14), border_radius=3)
    hp_w = max(0, int(200 * (player.health / player.max_health)))
    pygame.draw.rect(surface, RED, (20, 42, hp_w, 14), border_radius=3)
    hp_txt = font.render(f"{int(player.health)} HP", True, WHITE)
    surface.blit(hp_txt, (230, 40))

    # Munición
    ammo_str = "RECARGANDO..." if player.reloading else f"MUNICIÓN: {player.ammo_in_clip} / {player.reserve_ammo}"
    ammo_color = ORANGE if player.reloading else WHITE
    surface.blit(font.render(ammo_str, True, ammo_color), (20, 68))

    # Minimapa (Inferior Izquierda)
    map_size = 100
    pygame.draw.rect(surface, BLACK, (10, HEIGHT - map_size - 10, map_size, map_size))
    pygame.draw.rect(surface, LIGHT_GRAY, (10, HEIGHT - map_size - 10, map_size, map_size), 1)
    
    # Marcador de jugador en minimapa
    px = 10 + int((player.rect.centerx / WIDTH) * map_size)
    py = (HEIGHT - map_size - 10) + int((player.rect.centery / HEIGHT) * map_size)
    pygame.draw.circle(surface, GREEN, (px, py), 2)

    # Mira personalizada
    pygame.draw.circle(surface, RED, mouse_pos, 8, 1)
    pygame.draw.circle(surface, RED, mouse_pos, 2)


# --- BUCLE PRINCIPAL DEL JUEGO ---

def run_game():
    player = Player(WIDTH // 2, HEIGHT // 2)
    level_mgr = LevelManager()
    
    bullets = []
    enemies = []
    particles = []
    casings = []
    crates = []

    font_big = pygame.font.SysFont("Consolas", 28, bold=True)
    game_over = False

    while True:
        clock.tick(60)
        m_pos = pygame.mouse.get_pos()

        # Eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if not game_over:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if player.ammo_in_clip > 0 and not player.reloading:
                        player.ammo_in_clip -= 1
                        player.recoil = 6
                        angle = math.atan2(m_pos[1] - player.rect.centery, m_pos[0] - player.rect.centerx)
                        bullets.append(Bullet(player.rect.centerx, player.rect.centery, angle))
                        casings.append(ShellCasing(player.rect.centerx, player.rect.centery, angle))
                        
                        # Destello del disparo (Muzzle Flash)
                        for _ in range(5):
                            particles.append(Particle(player.rect.centerx + math.cos(angle)*20, 
                                                      player.rect.centery + math.sin(angle)*20, ORANGE, 4, 5))
                    elif player.ammo_in_clip == 0:
                        player.reload()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        player.reload()
            else:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    return run_game()

        if not game_over:
            # Movimiento
            keys = pygame.key.get_pressed()
            dx = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
            dy = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])
            player.move(dx, dy)
            player.update()

            # Aparición de enemigos según nivel
            max_enemies = 5 + (level_mgr.level * 3)
            if len(enemies) < max_enemies and random.random() < (0.015 + level_mgr.level * 0.005):
                spawn_x = random.choice([-20, WIDTH + 20])
                spawn_y = random.choice([-20, HEIGHT + 20])
                enemies.append(Enemy(spawn_x, spawn_y, level_mgr.level))

            # Proyectiles
            for bullet in bullets[:]:
                bullet.update()
                if bullet.lifetime <= 0 or not screen.get_rect().collidepoint(bullet.x, bullet.y):
                    bullets.remove(bullet)

            # Enemigos e Impactos
            for enemy in enemies[:]:
                enemy.update(player.rect)

                if enemy.rect.colliderect(player.rect):
                    player.health -= 0.6
                    for _ in range(2):
                        particles.append(Particle(player.rect.centerx, player.rect.centery, RED, 3, 2))

                for bullet in bullets[:]:
                    if enemy.rect.colliderect(bullet.rect):
                        enemy.health -= 20
                        if bullet in bullets:
                            bullets.remove(bullet)
                        for _ in range(4):
                            particles.append(Particle(enemy.rect.centerx, enemy.rect.centery, RED, 3, 4))

                if enemy.health <= 0:
                    # Probabilidad de soltar suministros
                    if random.random() < 0.25:
                        crates.append(SupplyCrate(enemy.rect.centerx, enemy.rect.centery, random.choice(["health", "ammo"])))
                    enemies.remove(enemy)
                    level_mgr.enemy_killed()

            # Recolección de Cajas
            for crate in crates[:]:
                if player.rect.colliderect(crate.rect):
                    if crate.type == "health":
                        player.health = min(player.max_health, player.health + 25)
                    elif crate.type == "ammo":
                        player.reserve_ammo += 30
                    crates.remove(crate)

            # Efectos y Casquillos
            for casing in casings[:]:
                casing.update()
                if casing.lifetime <= 0:
                    casings.remove(casing)

            for particle in particles[:]:
                particle.update()
                if particle.lifetime <= 0:
                    particles.remove(particle)

            if player.health <= 0:
                player.health = 0
                game_over = True

        # --- DIBUJADO DE ESCENA ---
        screen.fill(DARK_GROUND)

        # Rejilla del Suelo
        for x in range(0, WIDTH, 40):
            pygame.draw.line(screen, GRID_LINE, (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, 40):
            pygame.draw.line(screen, GRID_LINE, (0, y), (WIDTH, y))

        # Dibujar Objetos
        for casing in casings: casing.draw(screen)
        for crate in crates: crate.draw(screen)
        for bullet in bullets: bullet.draw(screen)
        for enemy in enemies: enemy.draw(screen)
        for particle in particles: particle.draw(screen)

        player.draw(screen, m_pos)
        draw_hud(screen, player, level_mgr, m_pos)

        # Pantalla de Game Over
        if game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((10, 10, 15, 210))
            screen.blit(overlay, (0, 0))

            txt1 = font_big.render("¡SOBREVIVIENTE CAÍDO!", True, RED)
            txt2 = font_big.render(f"Llegaste al Nivel {level_mgr.level}", True, WHITE)
            txt3 = font_big.render("Presiona 'R' para volver a intentar", True, AMBER)

            screen.blit(txt1, (WIDTH // 2 - txt1.get_width() // 2, HEIGHT // 2 - 60))
            screen.blit(txt2, (WIDTH // 2 - txt2.get_width() // 2, HEIGHT // 2))
            screen.blit(txt3, (WIDTH // 2 - txt3.get_width() // 2, HEIGHT // 2 + 60))

        pygame.display.flip()

if __name__ == "__main__":
    run_game()