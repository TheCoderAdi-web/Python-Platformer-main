import pygame
import sys
from os import listdir
from os.path import isfile, join
pygame.init()

pygame.display.set_caption("Platformer")

WIDTH, HEIGHT = 1000, 800
FPS = 60
PLAYER_VEL = 5

WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))

def read_level_data(level_file_name):
    path = join("assets", "Levels", level_file_name)
    level_data = []
    try:
        with open(path, 'r') as f:
            for line in f:
                # Remove newline characters and add to level data
                level_data.append(list(line.strip()))
    except FileNotFoundError:
        print(f"Error: Level file '{path}' not found.")
        # Return an empty grid or a default one if file not found
        return []
    return level_data

def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]


def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites


def get_block(x, y, size):
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(x, y, size, size)
    surface.blit(image, (0, 0), rect)
    return surface


class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1
    SPRITES = load_sprite_sheets("MainCharacters", "NinjaFrog", 32, 32, True)
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0
        self.hit_times = 0
        self.health = 5
        self.heart_image = pygame.image.load(join("assets", "In-Game-UI", "heartImage.png"))

    def jump(self):
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0

    def jump_trampoline(self):
        self.y_vel = -self.GRAVITY * 12
        self.animation_count = 0

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def make_hit(self):
        self.hit = True
        if self.hit == True and self.hit_times == 0:
            self.health -= 1
            self.hit_times += 1

    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps):
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2:
            self.hit = False
            self.hit_count = 0
            self.hit_times = 0

        self.fall_count += 1
        self.update_sprite()

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.count = 0
        self.y_vel *= -1

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.hit:
            sprite_sheet = "hit"
        elif self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self, win, offset_x, offset_y):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y - offset_y))
        for h in range(self.health):
            win.blit(self.heart_image, (h * self.heart_image.get_width(), 20))


class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x, offset_y):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y - offset_y))


class Block(Object):
    def __init__(self, x, y, size, type):
        super().__init__(x, y, size, size)
        if type == "X":
            block = get_block(192, 0, size)
        elif type == "D":
            block = get_block(288, 0, size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)


class Fire(Object):
    ANIMATION_DELAY = 6

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        self.fire = load_sprite_sheets("Traps", "Fire", width, height)
        self.image = self.fire["on"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "on"

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def loop(self, fps, objects, player):
        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0

class Spike(Object):
    def __init__(self, x, y, width, height, type):
        super().__init__(x, y, width, height, "spike")
        self.spike = pygame.image.load(join("assets", "Traps", "Spikes", "Idle.png")).convert_alpha()
        self.image = pygame.transform.scale(self.spike, (width, height))
        if type == "Down":
            self.image = pygame.transform.rotate(self.image, 180)

class Trampoline(Object):
    ANIMATION_DELAY = 6
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "trampoline")
        self.trampoline = load_sprite_sheets("Traps", "Trampoline", width, height)
        self.image = self.trampoline["Idle"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "Idle"
        self.jump_count = 0

    def jump_player(self):
        if self.animation_name == "Idle":
            self.animation_name = "Jump"
            self.animation_count = 0


    def loop(self, fps, player, objects):
        sprites = self.trampoline[self.animation_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0

        if self.animation_name == "Jump":
            self.jump_count += 1
            if self.jump_count > fps * 0.5:
                self.animation_name = "Idle"
                self.jump_count = 0

class Rock_Head(Object):
    """
    A crushing rock head trap that falls when the player is detected below it.
    """
    IDLE = 0
    FALLING = 1
    SMASHED = 2
    RESETTING = 3

    ANIMATION_DELAY = 10

    def __init__(self, x, y, width, height, fall_speed=1, reset_time=FPS * 0.5):
        # Use the calculated scaled size for the Rock_Head's actual width/height
        super().__init__(x, y, width, height, "rock_head")
        
        self.original_y = y
        
        # Load sprite sheets using the raw dimensions as expected by load_sprite_sheets
        self.rock_head = load_sprite_sheets("Traps", "Rock Head", width, height)
        
        self.image = self.rock_head["Idle"][0]
        self.mask = pygame.mask.from_surface(self.image)

        self.state = self.IDLE
        self.fall_speed = fall_speed
        self.y_vel = 0
        self.reset_timer = 0
        self.reset_time = reset_time # Time in frames before reset
        self.trigger_rect = pygame.Rect(self.rect.x, self.rect.bottom,
                                        self.rect.width, self.rect.height * 5)
        self.animation_name = "Idle"
        self.animation_count = 0


    def _check_collision_with_static_objects(self, objects):
        for obj in objects:
            if obj != self and not isinstance(obj, Fire) and not isinstance(obj, Rock_Head):
                if pygame.sprite.collide_mask(self, obj):
                    if self.y_vel > 0:
                        self.rect.bottom = obj.rect.top
                        self.y_vel = 0
                        return True
    
        return False

    def loop(self, fps, game_objects, player):
        sprites = self.rock_head[self.animation_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1
        if self.animation_count // self.ANIMATION_DELAY >= len(sprites):
            self.animation_count = 0

        if self.state == self.IDLE:
            self.trigger_rect.topleft = (self.rect.x, self.rect.bottom)

            if player.rect.colliderect(self.trigger_rect):
                self.state = self.FALLING

        elif self.state == self.FALLING:
            self.rect.y += self.y_vel
            self.y_vel += self.fall_speed

            if pygame.sprite.collide_mask(self, player) and self.y_vel > 0:
                player.make_hit()

            if self._check_collision_with_static_objects(game_objects):
                self.state = self.SMASHED
                self.y_vel = 0
                self.animation_name = "Bottom Hit"

        elif self.state == self.SMASHED:
            self.reset_timer += 1
            if self.reset_timer >= self.reset_time:
                self.state = self.RESETTING

        elif self.state == self.RESETTING:
            self.y_vel = 0
            self.reset_timer = 0
            self.animation_name = "Idle" 
            if self.rect.y > self.original_y:
                self.rect.y -= 3
            else:
                self.state = self.IDLE

        self.update()

    def update(self):
        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

def get_background(name):
    image = pygame.image.load(join("assets", "Background", name))
    _, _, width, height = image.get_rect()
    tiles = []

    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, image


def draw(window, background, bg_image, player, objects, offset_x, offset_y):
    for tile in background:
        window.blit(bg_image, tile)

    for obj in objects:
        obj.draw(window, offset_x, offset_y)

    player.draw(window, offset_x, offset_y)

            
    pygame.display.update()

def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()

            collided_objects.append(obj)

    return collided_objects


def collide(player, objects, dx):
    player.move(dx, 0)
    player.update()
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break

    player.move(-dx, 0)
    player.update()
    return collided_object


def handle_move(player, objects):
    keys = pygame.key.get_pressed()

    player.x_vel = 0
    collide_left = collide(player, objects, -PLAYER_VEL * 2)
    collide_right = collide(player, objects, PLAYER_VEL * 2)

    if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and not collide_left:
        player.move_left(PLAYER_VEL)
    if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and not collide_right:
        player.move_right(PLAYER_VEL)

    vertical_collide = handle_vertical_collision(player, objects, player.y_vel)
    to_check = [collide_left, collide_right, *vertical_collide]

    for obj in to_check:
        if obj and obj.name == "fire":
            player.make_hit()
            break
        elif obj and obj.name == "spike":
            player.make_hit()
            break
        elif obj and obj.name == "trampoline":
            obj.jump_player()
            player.jump_trampoline()
            break

def scroll(offset_x, offset_y, player, scroll_area_width, scroll_area_height):
    if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
            (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
        offset_x += player.x_vel
    if ((player.rect.bottom - offset_y >= HEIGHT - scroll_area_height) and player.y_vel > 0) or (
            (player.rect.top - offset_y <= scroll_area_height) and player.y_vel < 0):
        offset_y += player.y_vel
            
    offset_x = max(0, offset_x)

    return offset_x, offset_y

def main(window):
    clock = pygame.time.Clock()
    background, bg_image = get_background("Green.png")

    BLOCK_SIZE = 96
    
    player = None
    objects = []

    scroll_area_width = 200
    scroll_area_height = 200

    level_data = read_level_data("level_1.txt")

    for row_index, row in enumerate(level_data):
            for col_index, tile_char in enumerate(row):
                x = col_index * BLOCK_SIZE
                y = row_index * BLOCK_SIZE

                if tile_char == 'X':
                    # Create a Block object for grass
                    objects.append(Block(x, y, BLOCK_SIZE, "X"))
                elif tile_char == 'F':
                    # Create a Fire object, adjust its y position to sit on a block
                    fire_obj = Fire(x + 48, y + BLOCK_SIZE // 3, 16, 32)
                    fire_obj.on() # Set fire to animated state
                    objects.append(fire_obj)
                elif tile_char == 'P':
                    # Create the Player object at this position
                    player = Player(x, y, 50, 50)
                    offset_x = player.rect.x - WIDTH // 2
                    offset_y = player.rect.y - HEIGHT // 2
                elif tile_char == 'D':
                    # Create a Block object for dirt
                    objects.append(Block(x, y, BLOCK_SIZE, "D"))
                elif tile_char == 'S':
                    # Create a Spike object
                    spike_obj = Spike(x + 24, y + 32, 64, 64, "Up")
                    objects.append(spike_obj)
                elif tile_char == 's':
                    spike_obj = Spike(x, y, 64, 64, "Down")
                    objects.append(spike_obj)
                elif tile_char == 'T':
                    # Create a Trampoline object
                    trampoline_obj = Trampoline(x + 16, y + 40, 28, 28)
                    objects.append(trampoline_obj)
                elif tile_char == 'R':
                    rock_head_obj = Rock_Head(x, y + 40, 42, 42)
                    objects.append(rock_head_obj)

    while True:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
                exit()
            if event.type == pygame.KEYDOWN:
                if (event.key == pygame.K_SPACE or event.type == pygame.K_UP or event.type == pygame.K_w) and player.jump_count < 2:
                    player.jump()

        player.loop(FPS)
        handle_move(player, objects)
        for obj in objects:
            if hasattr(obj, 'loop'):
                obj.loop(FPS, objects, player)

        offset_x, offset_y = scroll(offset_x, offset_y, player, scroll_area_width, scroll_area_height)

        draw(window, background, bg_image, player, objects, offset_x, offset_y)

        #Player Health
        if player.health <= 0:
            sys.exit()
            exit()

if __name__ == "__main__":
    main(WINDOW)
