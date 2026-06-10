import pygame
import random
import math

# 1. INITIALIZE PYGAME
pygame.init()

SCREEN_WIDTH = 900
SCREEN_HEIGHT = 700
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Space Infiltration - Predictive Intercept Network")

clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 16)

# Colors
BACKGROUND_COLOR = (10, 10, 15)
SAFE_ZONE_COLOR = (15, 25, 20)       
RESTRICTED_LINE_COLOR = (255, 140, 0) 
PLAYER_COLOR = (0, 255, 200)
POLICE_COLOR = (50, 50, 255)
CHASE_COLOR = (255, 50, 50)
ALERT_COLOR = (255, 165, 0)

# Transparency layer
CIRCLE_SURFACE = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

# --- THE MAP BOUNDARY ---
BOUNDARY_X = 300 
NUM_SECTIONS = 5
SECTION_HEIGHT = SCREEN_HEIGHT // NUM_SECTIONS  

# --- 4x4 GRID SETUP ---
GRID_COLS = 4
GRID_ROWS = 4
GRID_CELL_WIDTH = (SCREEN_WIDTH - BOUNDARY_X) // GRID_COLS
GRID_CELL_HEIGHT = SCREEN_HEIGHT // GRID_ROWS

grid_data = [
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0]
]

high_value_cells = []
cells_visited_this_run = [] 
was_inside_last_frame = False

# --- PLAYER VARIABLES ---
player_x = 150.0  
player_y = 350.0
player_w = 3   
player_h = 2   
player_vx = 0.0
player_vy = 0.0
player_angle = 0.0

rotation_speed = 4.0 / 5.0          
acceleration_power = 0.07 / 5.0     
translation_power = 0.07 / 5.0      

player_surface = pygame.Surface((player_w, player_h), pygame.SRCALPHA)
pygame.draw.rect(player_surface, PLAYER_COLOR, (0, 0, player_w, player_h))

# --- CIRCLE PARAMETERS ---
CAPTURE_RADIUS = 50   
LOSE_RADIUS = 150     
CIRCLE_ALPHA = 50     

# --- 4 SEPARATE POLICE VARIABLES ---
police_w = 3   
police_h = 3   
police_speed = 1.5 / 5.0  

p1_x = p2_x = p3_x = p4_x = BOUNDARY_X + 15

p1_center = 100.0
p2_center = 260.0
p3_center = 420.0
p4_center = 580.0

p1_y, p2_y, p3_y, p4_y = p1_center, p2_center, p3_center, p4_center

# Independent local surveillance timers / offsets for pacing inside cells
p1_timer = 0.0
p2_timer = 1.5
p3_timer = 3.0
p4_timer = 4.5

p1_dir = p2_dir = 1
p3_dir = p4_dir = -1

p1_chasing = False
p2_chasing = False
p3_chasing = False
p4_chasing = False

# Tracks the player's last known trajectory when escaping
last_known_predict_x = None
last_known_predict_y = None

# MAIN GAME LOOP
running = True
while running:
    clock.tick(60)
    p1_timer += 0.05
    p2_timer += 0.05
    p3_timer += 0.05
    p4_timer += 0.05
    
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
    if keys[pygame.K_DOWN]:
        player_vx -= math.cos(rad) * acceleration_power
        player_vy += math.sin(rad) * acceleration_power

    if keys[pygame.K_w]: player_vy -= translation_power  
    if keys[pygame.K_s]: player_vy += translation_power  
    if keys[pygame.K_a]: player_vx -= translation_power  
    if keys[pygame.K_d]: player_vx += translation_power  

    # Apply velocity and drag friction
    player_x += player_vx
    player_y += player_vy
    player_vx *= 0.98
    player_vy *= 0.98

    if player_x < 0 or player_x > SCREEN_WIDTH:  player_vx *= -1
    if player_y < 0 or player_y > SCREEN_HEIGHT: player_vy *= -1

    # --- INFILTRATION RUN TRACKING ---
    is_inside_now = player_x > BOUNDARY_X

    if is_inside_now:
        current_col = int((player_x - BOUNDARY_X) // GRID_CELL_WIDTH)
        current_row = int(player_y // GRID_CELL_HEIGHT)
        
        if 0 <= current_col < GRID_COLS and 0 <= current_row < GRID_ROWS:
            cell_coordinates = (current_row, current_col)
            if cell_coordinates not in cells_visited_this_run:
                cells_visited_this_run.append(cell_coordinates)
        was_inside_last_frame = True

    # TRIGGER: Crossed back out to safety!
    elif was_inside_last_frame and not is_inside_now:
        for index in range(len(cells_visited_this_run)):
            row, col = cells_visited_this_run[index]
            run_multiplier = (index + 1) * 10
            grid_data[row][col] += run_multiplier
            
        # Calibration shift for base centers
        row_totals = [sum(grid_data[0]), sum(grid_data[1]), sum(grid_data[2]), sum(grid_data[3])]
        min_value = min(row_totals)
        target_row_index = row_totals.index(min_value)
        target_pixel_y = (target_row_index * GRID_CELL_HEIGHT) + (GRID_CELL_HEIGHT // 2)
        
        if p1_center < target_pixel_y: p1_center += 30
        elif p1_center > target_pixel_y: p1_center -= 30
        if p2_center < target_pixel_y: p2_center += 30
        elif p2_center > target_pixel_y: p2_center -= 30
        if p3_center < target_pixel_y: p3_center += 30
        elif p3_center > target_pixel_y: p3_center -= 30
        if p4_center < target_pixel_y: p4_center += 30
        elif p4_center > target_pixel_y: p4_center -= 30

        # Extract and sort high value nodes
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


    # --- DUAL-CIRCLE DISTANCE CALCULATIONS ---
    dist_to_p1 = math.hypot(player_x - p1_x, player_y - p1_y)
    dist_to_p2 = math.hypot(player_x - p2_x, player_y - p2_y)
    dist_to_p3 = math.hypot(player_x - p3_x, player_y - p3_y)
    dist_to_p4 = math.hypot(player_x - p4_x, player_y - p4_y)

    # Capture Checks 
    if not p1_chasing and dist_to_p1 < CAPTURE_RADIUS and is_inside_now: p1_chasing = True
    elif p1_chasing and dist_to_p1 > LOSE_RADIUS: p1_chasing = False

    if not p2_chasing and dist_to_p2 < CAPTURE_RADIUS and is_inside_now: p2_chasing = True
    elif p2_chasing and dist_to_p2 > LOSE_RADIUS: p2_chasing = False

    if not p3_chasing and dist_to_p3 < CAPTURE_RADIUS and is_inside_now: p3_chasing = True
    elif p3_chasing and dist_to_p3 > LOSE_RADIUS: p3_chasing = False

    if not p4_chasing and dist_to_p4 < CAPTURE_RADIUS and is_inside_now: p4_chasing = True
    elif p4_chasing and dist_to_p4 > LOSE_RADIUS: p4_chasing = False

    any_car_chasing = p1_chasing or p2_chasing or p3_chasing or p4_chasing

    # --- PREDICTIVE INTERCEPT & STRATEGIC LAYOUT GENERATION ---
    # Look ahead 60 frames into the player's vector trail to predict intersection point
    predict_lookahead = 60
    predict_x = player_x + (player_vx * predict_lookahead)
    predict_y = player_y + (player_vy * predict_lookahead)
    
    # Clamp prediction inside the tracking boundary fields
    predict_x = max(BOUNDARY_X, min(SCREEN_WIDTH, predict_x))
    predict_y = max(0, min(SCREEN_HEIGHT, predict_y))

    if any_car_chasing:
        last_known_predict_x = predict_x
        last_known_predict_y = predict_y

    t1_x, t1_y = None, None
    t2_x, t2_y = None, None
    t3_x, t3_y = None, None
    t4_x, t4_y = None, None

    if len(high_value_cells) > 0:
        coords_only = [(item[1], item[2]) for item in high_value_cells]
        
        # Base skipped priority assignment setups
        if not p1_chasing and 0 < len(coords_only): t1_x, t1_y = coords_only[0]
        if not p2_chasing and 2 < len(coords_only): t2_x, t2_y = coords_only[2]
        if not p3_chasing and 4 < len(coords_only): t3_x, t3_y = coords_only[4]
        if not p4_chasing and 6 < len(coords_only): t4_x, t4_y = coords_only[6]
        
        if t2_x is None and not p2_chasing: t2_x, t2_y = coords_only[1 % len(coords_only)]
        if t3_x is None and not p3_chasing: t3_x, t3_y = coords_only[2 % len(coords_only)]
        if t4_x is None and not p4_chasing: t4_x, t4_y = coords_only[3 % len(coords_only)]

    # OVERRIDE: If a unit detects player tracking, non-chasing units encircle the PREDICTED vector coordinate instead!
    if any_car_chasing and len(high_value_cells) > 0:
        reinforce_nodes = [(item[1], item[2]) for item in high_value_cells]
        # Sort node centers based on how close they are to the player's FUTURE predicted path location
        reinforce_nodes.sort(key=lambda pt: math.hypot(pt[0] - predict_x, pt[1] - predict_y))
        
        # Distribute non-chasing interceptors sequentially to create an tracking wall barrier
        idx = 0
        if not p1_chasing: t1_x, t1_y = reinforce_nodes[idx % len(reinforce_nodes)]; idx += 1
        if not p2_chasing: t2_x, t2_y = reinforce_nodes[idx % len(reinforce_nodes)]; idx += 1
        if not p3_chasing: t3_x, t3_y = reinforce_nodes[idx % len(reinforce_nodes)]; idx += 1
        if not p4_chasing: t4_x, t4_y = reinforce_nodes[idx % len(reinforce_nodes)]; idx += 1

    # OVERRIDE: If player disappears but remains inside boundary, look near last known prediction track
    elif not any_car_chasing and is_inside_now and last_known_predict_x is not None and len(high_value_cells) > 0:
        search_nodes = [(item[1], item[2]) for item in high_value_cells]
        search_nodes.sort(key=lambda pt: math.hypot(pt[0] - last_known_predict_x, pt[1] - last_known_predict_y))
        
        idx = 0
        if t1_x is not None: t1_x, t1_y = search_nodes[idx % len(search_nodes)]; idx += 1
        if t2_x is not None: t2_x, t2_y = search_nodes[idx % len(search_nodes)]; idx += 1
        if t3_x is not None: t3_x, t3_y = search_nodes[idx % len(search_nodes)]; idx += 1
        if t4_x is not None: t4_x, t4_y = search_nodes[idx % len(search_nodes)]; idx += 1


    # --- EXECUTING ENGINE ACTIONS & LOCAL AREA SURVEILLANCE ---

    # --- POLICE CAR 1 ---
    if p1_chasing:
        if p1_x < player_x: p1_x += police_speed
        if p1_x > player_x: p1_x -= police_speed
        if p1_y < player_y: p1_y += police_speed
        if p1_y > player_y: p1_y -= police_speed
    elif (any_car_chasing or is_inside_now) and t1_x is not None:
        # Move toward destination node...
        dist = math.hypot(t1_x - p1_x, t1_y - p1_y)
        if dist > 15:  # Heading to position
            if p1_x < t1_x: p1_x += police_speed
            if p1_x > t1_x: p1_x -= police_speed
            if p1_y < t1_y: p1_y += police_speed
            if p1_y > t1_y: p1_y -= police_speed
        else:          # Arrived! Begin local dynamic circle surveillance orbit loop
            p1_x = t1_x + math.cos(p1_timer) * 12
            p1_y = t1_y + math.sin(p1_timer) * 12
    else:
        if p1_x < BOUNDARY_X + 15: p1_x += police_speed
        if p1_x > BOUNDARY_X + 15: p1_x -= police_speed
        p1_y += police_speed * p1_dir
        if p1_y > p1_center + 50: p1_dir = -1  
        if p1_y < p1_center - 50: p1_dir = 1   

    # --- POLICE CAR 2 ---
    if p2_chasing:
        if p2_x < player_x: p2_x += police_speed
        if p2_x > player_x: p2_x -= police_speed
        if p2_y < player_y: p2_y += police_speed
        if p2_y > player_y: p2_y -= police_speed
    elif (any_car_chasing or is_inside_now) and t2_x is not None:
        dist = math.hypot(t2_x - p2_x, t2_y - p2_y)
        if dist > 15:
            if p2_x < t2_x: p2_x += police_speed
            if p2_x > t2_x: p2_x -= police_speed
            if p2_y < t2_y: p2_y += police_speed
            if p2_y > t2_y: p2_y -= police_speed
        else:
            p2_x = t2_x + math.cos(p2_timer) * 12
            p2_y = t2_y + math.sin(p2_timer) * 12
    else:
        if p2_x < BOUNDARY_X + 15: p2_x += police_speed
        if p2_x > BOUNDARY_X + 15: p2_x -= police_speed
        p2_y += police_speed * p2_dir
        if p2_y > p2_center + 50: p2_dir = -1
        if p2_y < p2_center - 50: p2_dir = 1

    # --- POLICE CAR 3 ---
    if p3_chasing:
        if p3_x < player_x: p3_x += police_speed
        if p3_x > player_x: p3_x -= police_speed
        if p3_y < player_y: p3_y += police_speed
        if p3_y > player_y: p3_y -= police_speed
    elif (any_car_chasing or is_inside_now) and t3_x is not None:
        dist = math.hypot(t3_x - p3_x, t3_y - p3_y)
        if dist > 15:
            if p3_x < t3_x: p3_x += police_speed
            if p3_x > t3_x: p3_x -= police_speed
            if p3_y < t3_y: p3_y += police_speed
            if p3_y > t3_y: p3_y -= police_speed
        else:
            p3_x = t3_x + math.cos(p3_timer) * 12
            p3_y = t3_y + math.sin(p3_timer) * 12
    else:
        if p3_x < BOUNDARY_X + 15: p3_x += police_speed
        if p3_x > BOUNDARY_X + 15: p3_x -= police_speed
        p3_y += police_speed * p3_dir
        if p3_y > p3_center + 50: p3_dir = -1
        if p3_y < p3_center - 50: p3_dir = 1

    # --- POLICE CAR 4 ---
    if p4_chasing:
        if p4_x < player_x: p4_x += police_speed
        if p4_x > player_x: p4_x -= police_speed
        if p4_y < player_y: p4_y += police_speed
        if p4_y > player_y: p4_y -= police_speed
    elif (any_car_chasing or is_inside_now) and t4_x is not None:
        dist = math.hypot(t4_x - p4_x, t4_y - p4_y)
        if dist > 15:
            if p4_x < t4_x: p4_x += police_speed
            if p4_x > t4_x: p4_x -= police_speed
            if p4_y < t4_y: p4_y += police_speed
            if p4_y > t4_y: p4_y -= police_speed
        else:
            p4_x = t4_x + math.cos(p4_timer) * 12
            p4_y = t4_y + math.sin(p4_timer) * 12
    else:
        if p4_x < BOUNDARY_X + 15: p4_x += police_speed
        if p4_x > BOUNDARY_X + 15: p4_x -= police_speed
        p4_y += police_speed * p4_dir
        if p4_y > p4_center + 50: p4_dir = -1
        if p4_y < p4_center - 50: p4_dir = 1

    # Clear memory trackers if player completely makes it back out to green zone safely
    if not is_inside_now:
        last_known_predict_x = None
        last_known_predict_y = None


    # --- DRAWING / RENDERING ---
    screen.fill(BACKGROUND_COLOR)
    CIRCLE_SURFACE.fill((0, 0, 0, 0)) 

    # Draw Safe Zone
    pygame.draw.rect(screen, SAFE_ZONE_COLOR, (0, 0, BOUNDARY_X, SCREEN_HEIGHT))
    
    # Draw Section Dividers
    for i in range(1, NUM_SECTIONS):
        pygame.draw.line(screen, (25, 30, 35), (0, i * SECTION_HEIGHT), (SCREEN_WIDTH, i * SECTION_HEIGHT), 1)

    # Render 4x4 Grid Boxes
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            cell_left = BOUNDARY_X + (col * GRID_CELL_WIDTH)
            cell_top = row * GRID_CELL_HEIGHT
            cell_value = grid_data[row][col]
            
            if cell_value > 0:
                temp_surface = pygame.Surface((GRID_CELL_WIDTH, GRID_CELL_HEIGHT))
                opacity = min(int(cell_value * 1.5), 160)
                temp_surface.set_alpha(opacity)
                temp_surface.fill((255, 0, 0))
                screen.blit(temp_surface, (cell_left, cell_top))

                text_surface = font.render(str(cell_value), True, (255, 255, 255))
                screen.blit(text_surface, (cell_left + (GRID_CELL_WIDTH//2) - 12, cell_top + (GRID_CELL_HEIGHT//2) - 8))

            if is_inside_now and (row, col) in cells_visited_this_run:
                pygame.draw.rect(screen, (255, 255, 255), (cell_left, cell_top, GRID_CELL_WIDTH, GRID_CELL_HEIGHT), 2)
            else:
                pygame.draw.rect(screen, (40, 40, 50), (cell_left, cell_top, GRID_CELL_WIDTH, GRID_CELL_HEIGHT), 1)

    # Draw Boundary Line
    pygame.draw.line(screen, RESTRICTED_LINE_COLOR, (BOUNDARY_X, 0), (BOUNDARY_X, SCREEN_HEIGHT), 3)

    # --- RENDERING ALPHA VISIBILITY RINGS ---
    police_positions = [(p1_x, p1_y, p1_chasing), (p2_x, p2_y, p2_chasing), (p3_x, p3_y, p3_chasing), (p4_x, p4_y, p4_chasing)]
    for cx, cy, is_hunting in police_positions:
        # Inner Capture Circle (Red)
        pygame.draw.circle(CIRCLE_SURFACE, (255, 0, 0, CIRCLE_ALPHA), (int(cx), int(cy)), CAPTURE_RADIUS)
        pygame.draw.circle(CIRCLE_SURFACE, (255, 50, 50, 80), (int(cx), int(cy)), CAPTURE_RADIUS, 1) 
        
        # Outer Break Circle (Blue)
        if is_hunting:
            pygame.draw.circle(CIRCLE_SURFACE, (0, 100, 255, CIRCLE_ALPHA // 2), (int(cx), int(cy)), LOSE_RADIUS)
            pygame.draw.circle(CIRCLE_SURFACE, (50, 150, 255, 90), (int(cx), int(cy)), LOSE_RADIUS, 1)

    screen.blit(CIRCLE_SURFACE, (0, 0))

    # Color rendering mapping indicators (Red = Chase, Orange = Pincer Intercept Orbit, Blue = Normal Patrol)
    in_sweep_state = any_car_chasing or (not any_car_chasing and is_inside_now and len(high_value_cells) > 0)
    p1_render_color = CHASE_COLOR if p1_chasing else (ALERT_COLOR if in_sweep_state else POLICE_COLOR)
    p2_render_color = CHASE_COLOR if p2_chasing else (ALERT_COLOR if in_sweep_state else POLICE_COLOR)
    p3_render_color = CHASE_COLOR if p3_chasing else (ALERT_COLOR if in_sweep_state else POLICE_COLOR)
    p4_render_color = CHASE_COLOR if p4_chasing else (ALERT_COLOR if in_sweep_state else POLICE_COLOR)

    # Draw Police Entities
    pygame.draw.rect(screen, p1_render_color, pygame.Rect(int(p1_x), int(p1_y), police_w, police_h))
    pygame.draw.rect(screen, p2_render_color, pygame.Rect(int(p2_x), int(p2_y), police_w, police_h))
    pygame.draw.rect(screen, p3_render_color, pygame.Rect(int(p3_x), int(p3_y), police_w, police_h))
    pygame.draw.rect(screen, p4_render_color, pygame.Rect(int(p4_x), int(p4_y), police_w, police_h))

    # Draw Player
    rotated_player = pygame.transform.rotate(player_surface, player_angle)
    new_rect = rotated_player.get_rect(center=(int(player_x), int(player_y)))
    screen.blit(rotated_player, new_rect.topleft)

    pygame.display.flip()

pygame.quit()