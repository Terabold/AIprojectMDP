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
        self.air_time = 0  # Start grounded
        self.grounded = True  # Start grounded
        self.was_grounded = True  # Prevent initial landing sound
        self.facing_right = True
        self.jump_available = True
        self.action = ''
        self.death = False 
        self.finishLevel = False 
        self.respawn = False
        self.was_colliding_wall = False
        self.wall_contact_time = 0
        self.wall_momentum_active = False
        
        # Jump state tracking
        self.jump_state = 'none'  # 'anticipation', 'rising', 'peak', 'falling', 'landing', 'none'
        self.jump_anticipation_timer = 0
        self.peak_timer = 0
        self.landing_timer = 0
        
        self.set_action('run')

    def reset(self):
        self._initialize()
        #self.game.scroll = list(self.start_pos).copy()
    
    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])
    
    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets['player/' + self.action].copy()
    
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
            if self.grounded:
                move_dir = int(keys['right']) - int(keys['left'])
                # If changing direction sharply: snap velocity to zero
                if move_dir != 0 and ((self.velocity[0] > 0 and move_dir < 0) or (self.velocity[0] < 0 and move_dir > 0)):
                    self.velocity[0] = 0
                # Now apply acceleration/deceleration as normal
                self.velocity[0] += move_dir * PLAYER_SPEED
                x_acceleration = (1 - DECCELARATION) if move_dir == 0 else (1 - ACCELERAION)
                self.velocity[0] = max(-MAX_X_SPEED, min(MAX_X_SPEED, self.velocity[0] * x_acceleration))
            else:
                # Air control (keep as is)
                move_dir = int(keys['right']) - int(keys['left'])
                self.velocity[0] += move_dir * PLAYER_SPEED
                x_acceleration = (1 - DECCELARATION) if move_dir == 0 else (1 - ACCELERAION)
                self.velocity[0] = max(-MAX_X_SPEED, min(MAX_X_SPEED, self.velocity[0] * x_acceleration))

            gravity = GRAVITY_DOWN if self.velocity[1] > 0 and not keys['jump'] else GRAVITY_UP
            self.velocity[1] = max(-MAX_Y_SPEED, min(MAX_Y_SPEED, self.velocity[1] + gravity))
        else:
            self.velocity[0] = 0    
            self.velocity[1] = 0
            
        self.pos[0] += self.velocity[0]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if self.velocity[0] > 0:
                    entity_rect.right = rect.left
                    self.collisions['right'] = True
                if self.velocity[0] < 0:
                    entity_rect.left = rect.right
                    self.collisions['left'] = True
                self.pos[0] = entity_rect.x
        
        self.pos[1] += self.velocity[1]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if self.velocity[1] > 0:
                    entity_rect.bottom = rect.top
                    self.collisions['down'] = True
                if self.velocity[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collisions['up'] = True
                self.pos[1] = entity_rect.y

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

        if keys['right'] and not keys['left']:
            self.facing_right = True
        elif keys['left'] and not keys['right']:
            self.facing_right = False

        if self.collisions['right'] or self.collisions['left']:
            self.velocity[0] = 0
        if self.collisions['down'] or self.collisions['up']:
            self.velocity[1] = 0

        # Check if we just hit a wall this frame
        just_hit_right = self.collisions['right'] and not self.was_colliding_wall and self.facing_right
        just_hit_left = self.collisions['left'] and not self.was_colliding_wall and not self.facing_right

        if just_hit_right or just_hit_left:
            self.sfx['collide'].play()

        self.was_colliding_wall = self.collisions['left'] or self.collisions['right']

        self.air_time += 1
        if self.collisions['down']:
            self.air_time = 0
        self.grounded = self.air_time <= 4

        # Play land sound effect when landing (but not during startup)
        if self.grounded and not self.was_grounded and self.velocity[1] >= 0:
            self.sfx['land'].play()
            self.jump_state = 'landing'
            self.landing_timer = 0

        # Reset jump availability when key is released
        if not keys['jump']:
            self.jump_available = True
        
        # Handle jumps - Only if jump is available and key is pressed
        elif keys['jump'] and self.jump_available:
            self.jump_available = False
            
            # Wall jump logic
            if not self.grounded and (self.collisions['left'] or self.collisions['right']):
                self.velocity[1] = -WALLJUMP_Y_SPEED
                if self.collisions['right']:
                    self.velocity[0] = -WALLJUMP_X_SPEED
                    self.sfx['wall_jump_right'].play()
                elif self.collisions['left']:
                    self.velocity[0] = WALLJUMP_X_SPEED
                    self.sfx['wall_jump_left'].play()
                self.jump_state = 'rising'
            
            # Regular jump logic
            elif self.grounded:
                self.velocity[1] = -JUMP_SPEED
                self.air_time = 5
                self.grounded = False
                self.sfx['jump'].play()
                self.jump_state = 'anticipation'
                self.jump_anticipation_timer = 0
        
        # Update jump state timers
        if self.jump_state == 'anticipation':
            self.jump_anticipation_timer += 1
            if self.jump_anticipation_timer > 3:  # Short anticipation
                self.jump_state = 'rising'
        elif self.jump_state == 'landing':
            self.landing_timer += 1
            if self.landing_timer > 8:  # Landing animation duration
                self.jump_state = 'none'

        # Update jump states based on velocity
        if not self.grounded and self.jump_state not in ['landing']:
            if self.velocity[1] < -1:  # Rising
                if self.jump_state != 'rising':
                    self.jump_state = 'rising'
            elif abs(self.velocity[1]) <= 1:  # At peak
                if self.jump_state != 'peak':
                    self.jump_state = 'peak'
                    self.peak_timer = 0
                self.peak_timer += 1
                if self.peak_timer > 6:  # Peak duration
                    self.jump_state = 'falling'
            elif self.velocity[1] > 1:  # Falling
                if self.jump_state != 'falling':
                    self.jump_state = 'falling'

        # Wall slide, wall slide momentum logic
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
        
        # Set animation based on state
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