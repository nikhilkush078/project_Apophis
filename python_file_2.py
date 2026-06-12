import pygame
import random
import math
import sys

# 1. INITIALIZE PYGAME
pygame.init()

SCREEN_WIDTH = 900
SCREEN_HEIGHT = 700
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Space Infiltration - Intercept Network")

clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 16, bold=True)

# Colors
BACKGROUND_COLOR = (10, 10, 15)
SAFE_ZONE_COLOR = (15, 25, 20, 120)    
RESTRICTED_LINE_COLOR = (255, 140, 0) 
PLAYER_COLOR = (0, 255, 200)
POLICE_COLOR = (50, 50, 255)
CHASE_COLOR = (255, 50, 50)
ALERT_COLOR = (255, 165, 0)
MOTHERSHIP_COLOR = (140, 40, 210)     
MOTHERSHIP_CHASE = (255, 0, 255)      
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
LIGHT_BLUE = (173, 216, 230)
RED = (255, 0, 0)
LASER_COLOR = (255, 0, 100)

# Resource & Rock Asteroid Colors
RES_FUEL_COLOR = (40, 220, 80)
RES_WATER_COLOR = (0, 180, 255)
RES_ROCK_COLOR = (110, 70, 70)

# Asteroid Variant Palette Colors
ASTEROID_GRAY_1 = (100, 102, 105)
ASTEROID_GRAY_2 = (140, 142, 145)
ASTEROID_GRAY_3 = (75, 77, 80)

#====================================================================

# --- WORLD SIZE EXPANSION ---
WORLD_WIDTH = SCREEN_WIDTH * 5
WORLD_HEIGHT = SCREEN_HEIGHT * 5

# --- CAMERA & VIRTUAL SCREEN CONFIG ---
VIRTUAL_WIDTH = int(SCREEN_WIDTH / 2.5)   
VIRTUAL_HEIGHT = int(SCREEN_HEIGHT / 2.5)

# --- SIMPLIFIED UNIVERSAL STATIC STARFIELD ---
STATIC_STAR_BACKGROUND = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
STATIC_STAR_BACKGROUND.fill(BACKGROUND_COLOR)

NUM_STARS = 60 
for _ in range(NUM_STARS):
    rx = random.randint(0, VIRTUAL_WIDTH - 1)
    ry = random.randint(0, VIRTUAL_HEIGHT - 1)
    star_color = (200, 220, 255, random.randint(120, 200)) 
    STATIC_STAR_BACKGROUND.set_at((rx, ry), star_color)

# --- TIME AND ZOOM SYSTEM CONFIG ---
elapsed_time = 0
max_time = 10  

virtual_screen = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))

camera_x = 0
camera_y = 0

fule = 100
water_indicator = 20
caught_timer = 0

my_rect = pygame.Rect(735, 100, 50, 50)
my_rect_2 = pygame.Rect(800, 400, 50, 75)

#====================================================================

# Transparency Layers (Using SRCALPHA for blending overlays)
CIRCLE_SURFACE = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
SAFE_ZONE_SURFACE = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)

# --- IMAGE LOADING & CONFIGURATION ---
try:
    player_img_base = pygame.image.load("player.png").convert_alpha()
    police_img_base = pygame.image.load("police.png").convert_alpha()
    mothership_img_base = pygame.image.load("mother_ship.png").convert_alpha()
    fuel_img_base = pygame.image.load("fule.png").convert_alpha()
    water_img_base = pygame.image.load("water.png").convert_alpha()
    rock_img_base = pygame.image.load("rock.png").convert_alpha()
except pygame.error as e:
    print(f"Error loading assets: {e}")
    sys.exit()

# --- THE MAP BOUNDARY & ASTEROID BELT SETUP ---
BOUNDARY_X = 300 
NUM_SECTIONS = 5 * 5  
SECTION_HEIGHT = WORLD_HEIGHT // NUM_SECTIONS  

asteroid_belt = []
current_belt_y = 0

while current_belt_y < WORLD_HEIGHT:
    spacing_gap = random.randint(50, 100)
    current_belt_y += spacing_gap
    
    if current_belt_y >= WORLD_HEIGHT:
        break
        
    asteroid_selection = random.choice(["astroid_type_1", "astroid_type_2", "astroid_type_3"])
    
    if asteroid_selection == "astroid_type_1":
        aw, ah = 12, 10
        color = ASTEROID_GRAY_1
    elif asteroid_selection == "astroid_type_2":
        aw, ah = 8, 8
        color = ASTEROID_GRAY_2
    else:
        aw, ah = 15, 14
        color = ASTEROID_GRAY_3
        
    ax = BOUNDARY_X - (aw // 2)
    
    asteroid_node = {
        "rect": pygame.Rect(ax, current_belt_y, aw, ah),
        "color": color,
        "type": asteroid_selection
    }
    asteroid_belt.append(asteroid_node)
    current_belt_y += ah

# --- 4x4 GRID SETUP ---
GRID_COLS = 4 * 5
GRID_ROWS = 4 * 5
GRID_CELL_WIDTH = (WORLD_WIDTH - BOUNDARY_X) // GRID_COLS
GRID_CELL_HEIGHT = WORLD_HEIGHT // GRID_ROWS

grid_data = [[0 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]

high_value_cells = []
cells_visited_this_run = [] 
was_inside_last_frame = False

# --- SPAWN 10 RESOURCE & ROCK MINING ASTEROIDS ---
resource_asteroids = []
types_pool = ["fuel", "water", "rock"]
for _ in range(10):
    atype = random.choice(types_pool)
    ax = random.randint(BOUNDARY_X + 100, WORLD_WIDTH - 120)
    ay = random.randint(100, WORLD_HEIGHT - 120)
    aw = random.randint(35, 60)
    ah = random.randint(35, 60)
    
    # Scale resource specific textures on creation based on their dynamic rectangle size
    if atype == "fuel":
        scaled_img = pygame.transform.scale(fuel_img_base, (aw, ah))
    elif atype == "water":
        scaled_img = pygame.transform.scale(water_img_base, (aw, ah))
    else:
        scaled_img = pygame.transform.scale(rock_img_base, (aw, ah))
        
    resource_asteroids.append({
        "rect": pygame.Rect(ax, ay, aw, ah),
        "type": atype,
        "image": scaled_img
    })

# --- PLAYER VARIABLES ---
player_x = 150.0  
player_y = 350.0
player_w = 20
player_h = 20
player_vx = 0.0
player_vy = 0.0
player_angle = 0.0

rotation_speed = 4.0 / 5.0          
acceleration_power = 0.07 / 5.0     
translation_power = 0.07 / 5.0      

# Pre-scale the raw player texture according to structural boundaries
player_surface = pygame.transform.scale(player_img_base, (player_w, player_h))

# --- CIRCLE PARAMETERS ---
CAPTURE_RADIUS = 100   
LOSE_RADIUS = 200  
CIRCLE_ALPHA = 50     

# --- LASER BULLET SYSTEM ---
police_bullets = []
LASER_SPEED = 1.0
FIRE_COOLDOWN = 120  

# --- HEAVY MOTHERSHIPS CONFIG ---
MOTHERSHIP_SIZE = 42            
MOTHERSHIP_CAPTURE_RADIUS = 250  
MOTHERSHIP_LOSE_RADIUS = 350
MOTHERSHIP_SPEED = 0.3 / 5.0     

# Pre-scale mothership texture asset
mothership_surface = pygame.transform.scale(mothership_img_base, (MOTHERSHIP_SIZE, MOTHERSHIP_SIZE))

mothership_positions = [
    (BOUNDARY_X + 200, 200),                                   
    (WORLD_WIDTH - 250, 200),                                  
    (BOUNDARY_X + 200, WORLD_HEIGHT - 300),                   
    (WORLD_WIDTH - 250, WORLD_HEIGHT - 300),                  
    (WORLD_WIDTH // 2, WORLD_HEIGHT // 2),                    
    (WORLD_WIDTH // 2, 400),                                   
    (WORLD_WIDTH // 2, WORLD_HEIGHT - 500),                   
    (BOUNDARY_X + 500, WORLD_HEIGHT // 2),                    
    (WORLD_WIDTH - 600, WORLD_HEIGHT // 2)                    
]

motherships = []
for i, pos in enumerate(mothership_positions):
    m_ship = {
        "id": i,
        "x": float(pos[0]),
        "y": float(pos[1]),
        "center_y": float(pos[1]),
        "direction": random.choice([-1, 1]),
        "chasing": False,
        "shoot_cooldown": random.randint(0, FIRE_COOLDOWN)
    }
    motherships.append(m_ship)

# --- DYNAMIC POLICE FLEET ---
police_w = 15   
police_h = 15  
police_speed = 1.5 / 5.0  

# Pre-scale police fleet texture asset
police_surface = pygame.transform.scale(police_img_base, (police_w, police_h))

police_fleet = []
for row_idx in range(GRID_ROWS):
    row_center_y = (row_idx * GRID_CELL_HEIGHT) + (GRID_CELL_HEIGHT // 2)
    assigned_mother = random.choice(motherships)
    
    role = "boundary" if row_idx % 2 == 0 else "escort"
    
    police_car = {
        "role": role,
        "x": BOUNDARY_X + 15,
        "y": float(row_center_y),
        "center_y": float(row_center_y),
        "timer": random.uniform(0.0, 5.0), 
        "direction": random.choice([-1, 1]),
        "chasing": False,
        "target_x": None,
        "target_y": None,
        "shoot_cooldown": random.randint(0, FIRE_COOLDOWN),
        "mother_id": assigned_mother["id"],
        "pattern_type": random.choice(["ellipse", "figure_8", "diamond"]),
        "orbit_angle": random.uniform(0, 2 * math.pi),
        "orbit_radius_x": random.randint(70, 150),    
        "orbit_radius_y": random.randint(50, 110),
        "orbit_speed": random.uniform(0.004, 0.009)    
    }
    police_fleet.append(police_car)

swap_ticks = 0.0
SWAP_INTERVAL = 7.0  

last_known_predict_x = None
last_known_predict_y = None

# Pre-scale the recharge surfaces using the context-appropriate asset mappings
fuel_base_station_img = pygame.transform.scale(fuel_img_base, (my_rect.width, my_rect.height))
water_base_station_img = pygame.transform.scale(water_img_base, (my_rect_2.width, my_rect_2.height))

# MAIN GAME LOOP
running = True
game_over = False
while running:
    frame_ms = clock.tick(60)
    dt = frame_ms / 1000.0
    dw = frame_ms / 1000.0
    
    water_indicator = max(0, water_indicator - (dw * 0.05))
    swap_ticks += dt
    
    for m in motherships:
        if m["shoot_cooldown"] > 0: m["shoot_cooldown"] -= 1
        
    for police in police_fleet:
        police["timer"] += 0.05
        if police["role"] == "escort":
            police["orbit_angle"] += police["orbit_speed"]
        if police["shoot_cooldown"] > 0:
            police["shoot_cooldown"] -= 1
            
    if swap_ticks >= SWAP_INTERVAL:
        swap_ticks = 0.0
        escort_pool = [p for p in police_fleet if p["role"] == "escort"]
        if len(escort_pool) > 0:
            migrating_unit = random.choice(escort_pool)
            alt_mothers = [m for m in motherships if m["id"] != migrating_unit["mother_id"]]
            if alt_mothers:
                migrating_unit["mother_id"] = random.choice(alt_mothers)["id"]

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # --- CONTROLS ---
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:  player_angle += rotation_speed
    if keys[pygame.K_RIGHT]: player_angle -= rotation_speed
    
    rad = math.radians(player_angle)
    if keys[pygame.K_UP]:
        player_vx += math.cos(rad) * acceleration_power
        player_vy -= math.sin(rad) * acceleration_power
        fule = max(0, fule - (acceleration_power * 0.5))
    if keys[pygame.K_DOWN]:
        player_vx -= math.cos(rad) * acceleration_power
        player_vy += math.sin(rad) * acceleration_power
        fule = max(0, fule - (acceleration_power * 0.5))

    if keys[pygame.K_w]:
        player_vy -= translation_power
        fule = max(0, fule - (translation_power * 0.5))
    if keys[pygame.K_s]:
        player_vy += translation_power
        fule = max(0, fule - (translation_power * 0.5))
    if keys[pygame.K_a]:
        player_vx -= translation_power
        fule = max(0, fule - (translation_power * 0.5))
    if keys[pygame.K_d]:
        player_vx += translation_power
        fule = max(0, fule - (translation_power * 0.5))

    # Apply velocity and drag friction
    player_x += player_vx
    player_y += player_vy
    player_vx *= 0.98
    player_vy *= 0.98

    if player_x < 0 or player_x > WORLD_WIDTH:  player_vx *= -1
    if player_y < 0 or player_y > WORLD_HEIGHT: player_vy *= -1
    player_x = max(0, min(player_x, WORLD_WIDTH))
    player_y = max(0, min(player_y, WORLD_HEIGHT))

    # --- CRITICAL COLLISION ENGINE: ASTEROID BELT IMPACT ---
    player_current_rect = pygame.Rect(player_x, player_y, player_w, player_h)
    for roid in asteroid_belt:
        if player_current_rect.colliderect(roid["rect"]):
            game_over = True
            break

    # --- MINING ASTEROIDS & ROCK COLLISION LOGIC ---
    for res_ast in resource_asteroids:
        if player_current_rect.colliderect(res_ast["rect"]):
            if res_ast["type"] == "rock":
                game_over = True
                break
            elif res_ast["type"] == "fuel":
                fule = min(100.0, fule + dt * 8.0)  
            elif res_ast["type"] == "water":
                water_indicator = min(100.0, water_indicator + dt * 8.0)  

    # --- UPDATE LASER BULLETS & CHECK COLLISIONS ---
    for bullet in police_bullets[:]:
        bullet["x"] += bullet["vx"]
        bullet["y"] += bullet["vy"]
        
        if bullet["x"] < 0 or bullet["x"] > WORLD_WIDTH or bullet["y"] < 0 or bullet["y"] > WORLD_HEIGHT:
            police_bullets.remove(bullet)
            continue
            
        bullet_rect = pygame.Rect(bullet["x"], bullet["y"], 2, 2)
        if bullet_rect.colliderect(player_current_rect):
            game_over = True
            break

    # --- INFILTRATION RUN TRACKING ---
    is_inside_now = player_x > BOUNDARY_X

    if is_inside_now and not game_over:
        current_col = int((player_x - BOUNDARY_X) // GRID_CELL_WIDTH)
        current_row = int(player_y // GRID_CELL_HEIGHT)
        
        if 0 <= current_col < GRID_COLS and 0 <= current_row < GRID_ROWS:
            cell_coordinates = (current_row, current_col)
            if cell_coordinates not in cells_visited_this_run:
                cells_visited_this_run.append(cell_coordinates)
        was_inside_last_frame = True

    # Write path history to grid memory even if player crashes inside the zone
    if (was_inside_last_frame and not is_inside_now) or (game_over and was_inside_last_frame):
        for index in range(len(cells_visited_this_run)):
            row, col = cells_visited_this_run[index]
            run_multiplier = (index + 1) * 10
            grid_data[row][col] += run_multiplier
            
        row_totals = [sum(grid_data[r]) for r in range(GRID_ROWS)]
        min_value = min(row_totals)
        target_row_index = row_totals.index(min_value)
        target_pixel_y = (target_row_index * GRID_CELL_HEIGHT) + (GRID_CELL_HEIGHT // 2)
        
        for police in police_fleet:
            if police["role"] == "boundary":
                if police["center_y"] < target_pixel_y: police["center_y"] += 30
                elif police["center_y"] > target_pixel_y: police["center_y"] -= 30

        high_value_cells = []
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                if grid_data[r][c] > 0:
                    cx = BOUNDARY_X + (c * GRID_CELL_WIDTH) + (GRID_CELL_WIDTH // 2)
                    cy = (r * GRID_CELL_HEIGHT) + (GRID_CELL_HEIGHT // 2)
                    high_value_cells.append((grid_data[r][c], cx, cy))
        high_value_cells.sort(key=lambda item: item[0], reverse=True)

        cells_visited_this_run = []
        was_inside_last_frame = False

    # --- FLEET CHASE & PREDICTIVE TARGETING CALCULATIONS ---
    any_car_chasing = False
    
    # 1. Process Motherships Threat States
    for m in motherships:
        dist_to_mother = math.hypot(player_x - m["x"], player_y - m["y"])
        
        if not m["chasing"] and dist_to_mother < MOTHERSHIP_CAPTURE_RADIUS and is_inside_now:
            m["chasing"] = True
        elif m["chasing"] and (dist_to_mother > MOTHERSHIP_LOSE_RADIUS or not is_inside_now):
            m["chasing"] = False
            
        if m["chasing"]:
            any_car_chasing = True
            if m["x"] < player_x: m["x"] += MOTHERSHIP_SPEED
            if m["x"] > player_x: m["x"] -= MOTHERSHIP_SPEED
            if m["y"] < player_y: m["y"] += MOTHERSHIP_SPEED
            if m["y"] > player_y: m["y"] -= MOTHERSHIP_SPEED
            
            if m["shoot_cooldown"] == 0:
                t_intercept = dist_to_mother / LASER_SPEED
                pred_mx = player_x + (player_vx * t_intercept)
                pred_my = player_y + (player_vy * t_intercept)
                
                base_angle = math.atan2(pred_my - m["y"], pred_mx - m["x"])
                for variance in [-0.12, 0.0, 0.12]:  
                    police_bullets.append({
                        "x": m["x"] + (MOTHERSHIP_SIZE // 2),
                        "y": m["y"] + (MOTHERSHIP_SIZE // 2),
                        "vx": math.cos(base_angle + variance) * LASER_SPEED,
                        "vy": math.sin(base_angle + variance) * LASER_SPEED
                    })
                m["shoot_cooldown"] = FIRE_COOLDOWN + 30
        else:
            m["y"] += MOTHERSHIP_SPEED * m["direction"] * 2.0
            if m["y"] > m["center_y"] + 150: m["direction"] = -1
            elif m["y"] < m["center_y"] - 150: m["direction"] = 1

    # 2. Process Mixed Fleet Entities
    for police in police_fleet:
        dist_to_player = math.hypot(player_x - police["x"], player_y - police["y"])
        
        if police["role"] == "escort":
            my_mother = next(m for m in motherships if m["id"] == police["mother_id"])
            should_chase = (is_inside_now and dist_to_player < CAPTURE_RADIUS) or (my_mother["chasing"] and is_inside_now)
        else:
            should_chase = is_inside_now and dist_to_player < CAPTURE_RADIUS

        if not police["chasing"] and should_chase:
            police["chasing"] = True
        elif police["chasing"] and (dist_to_player > LOSE_RADIUS or not is_inside_now):
            police["chasing"] = False
            
        if police["chasing"]:
            any_car_chasing = True
            if police["x"] < player_x: police["x"] += police_speed
            if police["x"] > player_x: police["x"] -= police_speed
            if police["y"] < player_y: police["y"] += police_speed
            if police["y"] > player_y: police["y"] -= police_speed
            
            if dist_to_player <= LOSE_RADIUS and police["shoot_cooldown"] == 0:
                time_to_target = dist_to_player / LASER_SPEED
                predicted_target_x = player_x + (player_vx * time_to_target)
                predicted_target_y = player_y + (player_vy * time_to_target)
                angle_to_prediction = math.atan2(predicted_target_y - police["y"], predicted_target_x - police["x"])
                
                police_bullets.append({
                    "x": police["x"], "y": police["y"],
                    "vx": math.cos(angle_to_prediction) * LASER_SPEED,
                    "vy": math.sin(angle_to_prediction) * LASER_SPEED
                })
                police["shoot_cooldown"] = FIRE_COOLDOWN
        else:
            if police["role"] == "boundary":
                if police["x"] < BOUNDARY_X + 15: police["x"] += police_speed
                if police["x"] > BOUNDARY_X + 15: police["x"] -= police_speed
                
                police["y"] += police_speed * police["direction"]
                if police["y"] > police["center_y"] + 50: police["direction"] = -1
                if police["y"] < police["center_y"] - 50: police["direction"] = 1
                
            elif police["role"] == "escort":
                my_mother = next(m for m in motherships if m["id"] == police["mother_id"])
                m_center_x = my_mother["x"] + (MOTHERSHIP_SIZE // 2)
                m_center_y = my_mother["y"] + (MOTHERSHIP_SIZE // 2)
                
                ang = police["orbit_angle"]
                rx = police["orbit_radius_x"]
                ry = police["orbit_radius_y"]
                
                if police["pattern_type"] == "ellipse":
                    target_ox = m_center_x + math.cos(ang) * rx
                    target_oy = m_center_y + math.sin(ang) * ry
                elif police["pattern_type"] == "figure_8":
                    target_ox = m_center_x + math.sin(ang) * rx
                    target_oy = m_center_y + math.sin(2 * ang) * (ry * 0.7)
                elif police["pattern_type"] == "diamond":
                    norm_ang = ang % (2 * math.pi)
                    if norm_ang < math.pi / 2:
                        t = norm_ang / (math.pi / 2)
                        dx, dy = 1.0 - t, t
                    elif norm_ang < math.pi:
                        t = (norm_ang - math.pi / 2) / (math.pi / 2)
                        dx, dy = -t, 1.0 - t
                    elif norm_ang < 3 * math.pi / 2:
                        t = (norm_ang - math.pi) / (math.pi / 2)
                        dx, dy = -1.0 + t, -t
                    else:
                        t = (norm_ang - 3 * math.pi / 2) / (math.pi / 2)
                        dx, dy = t, -1.0 + t
                    target_ox = m_center_x + dx * rx
                    target_oy = m_center_y + dy * ry

                police["x"] += (target_ox - police["x"]) * 0.0125
                police["y"] += (target_oy - police["y"]) * 0.0125

    if any_car_chasing and is_inside_now:
        caught_timer += dt
    else:
        caught_timer = 0

    if caught_timer > 15:
        game_over = True

    if any_car_chasing:
        elapsed_time += dt
    else:
        elapsed_time = 0
    
    remaining_time = max_time - elapsed_time
    if remaining_time < 0: remaining_time = 0

    # --- CAMERA TRACKING MATH ---
    camera_x = player_x - (VIRTUAL_WIDTH // 2)
    camera_y = player_y - (VIRTUAL_HEIGHT // 2)
    camera_x = max(0, min(camera_x, WORLD_WIDTH - VIRTUAL_WIDTH))
    camera_y = max(0, min(camera_y, WORLD_HEIGHT - VIRTUAL_HEIGHT))

    # --- PREDICTIVE INTERCEPT SYSTEM ---
    predict_lookahead = 60
    predict_x = player_x + (player_vx * predict_lookahead)
    predict_y = player_y + (player_vy * predict_lookahead)
    predict_x = max(BOUNDARY_X, min(WORLD_WIDTH, predict_x))
    predict_y = max(0, min(WORLD_HEIGHT, predict_y))

    if any_car_chasing:
        last_known_predict_x = predict_x
        last_known_predict_y = predict_y

    # --- RECHARGES (STATIONARY BASE STATIONS) ---
    if player_current_rect.colliderect(my_rect) and fule < 100:
        fule += dt 
    if player_current_rect.colliderect(my_rect_2) and water_indicator < 100:
        water_indicator += dt

    # =====================================================================
    # --- RENDER VIRTUAL ENVIRONMENT LAYER ---
    # =====================================================================
    virtual_screen.blit(STATIC_STAR_BACKGROUND, (0, 0))
    CIRCLE_SURFACE.fill((0, 0, 0, 0)) 
    SAFE_ZONE_SURFACE.fill((0, 0, 0, 0))

    pygame.draw.rect(SAFE_ZONE_SURFACE, SAFE_ZONE_COLOR, (0 - camera_x, 0 - camera_y, BOUNDARY_X, WORLD_HEIGHT))
    virtual_screen.blit(SAFE_ZONE_SURFACE, (0, 0))
    
    #for i in range(1, NUM_SECTIONS):
        #pygame.draw.line(virtual_screen, (25, 30, 35), (0 - camera_x, i * SECTION_HEIGHT - camera_y), (WORLD_WIDTH - camera_x, i * SECTION_HEIGHT - camera_y), 1)

    # Render Grid Boxes
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            cell_left = BOUNDARY_X + (col * GRID_CELL_WIDTH)
            cell_top = row * GRID_CELL_HEIGHT
            cell_value = grid_data[row][col]
            
            cam_cell_left = cell_left - camera_x
            cam_cell_top = cell_top - camera_y

            if (-GRID_CELL_WIDTH <= cam_cell_left <= VIRTUAL_WIDTH) and (-GRID_CELL_HEIGHT <= cam_cell_top <= VIRTUAL_HEIGHT):
                if cell_value > 0:
                    temp_surface = pygame.Surface((GRID_CELL_WIDTH, GRID_CELL_HEIGHT))
                    opacity = min(int(cell_value * 1.5), 160)
                    temp_surface.set_alpha(opacity)
                    temp_surface.fill((255, 0, 0))
                   # virtual_screen.blit(temp_surface, (cam_cell_left, cam_cell_top))

                   # text_surface = font.render(str(cell_value), True, (255, 255, 255))
                    #virtual_screen.blit(text_surface, (cam_cell_left + (GRID_CELL_WIDTH//2) - 12, cam_cell_top + (GRID_CELL_HEIGHT//2) - 8))

                #if is_inside_now and (row, col) in cells_visited_this_run:
                    #pygame.draw.rect(virtual_screen, (255, 255, 255), (cam_cell_left, cam_cell_top, GRID_CELL_WIDTH, GRID_CELL_HEIGHT), 2)
                #else:
                    #pygame.draw.rect(virtual_screen, (40, 40, 50), (cam_cell_left, cam_cell_top, GRID_CELL_WIDTH, GRID_CELL_HEIGHT), 1)

    # Render Edge Boundary Asteroids
    for roid in asteroid_belt:
        r_box = roid["rect"]
        cam_rx = r_box.x - camera_x
        cam_ry = r_box.y - camera_y
        if (-r_box.width <= cam_rx <= VIRTUAL_WIDTH) and (-r_box.height <= cam_ry <= VIRTUAL_HEIGHT):
            pygame.draw.rect(virtual_screen, roid["color"], (cam_rx, cam_ry, r_box.width, r_box.height))

    # Render Resource & Rock Asteroids (Replaced rectangles with scaled image sprites)
    for res_ast in resource_asteroids:
        r_box = res_ast["rect"]
        cam_rx = r_box.x - camera_x
        cam_ry = r_box.y - camera_y
        if (-r_box.width <= cam_rx <= VIRTUAL_WIDTH) and (-r_box.height <= cam_ry <= VIRTUAL_HEIGHT):
            virtual_screen.blit(res_ast["image"], (cam_rx, cam_ry))
            lbl = res_ast["type"].upper()
            lbl_surface = font.render(lbl, True, WHITE)
            virtual_screen.blit(lbl_surface, (cam_rx + 4, cam_ry + (r_box.height // 2) - 6))

    # Render Stationary Recharge Bases using configured image layers
    virtual_screen.blit(fuel_base_station_img, (my_rect.x - camera_x, my_rect.y - camera_y))
    virtual_screen.blit(water_base_station_img, (my_rect_2.x - camera_x, my_rect_2.y - camera_y))

    for bullet in police_bullets:
        cam_bx = int(bullet["x"] - camera_x)
        cam_by = int(bullet["y"] - camera_y)
        if (0 <= cam_bx <= VIRTUAL_WIDTH) and (0 <= cam_by <= VIRTUAL_HEIGHT):
            pygame.draw.rect(virtual_screen, LASER_COLOR, (cam_bx, cam_by, 2, 2))

    # --- RENDERING DETECTION RANGE OVERLAY RINGS ---
    for m in motherships:
        cam_mx = int(m["x"] + (MOTHERSHIP_SIZE // 2) - camera_x)
        cam_my = int(m["y"] + (MOTHERSHIP_SIZE // 2) - camera_y)
        if (-MOTHERSHIP_LOSE_RADIUS <= cam_mx <= VIRTUAL_WIDTH + MOTHERSHIP_LOSE_RADIUS) and (-MOTHERSHIP_LOSE_RADIUS <= cam_my <= VIRTUAL_HEIGHT + MOTHERSHIP_LOSE_RADIUS):
            pygame.draw.circle(CIRCLE_SURFACE, (130, 40, 240, 15), (cam_mx, cam_my), MOTHERSHIP_CAPTURE_RADIUS)
            if m["chasing"]:
                pygame.draw.circle(CIRCLE_SURFACE, (0, 120, 255, 20), (cam_mx, cam_my), MOTHERSHIP_LOSE_RADIUS)

    for police in police_fleet:
        cam_cx = int(police["x"] - camera_x)
        cam_cy = int(police["y"] - camera_y)
        if (-LOSE_RADIUS <= cam_cx <= VIRTUAL_WIDTH + LOSE_RADIUS) and (-LOSE_RADIUS <= cam_cy <= VIRTUAL_HEIGHT + LOSE_RADIUS):
            pygame.draw.circle(CIRCLE_SURFACE, (255, 0, 0, CIRCLE_ALPHA), (cam_cx, cam_cy), CAPTURE_RADIUS)
            pygame.draw.circle(CIRCLE_SURFACE, (255, 50, 50, 80), (cam_cx, cam_cy), CAPTURE_RADIUS, 1) 
            if police["chasing"]:
                pygame.draw.circle(CIRCLE_SURFACE, (0, 100, 255, CIRCLE_ALPHA // 2), (cam_cx, cam_cy), LOSE_RADIUS)
                pygame.draw.circle(CIRCLE_SURFACE, (50, 150, 255, 90), (cam_cx, cam_cy), LOSE_RADIUS, 1)

    virtual_screen.blit(CIRCLE_SURFACE, (0, 0))

    # Draw Heavy Motherships (Replaced rectangles with scaled image sprites)
    for m in motherships:
        cam_mx = int(m["x"] - camera_x)
        cam_my = int(m["y"] - camera_y)
        if (-MOTHERSHIP_SIZE <= cam_mx <= VIRTUAL_WIDTH) and (-MOTHERSHIP_SIZE <= cam_my <= VIRTUAL_HEIGHT):
            virtual_screen.blit(mothership_surface, (cam_mx, cam_my))

    # Draw Police Entities (Replaced rectangles with scaled image sprites)
    for police in police_fleet:
        cam_px = int(police["x"] - camera_x)
        cam_py = int(police["y"] - camera_y)
        if (-police_w <= cam_px <= VIRTUAL_WIDTH) and (-police_h <= cam_py <= VIRTUAL_HEIGHT):
            virtual_screen.blit(police_surface, (cam_px, cam_py))

    # Draw Player (Replaced color layer calculation with rotation of loaded player image asset)
    if not game_over:
        rotated_player = pygame.transform.rotate(player_surface, player_angle)
        new_rect = rotated_player.get_rect(center=(int(player_x - camera_x), int(player_y - camera_y)))
        virtual_screen.blit(rotated_player, new_rect.topleft)

    # =====================================================================
    # --- STRETCH CANVAS AND DRAW SCREEN HUD ---
    # =====================================================================
    scaled_surface = pygame.transform.scale(virtual_screen, (SCREEN_WIDTH, SCREEN_HEIGHT))
    screen.blit(scaled_surface, (0, 0))

    # HUD indicators
    fule_indicator_rect = pygame.Rect(10, 10, int(fule * 2), 20)
    pygame.draw.rect(screen, GREEN, fule_indicator_rect)
    pygame.draw.rect(screen, WHITE, (10, 10, 200, 20), 2)
    text_surface = font.render(f"Fuel: {fule:.2f}", True, RED)
    screen.blit(text_surface, (10, 12))

    water_indicator_rect = pygame.Rect(10, 40, int(water_indicator * 2), 20)
    pygame.draw.rect(screen, LIGHT_BLUE, water_indicator_rect)
    pygame.draw.rect(screen, WHITE, (10, 40, 200, 20), 2)
    text_surface = font.render(f"Water: {water_indicator:.2f}", True, RED)
    screen.blit(text_surface, (10, 42))

    if any_car_chasing and remaining_time > 0:
        time_bar_width = 150
        time_bar_height = 5
        time_bar_x = 10
        time_bar_y = 65
        time_remaining_ratio = max(0.0, min(1.0, remaining_time / max_time))
        pygame.draw.rect(screen, BLUE, (time_bar_x, time_bar_y, int(time_bar_width * time_remaining_ratio), time_bar_height))

    # --- GAME OVER SCREEN HUD ---
    if game_over:
        game_over_font = pygame.font.SysFont("Arial", 48, bold=True)
        game_over_surface = game_over_font.render("GAME OVER", True, RED)
        restart_font = pygame.font.SysFont("Arial", 24, bold=True)
        restart_surface = restart_font.render("Press R to Restart or Q to Quit", True, WHITE)
        
        screen.blit(game_over_surface, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 50))
        screen.blit(restart_surface, (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT // 2 + 30))
        
        pygame.display.flip()
        
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    waiting = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        game_over = False
                        caught_timer = 0
                        fule = 100
                        water_indicator = 20
                        player_x = 150.0
                        player_y = 350.0
                        player_vx = 0.0
                        player_vy = 0.0
                        player_angle = 0.0
                        police_bullets = [] 
                    
                        for idx, police in enumerate(police_fleet):
                            police["chasing"] = False
                            police["target_x"] = None
                            police["target_y"] = None
                            police["shoot_cooldown"] = random.randint(0, FIRE_COOLDOWN)
                            if police["role"] == "escort":
                                police["mother_id"] = random.choice(motherships)["id"]
                            
                        for m in motherships:
                            m["chasing"] = False
                            m["shoot_cooldown"] = random.randint(0, FIRE_COOLDOWN)
                            
                        cells_visited_this_run = [] # Clears uncommitted layout steps only
                        waiting = False
                    elif event.key == pygame.K_q:
                        running = False
                        waiting = False

    pygame.display.flip()

pygame.quit()
sys.exit()