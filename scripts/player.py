from scripts.constants import *
import pygame

class Player:
    def __init__(self, game, pos, size, sfx):
        self.game = game
        self.start_pos = pos
        self.size = size
        self.sfx = sfx
        self._initialize()

    def _initialize(self):
        self.pos = list(self.start_pos)
        self.velocity = [0, 0]
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        self.air_time = 0
        self.grounded = True
        self.was_grounded = True
        self.facing_right = True
        self.jump_available = True
        self.action = ''
        self.death = False 
        self.finishLevel = False 
        self.respawn = False
        self.was_colliding_wall = False
        self.wall_contact_time = 0
        self.wall_momentum_active = False
        
        # Enhanced wall jump setback system
        self.walljump_setback_timer = 0
        self.walljump_setback_direction = 0  # -1 for left, 1 for right, 0 for none
        self.super_speed_active = False  # Flag for when using higher speed cap
        
        # Jump state tracking
        self.jump_state = 'none'
        self.jump_anticipation_timer = 0
        self.peak_timer = 0
        self.landing_timer = 0
        
        self.set_action('run')

    def reset(self):
        self._initialize()
        #self.game.scroll = list(self.start_pos).copy()
    
    def rect(self):
        return pygame.Rect(round(self.pos[0]), round(self.pos[1]), self.size[0], self.size[1])
    
    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets['player/' + self.action].copy()

    # Enhanced movement logic with speed caps and wall jump setback
    def update(self, tilemap, keys, countdeathframes):
        self.animation.update()

        if tilemap.is_below_map(self.pos):
            self.death = True
            self.velocity = [0, 0]
            self.set_action('death')
            return 

        if countdeathframes > 40 or self.finishLevel:
            return 
        
        # Store previous grounded state for landing detection
        self.was_grounded = self.grounded
        
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        
        if not self.death and not self.finishLevel:
            # Update wall jump setback timer
            if self.walljump_setback_timer > 0:
                self.walljump_setback_timer -= 1
                if self.walljump_setback_timer <= 0:
                    self.walljump_setback_direction = 0
                    self.super_speed_active = False
            
            # Enhanced horizontal movement with dynamic speed caps
            if self.grounded:
                move_dir = int(keys['right']) - int(keys['left'])
                
                # Sharp direction change: snap velocity to zero
                if move_dir != 0 and ((self.velocity[0] > 0 and move_dir < 0) or (self.velocity[0] < 0 and move_dir > 0)):
                    self.velocity[0] = 0
                
                # Apply wall jump setback force
                if self.walljump_setback_timer > 0:
                    setback_force = self.walljump_setback_direction * WALLJUMP_X_SPEED
                    setback_strength = (self.walljump_setback_timer / WALLJUMP_SETBACK_FRAMES)
                    self.velocity[0] += setback_force * setback_strength * WALLJUMP_SETBACK_DECAY
                else:
                    self.velocity[0] += move_dir * PLAYER_SPEED
                
                # Apply acceleration/deceleration
                x_acceleration = (1 - DECELERATION) if move_dir == 0 else (1 - ACCELERATION)
                self.velocity[0] = self.velocity[0] * x_acceleration
                
            else:  # Air movement
                move_dir = int(keys['right']) - int(keys['left'])
                
                # Apply wall jump setback force in air
                if self.walljump_setback_timer > 0:
                    setback_force = self.walljump_setback_direction * WALLJUMP_X_SPEED * 0.5  # Reduced in air
                    setback_strength = (self.walljump_setback_timer / WALLJUMP_SETBACK_FRAMES)
                    self.velocity[0] += setback_force * setback_strength * WALLJUMP_SETBACK_DECAY
                else:
                    self.velocity[0] += move_dir * PLAYER_SPEED
                
                x_acceleration = (1 - DECELERATION) if move_dir == 0 else (1 - ACCELERATION)
                self.velocity[0] = self.velocity[0] * x_acceleration
            
            # Apply appropriate speed cap
            current_max_speed = SUPER_MAX_X_SPEED if self.super_speed_active else MAX_X_SPEED
            self.velocity[0] = max(-current_max_speed, min(current_max_speed, self.velocity[0]))
            
            # Enhanced gravity system
            gravity = GRAVITY_DOWN if self.velocity[1] > 0 and not keys['jump'] else GRAVITY_UP
            self.velocity[1] = max(-MAX_Y_SPEED, min(MAX_Y_SPEED, self.velocity[1] + gravity))
        else:
            self.velocity[0] = 0    
            self.velocity[1] = 0
            
        # X-axis collision (unchanged)
        if abs(self.velocity[0]) > 0.01:
            self.pos[0] += self.velocity[0]
            entity_rect = self.rect()
            
            collision_occurred = False
            for rect in tilemap.physics_rects_around(self.pos):
                if entity_rect.colliderect(rect):
                    collision_occurred = True
                    if self.velocity[0] > 0:
                        entity_rect.right = rect.left
                        self.collisions['right'] = True
                    if self.velocity[0] < 0:
                        entity_rect.left = rect.right
                        self.collisions['left'] = True
                    self.pos[0] = entity_rect.x
                    break
            
            if collision_occurred:
                self.velocity[0] = 0
        
        # Y-axis collision (unchanged)
        if abs(self.velocity[1]) > 0.01:
            self.pos[1] += self.velocity[1]
            entity_rect = self.rect()
            
            collision_occurred = False
            for rect in tilemap.physics_rects_around(self.pos):
                if entity_rect.colliderect(rect):
                    collision_occurred = True
                    if self.velocity[1] > 0:
                        entity_rect.bottom = rect.top
                        self.collisions['down'] = True
                    if self.velocity[1] < 0:
                        entity_rect.top = rect.bottom
                        self.collisions['up'] = True
                    self.pos[1] = entity_rect.y
                    break
            
            if collision_occurred:
                self.velocity[1] = 0

        # Interactive tiles (unchanged)
        entity_rect = self.rect()
        for rect, tile_info in tilemap.interactive_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                tile_type = tile_info[0]
                if tile_type in ['spikes', 'kill']:
                    self.death = True 
                    self.velocity = [0, 0]
                    self.set_action('death')
                    return
                elif tile_type == 'finish':
                    self.finishLevel = True

        # Update facing direction
        if keys['right'] and not keys['left']:
            self.facing_right = True
        elif keys['left'] and not keys['right']:
            self.facing_right = False

        # Collision response
        if self.collisions['right'] or self.collisions['left']:
            self.velocity[0] = 0
        if self.collisions['down'] or self.collisions['up']:
            self.velocity[1] = 0

        # Wall collision sound
        just_hit_right = self.collisions['right'] and not self.was_colliding_wall and self.facing_right
        just_hit_left = self.collisions['left'] and not self.was_colliding_wall and not self.facing_right

        if just_hit_right or just_hit_left:
            self.sfx['collide'].play()

        self.was_colliding_wall = self.collisions['left'] or self.collisions['right']

        # Grounded state
        self.air_time += 1
        if self.collisions['down']:
            self.air_time = 0
        self.grounded = self.air_time <= 4

        # Landing sound and state
        if self.grounded and not self.was_grounded and self.velocity[1] >= 0:
            self.sfx['land'].play()
            self.jump_state = 'landing'
            self.landing_timer = 0
            # Reset wall jump setback when landing
            self.walljump_setback_timer = 0
            self.walljump_setback_direction = 0
            self.super_speed_active = False

        # Jump input handling
        if not keys['jump']:
            self.jump_available = True
        elif keys['jump'] and self.jump_available:
            self.jump_available = False
            
            # Enhanced wall jump with greater setback
            if not self.grounded and (self.collisions['left'] or self.collisions['right']):
                self.velocity[1] = -WALLJUMP_Y_SPEED
                
                if self.collisions['right']:
                    self.velocity[0] = -WALLJUMP_X_SPEED
                    self.walljump_setback_direction = -1  # Push left
                    self.sfx['wall_jump_right'].play()
                elif self.collisions['left']:
                    self.velocity[0] = WALLJUMP_X_SPEED
                    self.walljump_setback_direction = 1   # Push right
                    self.sfx['wall_jump_left'].play()
                
                # Activate enhanced setback system
                self.walljump_setback_timer = WALLJUMP_SETBACK_FRAMES
                self.super_speed_active = True 
                self.jump_state = 'rising'
            
            # Regular jump
            elif self.grounded:
                self.velocity[1] = -JUMP_SPEED
                self.air_time = 5
                self.grounded = False
                self.sfx['jump'].play()
                self.jump_state = 'anticipation'
                self.jump_anticipation_timer = 0
        
        # Jump state management (unchanged)
        if self.jump_state == 'anticipation':
            self.jump_anticipation_timer += 1
            if self.jump_anticipation_timer > 3:
                self.jump_state = 'rising'
        elif self.jump_state == 'landing':
            self.landing_timer += 1
            if self.landing_timer > 8:
                self.jump_state = 'none'

        # Update jump states based on velocity
        if not self.grounded and self.jump_state not in ['landing']:
            if self.velocity[1] < -1:
                if self.jump_state != 'rising':
                    self.jump_state = 'rising'
            elif abs(self.velocity[1]) <= 1:
                if self.jump_state != 'peak':
                    self.jump_state = 'peak'
                    self.peak_timer = 0
                self.peak_timer += 1
                if self.peak_timer > 6:
                    self.jump_state = 'falling'
            elif self.velocity[1] > 1:
                if self.jump_state != 'falling':
                    self.jump_state = 'falling'

        # Wall slide mechanics (unchanged)
        if not self.grounded and (self.collisions['left'] or self.collisions['right']):
            if not self.was_colliding_wall:
                self.wall_contact_time = 0
                if self.velocity[1] < 0:
                    self.wall_momentum_active = True
            
            self.wall_contact_time += 1
            
            if self.wall_momentum_active and self.wall_contact_time <= WALL_MOMENTUM_FRAMES:
                self.velocity[1] *= WALL_MOMENTUM_PRESERVE
            else:
                self.wall_momentum_active = False
                if self.velocity[1] > 0:  
                    self.velocity[1] = min(WALLSLIDE_SPEED, self.velocity[1])
        
        # Cut jump short
        if not keys['jump'] and self.velocity[1] < 0:
            self.velocity[1] = 0
        
        # Animation state (unchanged)
        if self.death:
            self.set_action('death') 
        elif self.finishLevel:
            self.set_action('finish')
        elif (self.collisions['left'] or self.collisions['right']) and self.velocity[1] > 0 and not self.grounded:
            self.set_action('wallslide')
        elif (self.collisions['left'] or self.collisions['right']):
            self.set_action('wallcollide')
        elif self.jump_state == 'anticipation':
            self.set_action('jump_anticipation')
        elif self.jump_state == 'rising':
            self.set_action('jump_rising')
        elif self.jump_state == 'peak':
            self.set_action('jump_peak')
        elif self.jump_state == 'falling':
            self.set_action('jump_falling')
        elif self.jump_state == 'landing':
            self.set_action('jump_landing')
        elif abs(self.velocity[0]) > 0.5:
            self.set_action('run')
        else:
            self.set_action('idle')
        
    def render(self, surf, offset=(0, 0)):
        # Get the original image
        image = self.animation.img()
        
        # Flip the image horizontally if facing left
        if not self.facing_right:
            image = pygame.transform.flip(image, True, False)
        
        # Get the rectangle of the rotated image
        image_rect = image.get_rect(center=(self.pos[0] + self.size[0] // 2 - offset[0],
                                                self.pos[1] + self.size[1] // 2 - offset[1]))
        # Draw the rotated image
        surf.blit(image, image_rect)

    def render_ai(self, surf, offset=(0, 0)):
        # Draw a simple rectangle for AI mode
        rect = pygame.Rect(self.pos[0] - offset[0], self.pos[1] - offset[1], self.size[0], self.size[1])
        pygame.draw.rect(surf, (255, 215, 0), rect)    