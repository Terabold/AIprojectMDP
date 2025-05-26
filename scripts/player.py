from scripts.constants import *
import random
import pygame
import numpy as np

class Player:
    def __init__(self, game, pos, size, sfx):
        self.game = game
        self.start_pos = pos
        self.size = size
        self.hitbox_width = size[0] 
        self.hitbox_height = size[1] * 0.75
        self.sfx = sfx
        self._initialize()

    def _initialize(self):
        self.pos = np.array(self.start_pos, dtype=float)
        self.velocity = np.zeros(2)
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        self.air_time = 5
        self.grounded = False
        self.facing_right = True
        self.jump_available = True
        self.coyote_time = 0
        self.action = ''
        self.death = False 
        self.finishLevel = False 
        self.respawn = False
        self.was_colliding_wall = False
        self.wall_contact_time = 0
        self.wall_momentum_active = False
        
        # Enhanced animation state tracking
        self.animation_state = 'idle'
        self.animation_priority = 0
        self.animation_lock_timer = 0
        self.jump_phase = 'none'  # 'anticipation', 'rising', 'peak', 'falling', 'landing'
        self.jump_frame_counter = 0
        self.was_grounded_last_frame = True
        self.landing_buffer = 0
        
        self.set_action('run')

    def reset(self):
        self._initialize()
        
    def rect(self):
        hitbox_x = self.pos[0] + (self.size[0] - self.hitbox_width) // 2
        hitbox_y = self.pos[1] + self.size[1] - self.hitbox_height
        
        return pygame.Rect(hitbox_x, hitbox_y, self.hitbox_width, self.hitbox_height)
    
    def set_action(self, action, priority=0, lock_frames=0):
        if action != self.action or priority > self.animation_priority:
            if self.animation_lock_timer <= 0 or priority > self.animation_priority:
                self.action = action
                self.animation = self.game.assets['player/' + self.action].copy()
                self.animation_priority = priority
                self.animation_lock_timer = lock_frames
    
    def can_coyote_jump(self):
        return self.coyote_time <= COYOTE_TIME and not self.grounded
    
    def update_jump_animation_state(self):
        if self.jump_phase == 'anticipation':
            self.jump_frame_counter += 1
            # Complete anticipation after 2 frames
            if self.jump_frame_counter >= 2:
                self.jump_phase = 'rising'
                self.jump_frame_counter = 0
                self.velocity[1] = -JUMP_SPEED  # Apply jump force after anticipation
                
        elif self.jump_phase == 'rising':
            # Transition to peak when upward velocity slows down
            if self.velocity[1] >= -2:  # -2 is the velocity threshold for peak transition
                self.jump_phase = 'peak'
                self.jump_frame_counter = 0
                
        elif self.jump_phase == 'peak':
            self.jump_frame_counter += 1
            # Stay in peak for minimum 6 frames OR until clearly falling
            if self.jump_frame_counter >= 6 and self.velocity[1] > 1:
                self.jump_phase = 'falling'
                self.jump_frame_counter = 0
                
        elif self.jump_phase == 'falling':
            # Transition to landing when hitting ground
            if self.grounded or self.collisions['down']:
                self.jump_phase = 'landing'
                self.jump_frame_counter = 0
                self.landing_buffer = 8  # Show landing animation for 8 frames
                
        elif self.jump_phase == 'landing':
            self.landing_buffer -= 1
            # Complete landing sequence
            if self.landing_buffer <= 0:
                self.jump_phase = 'none'
                self.jump_frame_counter = 0

    def determine_animation_state(self):
        # Highest priority: Death
        if self.death:
            return 'death', 100, 0
        
        if self.finishLevel:
            return 'finish', 100, 0
        
        # High priority: Wall interactions when not grounded
        if (self.collisions['left'] or self.collisions['right']):
            if self.velocity[1] > 0 and not self.grounded:
                return 'wallslide', 80, 0
            else:
                return 'wallcollide', 80, 0 
        
        if self.jump_phase == 'landing':
            return 'jump_landing', 95, 10  # Lock for 10 frames
    
        # Peak animation priority
        if self.jump_phase == 'peak':
            return 'jump_peak', 90, 0
        
        # High priority: Jump phases
        if self.jump_phase != 'none':
            if self.jump_phase == 'anticipation':
                return 'jump_anticipation', 90, 0
            elif self.jump_phase == 'rising':
                return 'jump_rising', 90, 0
            elif self.jump_phase == 'peak':
                return 'jump_peak', 90, 0
            elif self.jump_phase == 'falling':
                return 'jump_falling', 90, 0
            elif self.jump_phase == 'landing':
                return 'jump_landing', 90, 0
        
        # Medium priority: Air states (when not in jump sequence)
        if not self.grounded:
            if self.velocity[1] < -1:
                return 'jump_rising', 70, 0  # Default rising animation
            elif self.velocity[1] > 1:
                return 'jump_falling', 70, 0  # Default falling animation
            else:
                return 'jump_peak', 70, 0  # Default peak animation
        
        # Low priority: Ground movement
        if abs(self.velocity[0]) > 0.5:
            return 'run', 10, 0
        else:
            return 'idle', 5, 0

    def update(self, tilemap, keys, countframes):
        # Update animation timer
        if self.animation_lock_timer > 0:
            self.animation_lock_timer -= 1
        
        self.animation.update()

        if tilemap.is_below_map(self.pos):
            self.death = True
            self.velocity = [0, 0]
            self.set_action('death', 100)
            return 

        if countframes > 40:
            return 
        
        # Store previous grounded state
        self.was_grounded_last_frame = self.grounded
        
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        if not self.death and not self.finishLevel:
            self.velocity[0] += (int(keys['right']) - int(keys['left'])) * PLAYER_SPEED
            x_acceleration = (1 - DECCELARATION) if int(keys['right']) - int(keys['left']) == 0 else (1 - ACCELERAION)
            self.velocity[0] = max(-MAX_X_SPEED, min(MAX_X_SPEED, self.velocity[0] * x_acceleration))

            gravity = GRAVITY_DOWN if self.velocity[1] > 0 and not keys['jump'] else GRAVITY_UP
            self.velocity[1] = max(-MAX_Y_SPEED, min(MAX_Y_SPEED, self.velocity[1] + gravity))
        else:
            self.velocity[0] = 0    
            self.velocity[1] = 0
            
        # HORIZONTAL MOVEMENT AND COLLISION
        self.pos[0] += self.velocity[0]
        entity_rect = self.rect()  # Use the smaller hitbox
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if self.velocity[0] > 0:
                    # When moving right, align hitbox right edge with tile left edge
                    entity_rect.right = rect.left
                    self.collisions['right'] = True
                if self.velocity[0] < 0:
                    # When moving left, align hitbox left edge with tile right edge
                    entity_rect.left = rect.right
                    self.collisions['left'] = True
                
                self.pos[0] = entity_rect.x - (self.size[0] - self.hitbox_width) // 2
        
        # VERTICAL MOVEMENT AND COLLISION
        self.pos[1] += self.velocity[1]
        entity_rect = self.rect()  
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if self.velocity[1] > 0:
                    # When falling, align hitbox bottom with tile top
                    entity_rect.bottom = rect.top
                    self.collisions['down'] = True
                if self.velocity[1] < 0:
                    # When jumping up, align hitbox top with tile bottom
                    entity_rect.top = rect.bottom
                    self.collisions['up'] = True

                self.pos[1] = entity_rect.y - (self.size[1] - self.hitbox_height)

        entity_rect = self.rect()  
        for rect, tile_info in tilemap.interactive_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                tile_type = tile_info[0]
                if tile_type in ['spikes', 'saws', 'kill']:
                    self.death = True 
                    self.velocity = [0, 0]
                    self.set_action('death', 100)
                    return
                elif tile_type == 'finish':
                    self.finishLevel = True

        # Update facing direction
        if keys['right'] and not keys['left']:
            self.facing_right = True
        elif keys['left'] and not keys['right']:
            self.facing_right = False

        # Apply collision effects
        if self.collisions['right'] or self.collisions['left']:
            self.velocity[0] = 0
        if self.collisions['down'] or self.collisions['up']:
            self.velocity[1] = 0
        if (self.collisions['left'] or self.collisions['right']) and self.grounded:
            self.velocity[0] = 0

        # Wall collision sound
        now_colliding_wall = self.collisions['left'] or self.collisions['right']
        if now_colliding_wall and not self.was_colliding_wall:  
            random.choice(self.sfx['collide']).play()
        self.was_colliding_wall = now_colliding_wall

        # Update grounded state and air time
        self.air_time += 1
        was_grounded = self.grounded
        
        if self.collisions['down']:
            self.air_time = 0
            self.coyote_time = 0
        
        self.grounded = self.air_time <= 4
        
        # Update coyote time
        if was_grounded and not self.grounded:
            self.coyote_time = 0
        elif not self.grounded:
            self.coyote_time += 1

        # Reset jump availability when key is released
        if not keys['jump']:
            self.jump_available = True
        
        # Handle jumps with animation phases
        elif keys['jump'] and self.jump_available:
            self.jump_available = False
            
            # Wall jump logic
            if not self.grounded and (self.collisions['left'] or self.collisions['right']):
                self.velocity[1] = -WALLJUMP_Y_SPEED
                if self.collisions['right']: 
                    self.velocity[0] = -WALLJUMP_X_SPEED
                if self.collisions['left']: 
                    self.velocity[0] = WALLJUMP_X_SPEED
                
                # Start wall jump animation sequence
                self.jump_phase = 'rising'
                self.jump_frame_counter = 0
                random.choice(self.sfx['jump']).play()
            
            # Regular jump logic (includes coyote jump)
            elif (self.grounded or self.can_coyote_jump()) and self.game.buffer_times['jump'] <= PLAYER_BUFFER:
                # Start jump anticipation phase
                self.jump_phase = 'anticipation'
                self.jump_frame_counter = 0
                
                self.velocity[1] = -JUMP_SPEED
                self.air_time = 5
                self.grounded = False
                self.coyote_time = COYOTE_TIME + 1
                random.choice(self.sfx['jump']).play()
        
        # Update jump animation state machine
        self.update_jump_animation_state()
        
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
        
        # Cut jump short if key released
        if not keys['jump'] and self.velocity[1] < 0:
            self.velocity[1] = 0
        
        # Update animation based on current state
        animation_state, priority, lock_frames = self.determine_animation_state()
        self.set_action(animation_state, priority, lock_frames)
        
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