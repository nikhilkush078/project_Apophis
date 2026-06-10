import pygame
import random
import math

# 1. INITIALIZE PYGAME
pygame.init()

SCREEN_WIDTH = 900
SCREEN_HEIGHT = 700
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Space Infiltration - Clean Canvas")

clock = pygame.time.Clock()

# Colors
BACKGROUND_COLOR = (10, 10, 15)
SAFE_ZONE_COLOR = (15, 25, 20)       
RESTRICTED_LINE_COLOR = (255, 140, 0) 
PLAYER_COLOR = (0, 255, 200)
POLICE_COLOR = (50, 50, 255)

# --- 2. THE MAP BOUNDARY ---
BOUNDARY_X = 300 
NUM_SECTIONS = 5
SECTION_HEIGHT = SCREEN_HEIGHT // NUM_SECTIONS  # Each section is 140 pixels high

# --- PLAYER VARIABLES ---
player_x = 150.0  # Starts safe inside the green zone
player_y = 350.0
player_w = 16
player_h = 10
player_vx = 0.0
player_vy = 0.0
player_angle = 0.0
rotation_speed = 4.0
acceleration_power = 0.07
translation_power = 0.07

# Create the surface for the player block
player_surface = pygame.Surface((player_w, player_h), pygame.SRCALPHA)
pygame.draw.rect(player_surface, PLAYER_COLOR, (0, 0, player_w, player_h))


# --- POLICE CAR CLASS (NO AI LOGIC) ---
class PoliceCar:
    def __init__(self, id_num, start_y):
        # Spawns them right along the boundary wall line
        self.x = BOUNDARY_X + 15
        self.y = start_y
        self.w = 14
        self.h = 14
        self.id = id_num
        self.speed = 1.2
        
        # --- YOUR CUSTOM VARIABLES GO BELOW HERE ---
        # (e.g., self.target_y, self.state, self.timer, etc.)
        

# Instantiate your 3 raw police objects separated along the line
police_squad = [
    PoliceCar(1, 150),
    PoliceCar(2, 350),
    PoliceCar(3, 550)
]


# 3. MAIN GAME LOOP
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # --- CONTROLS (Momentum Space Drift) ---
    keys = pygame.key.get_pressed()
    
    # Rotation (Arrow keys tilt the heading angle)
    if keys[pygame.K_LEFT]:  player_angle += rotation_speed
    if keys[pygame.K_RIGHT]: player_angle -= rotation_speed
    
    # Directional Thrust relative to rotation angle
    rad = math.radians(player_angle)
    if keys[pygame.K_UP]:
        player_vx += math.cos(rad) * acceleration_power
        player_vy -= math.sin(rad) * acceleration_power
    if keys[pygame.K_DOWN]:
        player_vx -= math.cos(rad) * acceleration_power
        player_vy += math.sin(rad) * acceleration_power

    # Absolute Translation (WASD strafes independent of direction)
    if keys[pygame.K_w]: player_vy -= translation_power  
    if keys[pygame.K_s]: player_vy += translation_power  
    if keys[pygame.K_a]: player_vx -= translation_power  
    if keys[pygame.K_d]: player_vx += translation_power  

    # --- APPLY PHYSICS AND MOVEMENT ---
    player_x += player_vx
    player_y += player_vy

    # Screen boundary bouncing parameters
    if player_x < 0 or player_x > SCREEN_WIDTH:  player_vx *= -1
    if player_y < 0 or player_y > SCREEN_HEIGHT: player_vy *= -1


    # ========================================================
    #  WRITE YOUR OWN PATROL, CHASE, AND AI LOGIC DOWN HERE!
    # ========================================================
    
    # Useful tip to get you started:
    # is_inside_restricted = player_x > BOUNDARY_X
    
    # ========================================================


    # --- DRAWING / RENDERING ---
    screen.fill(BACKGROUND_COLOR)

    # 1. Draw Green Safe Zone
    pygame.draw.rect(screen, SAFE_ZONE_COLOR, (0, 0, BOUNDARY_X, SCREEN_HEIGHT))
    
    # 2. Draw Section Divider Lines (Faint horizontal visual markers)
    for i in range(1, NUM_SECTIONS):
        pygame.draw.line(screen, (25, 30, 35), (BOUNDARY_X, i * SECTION_HEIGHT), (SCREEN_WIDTH, i * SECTION_HEIGHT), 1)

    # 3. Draw Main Orange Threat Fence Line
    pygame.draw.line(screen, RESTRICTED_LINE_COLOR, (BOUNDARY_X, 0), (BOUNDARY_X, SCREEN_HEIGHT), 3)

    # 4. Draw the 3 Police Blocks
    for agent in police_squad:
        pygame.draw.rect(screen, POLICE_COLOR, pygame.Rect(int(agent.x), int(agent.y), agent.w, agent.h))

    # 5. Rotate and Draw the Player
    rotated_player = pygame.transform.rotate(player_surface, player_angle)
    new_rect = rotated_player.get_rect(center=(int(player_x), int(player_y)))
    screen.blit(rotated_player, new_rect.topleft)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()