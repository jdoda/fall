from settings import *
import os
import pygame
from pymunk import Vec2d
import pymunk as pm
from pygame.locals import *
from player import Player
import level
import gravityvolume
import particles


class game(object):

    def __init__(self):
        self.game_over = False
        self.camera_pos = Vec2d(0,0)
        
        self.on_screen = []
        self.player_collisions = []
        
        self.pan_left = False
        self.pan_right = False
        self.pan_up = False
        self.pan_down = False
        
        self.move_left = False
        self.move_right = False
        
        self.jump = False
        self.jump_time = 0
        
        self.last_on_ground = 0

        #Editor events
        self.mode_edit=False
        self.cmd_x=0
        self.cmd_y=0
        self.pos_start=None
        self.pos_end=None
        self.pos_mouse=None
        self.snap_radius=5.0
        self.dec_snap_radius=0
        self.inc_snap_radius=0
        self.level_path = os.path.join(RES, 'level.pickle')
        try:
            self.level = level.load_level(self.level_path)
        except:
            self.level = level.level()
            
        #PHYSICS!!!!
        pm.init_pymunk()
        self.space = pm.Space()
        self.space.gravity = Vec2d(0.0, 0.0)
        
        #the player
        self.player = Player(self)
        self.space.add(self.player.body, self.player.shape)

        for line in self.level.lines.iterkeys():
            self.space.add_static(self.level.lines[line].shape)

        for gvol in self.level.gvols:
            self.space.add_static(gvol.shape)

        #gravity polygons
        self.mode_gvol=False
        self.mode_grav_vec=False
        self.mode_grav_poly=False#check whether we've used this poly yet in list
        self.grav_set=False
        self.grav_vec=None
        self.poly_verts=[]
        #gravitate
        self.player.body.apply_force(Vec2d(0.0, -900 * self.player.body.mass))
        
        # make a test gravity volume
#        g = gravityvolume.GravityVolume([(-3000, 3000), (3000, 3000), (3000, -3000), (-3000, -3000)], (900, 900))
#        self.space.add_static(g.shape)

        self.particles = []
        self.level.emitters = []
        self.level.emitters.append(particles.Emitter((0,0), 0.05))
        
        #The screen to collide with what we need to draw
        self.screen_body = pm.Body(pm.inf, pm.inf)
        self.screen_shape = None
        self.set_screen_shape()
        
        self.space.set_default_collision_handler(None, self.ignore_collision, None, None)
        self.space.add_collision_handler(COLLTYPE_DEFAULT, COLLTYPE_PLAYER, None, self.collect_player_collisions, None, None)
        self.space.add_collision_handler(COLLTYPE_GRAVITY, COLLTYPE_PLAYER, None, gravityvolume.handle_collision, None, None)
        self.space.add_collision_handler(COLLTYPE_GRAVITY, COLLTYPE_PARTICLE, None, gravityvolume.handle_collision, None, None)
        self.space.add_collision_handler(COLLTYPE_LETHAL, COLLTYPE_PLAYER, None, self.handle_lethal_collision, None, None)
        self.space.add_collision_handler(COLLTYPE_LETHAL, COLLTYPE_PLAYER, None, self.handle_goal_collision, None, None)
        
    def set_screen_shape(self):
        if self.screen_shape:
            self.space.remove(self.screen_shape)
        pts = map(self.screen2world,[(0, 0), (WIDTH, 0), (WIDTH, HEIGHT), (0, HEIGHT)])
        self.screen_shape = pm.Poly(self.screen_body, pts)
        self.screen_shape.collision_type = COLLTYPE_SCREEN
        self.space.add(self.screen_shape)
        self.on_screen = []
    
    def ignore_collision(self, space, arbiter):
        s1, s2 = arbiter.shapes
        if s1 == self.screen_shape:
            self.on_screen.append(s2)
        elif s2 == self.screen_shape:
            self.on_screen.append(s1)
        return False
    
    def collect_player_collisions(self, space, arbiter):
        for c in arbiter.contacts:
            self.player_collisions.append(c.position)
        return True
    
    def handle_lethal_collision(self, space, arbiter):
        self.game_over = True
        return True
    
    def handle_goal_collision(self, space, arbiter):
        return True

    def world2screen(self,v):
        x,y = v
        w = WIDTH
        h = HEIGHT
        rx = self.camera_pos.x
        ry = self.camera_pos.y
        return (int((x-rx)+w/2), int(-1*(y-ry)+h/2))
        
    def screen2world(self,v):
        x,y = v
        w = WIDTH
        h = HEIGHT
        rx = self.camera_pos.x
        ry = self.camera_pos.y
        return Vec2d((x-w/2) + rx,-1*(y-h/2)+ry)
    
    def on_ground(self):
        if self.last_on_ground > 0:
            return True
        for c in self.player_collisions:
            body_loc = self.player.body.world_to_local(c)
            #p = self.player.shape.body.position
            #a = (c - p).get_angle_degrees()
            #if abs(a + 90) < PLAYER_GROUND_COLLISION_ANGLE:
            if abs(body_loc.y + 20) < 3:
                self.last_on_ground = DOWN_HILL_GRACE
                return True
        return False

    def handle_input(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                exit()
            elif e.type == pygame.KEYDOWN:
                if e.key == K_e:
                    self.mode_edit = not self.mode_edit
                elif self.mode_edit:
                    if e.key == K_a:
                        self.pan_left = True
                    elif e.key == K_d:
                        self.pan_right = True
                    elif e.key == K_w:
                        self.pan_up = True
                    elif e.key == K_s:
                        self.pan_down = True
                    elif e.key == K_COMMA :
                        self.dec_snap_radius= True
                    elif e.key == K_PERIOD :
                        self.inc_snap_radius = True
                    elif e.key == K_k :
                        self.level.save_level(self.level_path)
                    elif e.key == K_RETURN and self.mode_gvol:
                        self.mode_grav_vec = not self.mode_grav_vec
                        self.pos_start=None
                        self.pos_end=None
                    elif e.key == K_g :
                        if self.mode_gvol:#stopping gravity volume
                            self.grav_set=True
                        else: #starting gravity volume
                            self.mode_grav_vec=False
                            self.grav_set=False
                            self.poly_verts=[]
                            self.grav_vec=None
                        self.mode_gvol = not self.mode_gvol
                elif e.key == K_LEFT:
                    self.move_left = True
                elif e.key == K_RIGHT:
                    self.move_right = True
                elif e.key == K_SPACE and self.on_ground():
                    self.jump = True
                    self.jump_time = JUMP_TIME
                    self.player.jump()

            elif e.type == pygame.KEYUP:
                if self.mode_edit:
                    if e.key == K_a:
                        self.pan_left = False
                    elif e.key == K_d:
                        self.pan_right = False
                    elif e.key == K_w:
                        self.pan_up = False
                    elif e.key == K_s:
                        self.pan_down = False
                    elif e.key == K_COMMA :
                        self.dec_snap_radius= False 
                    elif e.key == K_PERIOD :
                        self.inc_snap_radius = False
                elif e.key == K_LEFT:
                    self.move_left = False
                elif e.key == K_RIGHT:
                    self.move_right = False
                elif e.key == K_SPACE:
                    self.jump = False
            elif e.type == pygame.MOUSEBUTTONDOWN and self.mode_edit:
                if e.button == 1:
                    self.mode_grav_poly=True

                    pos_snap=self.level.check_snap(self.screen2world(e.pos),self.snap_radius)
                    if pos_snap is not None:
                        pos=pos_snap
                    else:
                        pos=self.screen2world(e.pos)
                    self.pos_start=pos

            elif e.type == pygame.MOUSEBUTTONUP and self.mode_edit:
                if e.button == 1:
                    pos_snap=self.level.check_snap(self.screen2world(e.pos),self.snap_radius)
                    if pos_snap is not None:
                        pos=pos_snap
                    else:
                        pos=self.screen2world(e.pos)
                    self.pos_end=pos
            elif e.type == JOYHATMOTION:
                x, y = e.value
                if x == 0:
                    self.move_left = False
                    self.move_right = False
                elif x == 1:
                    self.move_right = True
                elif x == -1:
                    self.move_left = True
            elif e.type == JOYAXISMOTION:
                if e.axis == 0:
                    if e.value < DEADZONE and e.value > -DEADZONE:
                        self.move_left = False
                        self.move_right = False
                    elif e.value >= DEADZONE:
                        self.move_right = True
                    elif e.value <= -DEADZONE:
                        self.move_left = True
            elif e.type == JOYBUTTONDOWN:
                if e.button == 1 and self.on_ground():
                    self.jump = True
                    self.jump_time = JUMP_TIME
                    self.player.jump()
                if e.button == 2:
                    self.player.body.reset_forces()
                if e.button == 3:
                    self.player.body.reset_forces()                   
                    self.player.body.apply_force(Vec2d(0.0, -900 * self.player.body.mass))
            elif e.type == JOYBUTTONUP:
                if e.button == 1:
                    self.jump = False

        if self.mode_edit:
            self.pos_mouse=pygame.mouse.get_pos()
            if self.pos_mouse is not None: self.pos_mouse=self.screen2world(self.pos_mouse)


    def tick(self,screen,clock):
        time = clock.tick(60)/1000.0
        #pygame.display.set_caption("fps: " + str(clock.get_fps()))
        self.handle_input()

        if self.pan_left:
            self.camera_pos += Vec2d(-1 * PAN_SPEED, 0)
        if self.pan_right:
            self.camera_pos += Vec2d(PAN_SPEED, 0)
        if self.pan_up:
            self.camera_pos += Vec2d(0, PAN_SPEED)
        if self.pan_down:
            self.camera_pos += Vec2d(0, -1 * PAN_SPEED)
        
        #check to see if the player is allowed to move left/right
        allow_left = True
        allow_right = True
        #print 'collisions'
        for c in self.player_collisions:
            body_loc = self.player.body.world_to_local(c)
            #print body_loc
            #p = self.player.shape.body.position
            #a = (c - p).get_angle_degrees()
            #print a
            #if abs((a % 360) - 180) < PLAYER_WALL_COLLISION_ANGLE:
            if abs(body_loc.x + 20) < 3:
                allow_left = False
            #if abs(a) < PLAYER_WALL_COLLISION_ANGLE:
            if abs(body_loc.x - 20) < 3:
                allow_right = False
            
        #control the player
        speed = 0
        if self.move_left and allow_left:
            speed -= PLAYER_SPEED
        if self.move_right and allow_right:
            speed += PLAYER_SPEED
        
        if self.jump and self.jump_time > 0:
            self.player.body.apply_impulse(Vec2d(0,self.jump_time*JUMP_STRENGTH/JUMP_TIME))
            self.jump_time -= time
        
        if self.last_on_ground > 0:
            self.last_on_ground -= time
        
        if speed and self.on_ground():
            self.player.walk()
        elif self.on_ground():
            self.player.idle()
        else:
            self.player.fly()
            
        self.player.body.velocity = Vec2d(speed, self.player.body.velocity[1])
            
        self.player.body.angle = 0
        self.player.body.angular_velocity = 0
        
        if self.mode_edit:
            if self.dec_snap_radius:
                self.snap_radius-=1
                if self.snap_radius<1: self.snap_radius=1
            if self.inc_snap_radius:
                self.snap_radius+=1
            if self.mode_gvol:#doing gravity volume stuff
               
                #gravity vector mode, endpoints are defined
                if self.mode_grav_vec and self.pos_start is not None and self.pos_end is not None:
                    self.grav_vec =  (self.pos_end[0]-self.pos_start[0], self.pos_end[1]-self.pos_start[1])
                    self.pos_start=None
                    self.pos_end=None
                elif self.mode_grav_vec is False and self.mode_grav_poly and self.pos_start is not None:#not doing gravity vector
                    self.poly_verts.append((self.pos_start[0],self.pos_start[1]))
                    self.mode_grav_poly=False
            #think gravity was set: add gravity object and clear our vars
            elif self.pos_start is not None and self.pos_end is not None:
                body = pm.Body(pm.inf, pm.inf)
                shape = pm.Segment(body, self.pos_start, self.pos_end, 5.0)
                shape.friction = 1.0
                self.space.add_static(shape)
                self.level.add_line(level.line(self.pos_start, self.pos_end, shape))
                self.pos_start = None
                self.pos_end= None
            if self.grav_set and self.mode_grav_vec is not None and self.poly_verts!=[]:
                self.level.add_gvol(map(lambda x:(x[0],x[1]),self.poly_verts),self.grav_vec)
                self.space.add_static(self.level.gvols[-1].shape)
                self.poly_verts=[]
                self.grav_vec=None

        self.player.update(time)
        
        for e in self.level.emitters:
            e.update(self, time)
        
        dead_particles = []
        for i, p in enumerate(self.particles):
            p.ttl -= time
            if p.ttl < 0:
                dead_particles.append(i)
        for i in dead_particles:
            p = self.particles[i]
            self.space.remove(p.body, p.shape)
            del self.particles[i]
                
        self.physics(time)
        
        if not self.mode_edit:
            self.camera_pos = Vec2d(self.player.body.position)
        
        self.draw(screen)
        
        if self.game_over:
            return 3
        else:
            return 1
    
    def physics(self,time):
        self.set_screen_shape()
        self.player_collisions = []
        self.space.step(time)
    
    def draw(self,screen):
        screen.fill((255,255,255))

        for p in self.particles:
            pygame.draw.circle(screen, (255,0,0), self.world2screen(p.body.position), 1)

        #Draw the player
        self.player.draw(screen)
#        r = self.player.shape.radius
#        v = self.player.shape.body.position
#        rot = self.player.shape.body.rotation_vector
#        p = self.world2screen(v)
#        p2 = Vec2d(rot.x, -rot.y) * r
#        pygame.draw.circle(screen, (0,0,255), p, int(r), 2)
#        pygame.draw.line(screen, (255,0,0), p, p+p2)
#        pygame.draw.circle(screen, (0,0,255) , self.world2screen(Vec2d(0,0)), 20, 2)
        
        #points = self.player.shape.get_points()
        #flipped = map(self.world2screen,points)
        #pygame.draw.polygon(screen,(0,0,255),flipped,1)
        
        #for p in self.player_collisions:
        #    pygame.draw.circle(screen, (255,0,0) , self.world2screen(p),3,0)
        
        if self.mode_edit:
            pos_snap=self.level.check_snap(self.pos_mouse,self.snap_radius)
            if pos_snap is not None:
                pre_end=pos_snap
                pygame.draw.circle(screen, (255,0,0) , self.world2screen(pos_snap),int(self.snap_radius),1)
            else:
                pre_end=self.pos_mouse
            #Draw mouse drag
            if self.pos_start is not None and self.pos_mouse is not None:
                pygame.draw.line(screen, (0,0,0), self.world2screen(self.pos_start),self.world2screen(pre_end))
            #draw edit osd
            cmds = ["Pan Up: w", "Pan Left: a", "Pan Down: s", "Pan Right: d", "Toggle Edit mode: E",\
                    "Save: k", "Increase Snap Radius: .", "Decrease Snap Radius: ,", "Polygon mode: p"]
            if self.mode_gvol:
                cmds.append("Gravity Volume Mode ENABLED")
                if self.mode_grav_vec: cmds.append("Draw Gravity Vector")
                else: cmds.append("Draw Gravity Polygon")
            font = pygame.font.SysFont('helvetica',14)
            for i in xrange(len(self.poly_verts)):
                pygame.draw.line(screen, (0,0,255), \
                        self.world2screen(self.poly_verts[i]),self.world2screen(self.poly_verts[(i+1)%len(self.poly_verts)]),10)



            for i in xrange(len(cmds)):
                cmd=cmds[i]
                surf=font.render(cmd,True,(40,40,40))
                screen.blit(surf,(self.cmd_x,self.cmd_y+i*surf.get_height()))


        #Draw other stuff
        for shape in self.on_screen:
            line = self.level.get_line(shape)
            if line:
                if line.lethal:
                    color = (255, 0, 0)
                else:
                    color = (180, 180, 180)
                pygame.draw.line(screen, color, self.world2screen(line.start),self.world2screen(line.end),10)
                for gvol in self.level.gvols:
                    points = gvol.shape.get_points()
                    flipped = map(self.world2screen,points)
                    pygame.draw.polygon(screen,(0,0,255),flipped,1)

        pygame.display.flip()
        
