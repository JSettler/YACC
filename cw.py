"""
YACC - Yet Another Castlewars Clone - put under AGPL(v3) license
------------------------------------------------------------------

Instructions
The purpose of this game is to be the first to build a 100 storey
castle, but its also possible to win by destroying your opponents castle

Cards
#	Name	Cost	Effect
01	Wall	1 brick	fence +3
02	Base	1 brick	castle +2
03	Defence	3 brick	fence +6
04	Reserve	3 brick	castle +8; fence -4
05	Tower	5 brick	castle +5
06	School	8 brick	builders +1
07	Wain	10 brick	castle +8; enemy castle -4
08	Fence	12 brick	fence +22
09	Fort	18 brick	castle +20
10	Babylon	39 brick	castle +32
11  Archer	1 sword	attack 2
12	Knight	2 sword	attack 3
13	Rider	2 sword	attack 4
14	Platoon	4 sword	attack 6
15	Recruit	8 sword	soldiers +1
16	Attack	10 sword	attack 12
17	Saboteur	12 sword	enemy stocks -4
18	Thief	15 sword	transfer enemy stocks 5
19	Swat	18 sword	enemy castle -10
20	Banshee	28 sword	attack 32
21	Conjure Bricks	4 crystal	bricks +8
22	Conjure Crystals	4 crystal	crystals +8
23	Conjure Weapons	4 crystal	weapons +8
24	Crush Bricks	4 crystal	enemy bricks -8
25	Crush Crystals	4 crystal	enemy crystals -8
26	Crush Weapons	4 crystal	enemy weapons -8
27	Sorcerer	8 crystal	magic +1
28	Dragon	21 crystal	attack 25
29	Pixies	22 crystal	castle +22
30	Curse	45 crystal	all +1; enemies all -1
"""
# (potential) special/premium cards:
#31 University  32? brick    all generators +1
#32 Poison      25-35 sword all enemy generators -1
#33 Abduct      20-25 brick    builder +1; enemy builder -1
#34 Bribe       20-25 weapon   soldiers +1; enemy soldiers -1
#35 Enchant     20-25 crystals mages +1; enemy mages -1
# but these would change the game very much..


import pygame
import random
import math
import wave
import struct
import os
import pickle
import json


# Initialize Pygame
pygame.init()

# Set up the display
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()


DEBUG_MODE = False     # Set to 'True' to show the ingame debug-message-box (and shift the card-playing area to the top, to make more place for it)
SHOW_COMPUTER_CARDS = False  # to have 4 different modes available: full release, full debug, show-cards-only and debug-without-showing-cards modes

MAX_DEBUG_MESSAGES = 100  # Adjust this value as needed
debug_messages = []

debug_font = pygame.font.Font(None, 20)  # Small font for debug messages

DEBUG_CARD_PLAY_Y = 60  # Just below the player indicator
DEBUG_MSG_TOP_MARGIN = 10  # Space between card play area and debug box


# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_GREEN = (0, 100, 0)
BLUE_GREY = (100, 100, 150)
BROWN = (139, 69, 19)
SKY_BLUE = (135, 206, 235)
CARD_RED = (255, 200, 200)
CARD_DARK_RED = (200, 100, 100)
CARD_GREEN = (200, 255, 200)
CARD_DARK_GREEN = (100, 200, 100)
CARD_BLUE = (200, 200, 255)
CARD_DARK_BLUE = (100, 100, 200)
CARD_BACK = (100, 100, 100)


# Graphical constants
TOWER_WIDTH = 60    # 50
FENCE_WIDTH = 10
CARD_WIDTH = 100
CARD_HEIGHT = 150
CENTER_CARD_X = WIDTH // 2 - CARD_WIDTH // 2
CENTER_CARD_Y = HEIGHT // 2 - CARD_HEIGHT // 2

CARD_PLAY_AREA_Y = HEIGHT // 2 - CARD_HEIGHT // 2  -100

ANIMATION_SPEED = 2  # actually, this is the delay: the higher, the slower is the animation


# Gameplay constants
TOWER_START_HEIGHT = 30  # 50  # 25
FENCE_START_HEIGHT = 10  # 15
TOWER_WIN_HEIGHT = 200  # 1000  # 100
MAX_CARDS = 15   # old CW-default: 8   # max.15, due to graphical constraints
DISCARD_MAX = 1    # how many cards a player can throw away at maximum, per each turn  (max: the amount of cards in the hand)

PASSES_ALLOWED = False # True  # Set this to False if passes are not valid moves



def debug_print(message):
    global debug_messages
    if DEBUG_MODE:
        print(message)  # Print to console as well
        debug_messages.append(message)
        if len(debug_messages) > MAX_DEBUG_MESSAGES:
            debug_messages.pop(0)  # Remove oldest message if we exceed the maximum
        draw_game(CENTER_CARD_X, CENTER_CARD_Y)
        pygame.display.flip()
        waiting_for_click = True
        while waiting_for_click:
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    waiting_for_click = False
                elif event.type == pygame.QUIT:
                    pygame.quit()
                    import sys
                    sys.exit()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    waiting_for_click = False
            pygame.time.wait(10)  # Small delay to prevent high CPU usage



# Add this near the top of your script, with other global variables
game_just_loaded = False


def create_sound(filename, freq, duration, wave_type='sine'):
    sample_rate = 44100
    num_samples = int(sample_rate * duration)
    
    wav_file = wave.open(filename, 'w')
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(sample_rate)
    
    for i in range(num_samples):
        if wave_type == 'sine':
            sample = int(32767 * math.sin(2 * math.pi * freq * i / sample_rate))
        elif wave_type == 'square':
            sample = int(32767 * (1 if math.sin(2 * math.pi * freq * i / sample_rate) > 0 else -1))
        elif wave_type == 'sawtooth':
            sample = int(32767 * ((i % (sample_rate // freq)) / (sample_rate // freq) * 2 - 1))
        wav_file.writeframes(struct.pack('h', sample))
    
    wav_file.close()

# Generate improved sound files
sound_files = [f"cw_sound{i}.wav" for i in range(1, 8)]
if not all(os.path.exists(f) for f in sound_files):
    create_sound("cw_sound1.wav", 440, 0.1, 'sine')  # A4 note
    create_sound("cw_sound2.wav", 523, 0.1, 'square')  # C5 note
    create_sound("cw_sound3.wav", 659, 0.1, 'sawtooth')  # E5 note
    create_sound("cw_sound4.wav", 784, 0.1, 'sine')  # G5 note
    create_sound("cw_sound5.wav", 880, 0.1, 'square')  # A5 note
    create_sound("cw_sound6.wav", 987, 0.1, 'sawtooth')  # B5 note
    create_sound("cw_sound7.wav", 1046, 0.1, 'sine')  # C6 note



# Initialize Pygame mixer and load sound effects
pygame.mixer.init()
sound_effects = {}
for i in range(1, 8):
    sound_effects[i] = pygame.mixer.Sound(f"cw_sound{i}.wav")


# Create pass sound files if they don't exist
if not os.path.exists("pass_high.wav"):
    create_sound("pass_high.wav", 880, 0.1, 'sine')  # A5 note, short duration
if not os.path.exists("pass_low.wav"):
    create_sound("pass_low.wav", 440, 0.3, 'sine')  # A4 note, longer duration

# Now load the sound files
pass_sound_high = pygame.mixer.Sound("pass_high.wav")
pass_sound_low = pygame.mixer.Sound("pass_low.wav")


class CardTemplate:
    def __init__(self, name, cost, effect, sound_id):
        self.name = name
        self.cost = cost
        self.effect = effect
        self.sound_id = sound_id

    def create_card(self, player):
        return Card(self.name, self.cost, self.effect, self.sound_id, player)


class Card:
    def __init__(self, name, cost, effect, sound_id, player):
        self.name = name
        self.cost = cost
        self.effect = effect
        self.color = self.get_color()
        self.sound_id = sound_id
        self.selected_for_discard = False
        self.id = id(self)  # Unique identifier for each card instance
        self.player = player  # Reference to the player who owns this card



    def __eq__(self, other):
        if isinstance(other, Card):
            return self.id == other.id
        return False

    def __hash__(self):
        return hash(self.id)


    def get_color(self):
        if "brick" in self.cost:
            return CARD_RED
        elif "sword" in self.cost:
            return CARD_GREEN
        elif "crystal" in self.cost:
            return CARD_BLUE
        return WHITE

    def play_sound(self):
        sound_effects[self.sound_id].play()

CARD_TYPES = [
    CardTemplate("Wall", "1 brick", "fence +3", 1),
    CardTemplate("Base", "1 brick", "castle +2", 1),
    CardTemplate("Defence", "3 brick", "fence +6", 1),
    CardTemplate("Reserve", "3 brick", "castle +8; fence -4", 1),
    CardTemplate("Tower", "5 brick", "castle +5", 1),
    CardTemplate("School", "8 brick", "builders +1", 3),
    CardTemplate("Wain", "10 brick", "castle +8; enemy castle -4", 1),
    CardTemplate("Fence", "12 brick", "fence +22", 1),
    CardTemplate("Fort", "18 brick", "castle +20", 1),
    CardTemplate("Babylon", "39 brick", "castle +32", 1),
    CardTemplate("Archer", "1 sword", "attack 2", 2),
    CardTemplate("Knight", "2 sword", "attack 3", 2),
    CardTemplate("Rider", "2 sword", "attack 4", 2),
    CardTemplate("Platoon", "4 sword", "attack 6", 2),
    CardTemplate("Recruit", "8 sword", "soldiers +1", 3),
    CardTemplate("Attack", "10 sword", "attack 12", 2),
    CardTemplate("Saboteur", "12 sword", "enemy stocks -4", 4),
    CardTemplate("Thief", "15 sword", "transfer enemy stocks 5", 4),
    CardTemplate("Swat", "18 sword", "enemy castle -10", 2),
    CardTemplate("Banshee", "28 sword", "attack 32", 5),
    CardTemplate("Conjure Bricks", "4 crystal", "bricks +8", 6),
    CardTemplate("Conjure Crystals", "4 crystal", "crystals +8", 6),
    CardTemplate("Conjure Weapons", "4 crystal", "weapons +8", 6),
    CardTemplate("Crush Bricks", "4 crystal", "enemy bricks -8", 7),
    CardTemplate("Crush Crystals", "4 crystal", "enemy crystals -8", 7),
    CardTemplate("Crush Weapons", "4 crystal", "enemy weapons -8", 7),
    CardTemplate("Sorcerer", "8 crystal", "mages +1", 3),
    CardTemplate("Dragon", "21 crystal", "attack 25", 5),
    CardTemplate("Pixies", "22 crystal", "castle +22", 5),
    CardTemplate("Curse", "45 crystal", "all +1; enemies all -1", 5)
]


class Player:
    def __init__(self, is_human):
        self.is_human = is_human
        self.tower_height = TOWER_START_HEIGHT
        self.fence_height = FENCE_START_HEIGHT
        self.bricks = 5
        self.weapons = 5
        self.crystals = 5
        self.builders = 2
        self.soldiers = 2
        self.mages = 2
        self.cards = []
        self.resources_added_this_turn = False


    def draw_card(self):
        if len(self.cards) < MAX_CARDS:
            card_template = random.choice(CARD_TYPES)
            self.cards.append(card_template.create_card(self))

    def can_afford(self, card):
        cost_value = int(card.cost.split()[0])
        cost_type = card.cost.split()[1]
        if cost_type == 'brick':
            can_pay = self.bricks >= cost_value
        elif cost_type == 'sword':
            can_pay = self.weapons >= cost_value
        elif cost_type == 'crystal':
            can_pay = self.crystals >= cost_value
        else:
            can_pay = False

        # Special case for "Reserve" card
        if card.name == "Reserve":
            return can_pay and self.fence_height >= 4

        return can_pay


    def add_resources(self):
        global game_just_loaded
        if not self.resources_added_this_turn and not game_just_loaded:
            self.bricks += self.builders
            self.weapons += self.soldiers
            self.crystals += self.mages
        self.resources_added_this_turn = True



# Initialize game state
human_player = Player(True)
computer_player = Player(False)
current_player = human_player
center_card = None


# Initialize cards
for _ in range(MAX_CARDS):
    human_player.draw_card()
    computer_player.draw_card()



def draw_card_on_screen(card, x, y, show_face=True, playable=True, dimmed=False):
    shift = 20 if card.selected_for_discard else 0
    if show_face:
        if dimmed:
            color = (int(card.color[0] * 0.5), int(card.color[1] * 0.5), int(card.color[2] * 0.5))
        else:
            color = card.color if playable else (int(card.color[0] // 2), int(card.color[1] // 2), int(card.color[2] // 2))

        pygame.draw.rect(screen, color, (x, y - shift, CARD_WIDTH, CARD_HEIGHT))
        pygame.draw.rect(screen, BLACK, (x, y - shift, CARD_WIDTH, CARD_HEIGHT), 2)  # Border
        
        font = pygame.font.Font(None, 20)
        text_color = BLACK if not dimmed else (int(BLACK[0] * 0.5), int(BLACK[1] * 0.5), int(BLACK[2] * 0.5))

        
        def split_text(text, max_width):
            words = text.split()
            lines = []
            current_line = []
            for word in words:
                if font.size(' '.join(current_line + [word]))[0] <= max_width:
                    current_line.append(word)
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]
            if current_line:
                lines.append(' '.join(current_line))
            return lines

        # Draw card name at the top (multi-line if necessary)
        name_lines = split_text(card.name, CARD_WIDTH - 10)
        for i, line in enumerate(name_lines):
            name_text = font.render(line, True, BLACK)
            name_rect = name_text.get_rect(midtop=(x + CARD_WIDTH/2, y + 5 - shift + i*20))
            screen.blit(name_text, name_rect)
        
        # Draw effect in the middle (multi-line if necessary)
        effect_lines = split_text(card.effect, CARD_WIDTH - 10)
        effect_start_y = y + CARD_HEIGHT/2 - 10 * len(effect_lines) - shift
        for i, line in enumerate(effect_lines):
            effect_text = font.render(line, True, BLACK)
            effect_rect = effect_text.get_rect(center=(x + CARD_WIDTH/2, effect_start_y + i*20))
            screen.blit(effect_text, effect_rect)
        
        # Draw cost at the bottom
        cost_text = font.render(f"-{card.cost}", True, BLACK)
        cost_rect = cost_text.get_rect(midbottom=(x + CARD_WIDTH/2, y + CARD_HEIGHT - 5 - shift))
        screen.blit(cost_text, cost_rect)
    else:
        pygame.draw.rect(screen, CARD_BACK, (x, y - shift, CARD_WIDTH, CARD_HEIGHT))
        pygame.draw.rect(screen, BLACK, (x, y - shift, CARD_WIDTH, CARD_HEIGHT), 2)  # Border
        font = pygame.font.Font(None, 20)
        text = font.render("Card", True, WHITE)
        text_rect = text.get_rect(center=(x + CARD_WIDTH/2, y + CARD_HEIGHT/2 - shift))
        screen.blit(text, text_rect)



def draw_game(center_card_x, center_card_y):
    screen.fill(SKY_BLUE)
    pygame.draw.rect(screen, DARK_GREEN, (0, HEIGHT * 2 // 3, WIDTH, HEIGHT // 3))

    # Draw towers and fences
    max_visible_height = HEIGHT * 2 // 3
    human_tower_height = min(human_player.tower_height * 5, max_visible_height)
    computer_tower_height = min(computer_player.tower_height * 5, max_visible_height)
    
    pygame.draw.rect(screen, BLUE_GREY, (50, HEIGHT * 2 // 3 - human_tower_height, TOWER_WIDTH, human_tower_height))
    pygame.draw.rect(screen, BLUE_GREY, (150, HEIGHT * 2 // 3 - human_player.fence_height * 5, FENCE_WIDTH, human_player.fence_height * 5))
    pygame.draw.rect(screen, WHITE, (150, HEIGHT * 2 // 3 - human_player.fence_height * 5, FENCE_WIDTH, 5))  # White top brick
    
    pygame.draw.rect(screen, BROWN, (WIDTH - 100, HEIGHT * 2 // 3 - computer_tower_height, TOWER_WIDTH, computer_tower_height))
    pygame.draw.rect(screen, BROWN, (WIDTH - 160, HEIGHT * 2 // 3 - computer_player.fence_height * 5, FENCE_WIDTH, computer_player.fence_height * 5))
    pygame.draw.rect(screen, WHITE, (WIDTH - 160, HEIGHT * 2 // 3 - computer_player.fence_height * 5, FENCE_WIDTH, 5))  # White top brick

    # Draw player cards
    for i, card in enumerate(human_player.cards):
        draw_card_on_screen(card, 10 + i * (CARD_WIDTH + 10), HEIGHT - CARD_HEIGHT - 10, playable=human_player.can_afford(card))

    # Draw computer cards (shifted to the right edge)
    for i, card in enumerate(computer_player.cards):
        draw_card_on_screen(card, WIDTH - (CARD_WIDTH + 10) * (MAX_CARDS - i), HEIGHT * 2 // 3 + 10, show_face=SHOW_COMPUTER_CARDS, playable=computer_player.can_afford(card))

    # Draw resources and generators
    font = pygame.font.Font(None, 24)
    
    # Human player resources
    human_resources_text = f"Human - Bricks: {human_player.bricks} | Weapons: {human_player.weapons} | Crystals: {human_player.crystals}"
    human_generators_text = f"Builders: {human_player.builders} | Soldiers: {human_player.soldiers} | Mages: {human_player.mages}"
    human_structures_text = f"Castle: {human_player.tower_height} | Fence: {human_player.fence_height}"
    screen.blit(font.render(human_resources_text, True, BLACK), (10, 10))
    screen.blit(font.render(human_generators_text, True, BLACK), (10, 40))
    screen.blit(font.render(human_structures_text, True, BLACK), (10, 70))

    # Computer player resources (shifted to the right edge)
    computer_resources_text = f"Computer - Bricks: {computer_player.bricks} | Weapons: {computer_player.weapons} | Crystals: {computer_player.crystals}"
    computer_generators_text = f"Builders: {computer_player.builders} | Soldiers: {computer_player.soldiers} | Mages: {computer_player.mages}"
    computer_structures_text = f"Castle: {computer_player.tower_height} | Fence: {computer_player.fence_height}"
    screen.blit(font.render(computer_resources_text, True, BLACK), (WIDTH - font.size(computer_resources_text)[0] - 10, 10))
    screen.blit(font.render(computer_generators_text, True, BLACK), (WIDTH - font.size(computer_generators_text)[0] - 10, 40))
    screen.blit(font.render(computer_structures_text, True, BLACK), (WIDTH - font.size(computer_structures_text)[0] - 10, 70))


    # Draw current player indicator with a clickable area
    current_player_text = "Current Player: " + ("Human" if current_player.is_human else "Computer")
    text_rect = font.render(current_player_text, True, BLACK).get_rect(center=(WIDTH // 2, 25))
    pygame.draw.rect(screen, (200, 200, 200), (text_rect.left - 10, text_rect.top - 5, text_rect.width + 20, text_rect.height + 10))
    screen.blit(font.render(current_player_text, True, BLACK), text_rect)


  
    # Determine card play area position
    if DEBUG_MODE:
        card_play_y = DEBUG_CARD_PLAY_Y   # Fixed position below player indicator in debug mode
    else:
        card_play_y = (HEIGHT * 2 // 3 - CARD_HEIGHT) // 2  # Centered between top and green area
  

    # Draw center card if it exists
    if not DEBUG_MODE:
        if center_card:
            if isinstance(center_card, list):  # Discarded cards
                for i, card in enumerate(center_card):
                    x = center_card_x - (len(center_card) - 1) * CARD_WIDTH // 2 + i * CARD_WIDTH
                    draw_card_on_screen(card, x, card_play_y, show_face=True, playable=False, dimmed=True)
            else:  # Single played card
                draw_card_on_screen(center_card, center_card_x, card_play_y)


    if DEBUG_MODE:
        # Draw center card if it exists
        if center_card:
            if isinstance(center_card, list):  # Discarded cards
                for i, card in enumerate(center_card):
                    x = center_card_x - (len(center_card) - 1) * CARD_WIDTH // 2 + i * CARD_WIDTH
                    draw_card_on_screen(card, x, DEBUG_CARD_PLAY_Y, show_face=True, playable=False, dimmed=True)
            else:  # Single played card
                draw_card_on_screen(center_card, center_card_x, DEBUG_CARD_PLAY_Y)

        # Calculate debug area position and size
        debug_area_top = DEBUG_CARD_PLAY_Y + CARD_HEIGHT + DEBUG_MSG_TOP_MARGIN
        debug_area_bottom = HEIGHT * 2 // 3 - 5
        debug_area_height = debug_area_bottom - debug_area_top
        debug_area_width = int(WIDTH * 0.8)  # 80% of screen width
        debug_area_left = (WIDTH - debug_area_width) // 2

        # Create debug area surface
        debug_area = pygame.Surface((debug_area_width, debug_area_height))
        debug_area.fill((200, 200, 200))  # Light gray background
        
        # Render debug messages (scrolling from bottom)
        total_height = 0
        visible_messages = []
        for message in reversed(debug_messages):
            text_surface = debug_font.render(message, True, BLACK)
            total_height += text_surface.get_height() + 2
            if total_height > debug_area_height:
                break
            visible_messages.insert(0, text_surface)

        y_offset = debug_area_height - 5  # Start from bottom
        for text_surface in reversed(visible_messages):
            y_offset -= text_surface.get_height() + 2
            debug_area.blit(text_surface, (5, y_offset))

        # Draw a border around the debug area
        pygame.draw.rect(screen, BLACK, (debug_area_left - 2, debug_area_top - 2, debug_area_width + 4, debug_area_height + 4), 2)

        # Blit the debug area onto the screen
        screen.blit(debug_area, (debug_area_left, debug_area_top))

    pygame.display.flip()



def save_game():
    game_state = {
        'human_player': human_player,
        'computer_player': computer_player,
        'current_player': current_player
    }
    with open('cw_savegame.pkl', 'wb') as f:
        pickle.dump(game_state, f)


def load_game():
    global human_player, computer_player, current_player, game_just_loaded
    try:
        with open('cw_savegame.pkl', 'rb') as f:
            game_state = pickle.load(f)
        human_player = game_state['human_player']
        computer_player = game_state['computer_player']
        current_player = game_state['current_player']
        
        game_just_loaded = True
        return True
    except FileNotFoundError:
        return False


def read_score():
    if os.path.exists('cw_match-score.json'):
        with open('cw_match-score.json', 'r') as f:
            return json.load(f)
    return {"human": 0, "computer": 0}


def write_score(score):
    with open('cw_match-score.json', 'w') as f:
        json.dump(score, f)


def animate_card_to_center(card, start_x, start_y):
    global center_card
    steps = 20

    if DEBUG_MODE:
        end_y = DEBUG_CARD_PLAY_Y
    else:
        end_y = (HEIGHT * 2 // 3 - CARD_HEIGHT) // 2


    for i in range(steps + 1):
        t = i / steps
        x = int(start_x + (CENTER_CARD_X - start_x) * t)
        y = int(start_y + (end_y - start_y) * t)

        draw_game(CENTER_CARD_X, end_y)

        draw_card_on_screen(card, x, y)
        pygame.display.flip()
        pygame.time.wait(ANIMATION_SPEED)
    
    center_card = card



def play_card(player, opponent, card):
    debug_print(f"Playing card: {card.name}")
    debug_print(f"Player resources before: Bricks: {player.bricks}, Weapons: {player.weapons}, Crystals: {player.crystals}")
    debug_print(f"Opponent resources before: Bricks: {opponent.bricks}, Weapons: {opponent.weapons}, Crystals: {opponent.crystals}")
    
    # Subtract the cost first
    cost_value = int(card.cost.split()[0])
    cost_type = card.cost.split()[1]
    if cost_type == 'brick':
        player.bricks -= cost_value
    elif cost_type == 'sword':
        player.weapons -= cost_value
    elif cost_type == 'crystal':
        player.crystals -= cost_value
    
    debug_print(f"Resources after paying cost: Bricks: {player.bricks}, Weapons: {player.weapons}, Crystals: {player.crystals}")

    card.play_sound()

    win_by_height = False
    win_by_destruction = False

    debug_print(f"Card effect: {card.effect}")
    effects = card.effect.split(';')
    for effect in effects:
        effect = effect.strip()
        debug_print(f"Applying effect: {effect}")
        if "castle +" in effect:
            value = int(effect.split("+")[1].split()[0])
            player.tower_height += value
            debug_print(f"Increased player's castle height by {value}")
            if player.tower_height >= TOWER_WIN_HEIGHT:
                win_by_height = True
        elif "fence +" in effect:
            value = int(effect.split("+")[1].split()[0])
            player.fence_height += value
        elif "enemy castle" in effect:
            value = int(effect.split("-")[1].split()[0])
            old_height = opponent.tower_height
            opponent.tower_height = max(0, opponent.tower_height - value)
            debug_print(f"Reduced opponent's castle height from {old_height} to {opponent.tower_height} (reduction of {value})")
            if opponent.tower_height <= 0:
                win_by_destruction = True
        elif "castle -" in effect:
            value = int(effect.split("-")[1].split()[0])
            player.tower_height = max(0, player.tower_height - value)
        elif "fence -" in effect:
            value = int(effect.split("-")[1].split()[0])
            player.fence_height = max(0, player.fence_height - value)
        elif "attack" in effect:
            damage = int(effect.split()[1])
            if opponent.fence_height > 0:
                if damage > opponent.fence_height:
                    remaining_damage = damage - opponent.fence_height
                    opponent.fence_height = 0
                    opponent.tower_height = max(0, opponent.tower_height - remaining_damage)
                else:
                    opponent.fence_height -= damage
            else:
                opponent.tower_height = max(0, opponent.tower_height - damage)
            if opponent.tower_height <= 0:
                win_by_destruction = True
        elif any(gen in effect for gen in ["builders", "soldiers", "mages"]):
            attr, value = effect.split("+")
            attr = attr.strip()
            value = int(value)
            setattr(player, attr, getattr(player, attr) + value)
        elif "bricks +" in effect:
            value = int(effect.split("+")[1].split()[0])
            player.bricks += value
        elif "weapons +" in effect:
            value = int(effect.split("+")[1].split()[0])
            player.weapons += value
        elif "crystals +" in effect:
            value = int(effect.split("+")[1].split()[0])
            player.crystals += value

        elif "transfer enemy stocks" in effect:
            debug_print("=== Beginning of Thief card effect ===")
            
            # Store original resource values for player A
            starting_bricks = player.bricks
            starting_weapons = player.weapons
            starting_crystals = player.crystals
            
            debug_print(f"Player A starting resources - Bricks: {starting_bricks}, Weapons: {starting_weapons}, Crystals: {starting_crystals}")
            
            # Process bricks
            B_bricks = opponent.bricks
            debug_print(f"Processing bricks - Opponent has: {B_bricks}")
            opponent.bricks = max(0, B_bricks - 5)
            transfer_bricks = min(5, B_bricks)
            sum_bricks = starting_bricks + transfer_bricks
            player.bricks = sum_bricks
            
            debug_print(f"Bricks transfer - Opponent now has: {opponent.bricks}, Transferred: {transfer_bricks}, Player A now has: {player.bricks}")
            
            # Process weapons
            B_weapons = opponent.weapons
            debug_print(f"Processing weapons - Opponent has: {B_weapons}")
            opponent.weapons = max(0, B_weapons - 5)
            transfer_weapons = min(5, B_weapons)
            sum_weapons = starting_weapons + transfer_weapons
            player.weapons = sum_weapons
            
            debug_print(f"Weapons transfer - Opponent now has: {opponent.weapons}, Transferred: {transfer_weapons}, Player A now has: {player.weapons}")
            
            # Process crystals
            B_crystals = opponent.crystals
            debug_print(f"Processing crystals - Opponent has: {B_crystals}")
            opponent.crystals = max(0, B_crystals - 5)
            transfer_crystals = min(5, B_crystals)
            sum_crystals = starting_crystals + transfer_crystals
            player.crystals = sum_crystals
            
            debug_print(f"Crystals transfer - Opponent now has: {opponent.crystals}, Transferred: {transfer_crystals}, Player A now has: {player.crystals}")
            
            debug_print(f"Final resource states after Thief card effect:")
            debug_print(f"Player A - Bricks: {player.bricks}, Weapons: {player.weapons}, Crystals: {player.crystals}")
            debug_print(f"Player B - Bricks: {opponent.bricks}, Weapons: {opponent.weapons}, Crystals: {opponent.crystals}")
            debug_print("=== End of Thief card effect ===")


        elif "enemy stocks" in effect:
            value = abs(int(effect.split()[-1]))  # Use abs() to ensure a positive value
            for resource in ["bricks", "weapons", "crystals"]:
                current_value = getattr(opponent, resource)
                new_value = max(0, current_value - value)
                reduction = current_value - new_value
                setattr(opponent, resource, new_value)
                debug_print(f"Reduced opponent's {resource} from {current_value} to {new_value}")



    # Special card effects
    if card.name in ["Crush Bricks", "Crush Weapons", "Crush Crystals"]:
        resource = card.name.split()[1].lower()
        current_value = getattr(opponent, resource)
        new_value = max(0, current_value - 8)
        reduction = current_value - new_value
        setattr(opponent, resource, new_value)
        debug_print(f"Reduced opponent's {resource} from {current_value} to {new_value}")
    elif card.name == "Curse":
        for attr in ["builders", "soldiers", "mages"]:
            setattr(player, attr, getattr(player, attr) + 1)
            setattr(opponent, attr, max(1, getattr(opponent, attr) - 1))
        for attr in ["bricks", "weapons", "crystals"]:
            setattr(player, attr, getattr(player, attr) + 1)
            setattr(opponent, attr, max(0, getattr(opponent, attr) - 1))
        player.tower_height += 1
        if player.tower_height >= TOWER_WIN_HEIGHT:
            win_by_height = True
        opponent.tower_height = max(0, opponent.tower_height - 1)
        if opponent.tower_height <= 0:
            win_by_destruction = True

    debug_print(f"Player resources after: Bricks: {player.bricks}, Weapons: {player.weapons}, Crystals: {player.crystals}")
    debug_print(f"Opponent resources after: Bricks: {opponent.bricks}, Weapons: {opponent.weapons}, Crystals: {opponent.crystals}")
    debug_print(f"Player tower height: {player.tower_height}, Fence height: {player.fence_height}")
    debug_print(f"Opponent tower height: {opponent.tower_height}, Fence height: {opponent.fence_height}")

    player.cards.remove(card)
    player.draw_card()

    if win_by_height and win_by_destruction:
        return "double_win"
    elif win_by_height or win_by_destruction:
        return "win"
    else:
        return True



def smart_bot_play(player, opponent):
    debug_print("Computer is deciding which card to play")
    playable_cards = [card for card in player.cards if player.can_afford(card)]

    if SHOW_COMPUTER_CARDS:
        debug_print(f"Playable cards: {[card.name for card in playable_cards]}")


    # Check for panic mode
    if is_panic_mode(player, opponent):
        debug_print("PANIC MODE ACTIVATED!")
        panic_action = handle_panic_mode(player, opponent, playable_cards)
        if panic_action:
            return panic_action


    action = "play"  # Default action is now play
    cards = None

    if playable_cards:
        # 1. Curse (only if human has 2+ mages)
        curse_card = next((card for card in playable_cards if card.name == "Curse"), None)
        if curse_card and opponent.mages >= 2:
            action = "play"
            cards = curse_card

        # 2. Thief (only if human has 5+ crystals and >5 other resources)
        elif next((card for card in playable_cards if card.name == "Thief"), None) and opponent.crystals >= 5 and (opponent.bricks + opponent.weapons) > 5:
            action = "play"
            cards = next(card for card in playable_cards if card.name == "Thief")

        # 3. Add Mage
        elif next((card for card in playable_cards if card.name == "Sorcerer"), None):
            action = "play"
            cards = next(card for card in playable_cards if card.name == "Sorcerer")

        # 4. Add Soldier
        elif next((card for card in playable_cards if card.name == "Recruit"), None):
            action = "play"
            cards = next(card for card in playable_cards if card.name == "Recruit")

        # 5. Add Builder
        elif next((card for card in playable_cards if card.name == "School"), None):
            action = "play"
            cards = next(card for card in playable_cards if card.name == "School")

        # 6. Crush Crystals (only if human has 8+ crystals)
        elif next((card for card in playable_cards if card.name == "Crush Crystals"), None) and opponent.crystals >= 8:
            action = "play"
            cards = next(card for card in playable_cards if card.name == "Crush Crystals")

        # 7. Conjure Crystals
        elif next((card for card in playable_cards if card.name == "Conjure Crystals"), None):
            action = "play"
            cards = next(card for card in playable_cards if card.name == "Conjure Crystals")

        # 8. Saboteur (only if human has 4+ of each resource)
        elif next((card for card in playable_cards if card.name == "Saboteur"), None) and opponent.bricks >= 4 and opponent.weapons >= 4 and opponent.crystals >= 4:
            action = "play"
            cards = next(card for card in playable_cards if card.name == "Saboteur")

        # 9. Attack cards (if opponent's fence is low)
        elif opponent.fence_height < 10:
            attack_cards = [card for card in playable_cards if "attack" in card.effect]
            if attack_cards:
                action = "play"
                cards = max(attack_cards, key=lambda c: int(c.effect.split()[1]))

        # 10. Defense cards (if own tower is low)
        elif player.tower_height < 40:
            defense_cards = [card for card in playable_cards if "castle +" in card.effect or "fence +" in card.effect]
            if defense_cards:
                def get_defense_value(card):
                    total_value = 0
                    effects = card.effect.split(';')
                    for effect in effects:
                        effect = effect.strip()
                        if "castle +" in effect:
                            total_value += int(effect.split("castle +")[1].split()[0])
                        elif "fence +" in effect:
                            total_value += int(effect.split("fence +")[1].split()[0])
                    return total_value
                action = "play"
                cards = max(defense_cards, key=get_defense_value)

        # 11. Resource stealing or destruction
        elif any(card for card in playable_cards if card.name in ["Thief", "Saboteur", "Crush Bricks", "Crush Weapons", "Crush Crystals"]):
            action = "play"
            cards = next(card for card in playable_cards if card.name in ["Thief", "Saboteur", "Crush Bricks", "Crush Weapons", "Crush Crystals"])

        # If no specific strategy applies, choose a random card
        else:
            action = "play"
            cards = random.choice(playable_cards)



    # If no card was chosen and passes are not allowed, choose a card to discard
    if not cards and not PASSES_ALLOWED:
        action = "discard"
        cards = choose_cards_to_discard(player)
    
    # If passes are allowed and no action was taken, pass
    if not cards and PASSES_ALLOWED:
        action = "pass"
        cards = []

    return action, cards



def choose_cards_to_discard(player):
    absolutely_never_discard = [
        "Curse", "Sorcerer", "Recruit", "School", "Thief"
    ]
    
    prefer_not_to_discard = [
        "Conjure Crystals", "Crush Crystals", "Swat", "Wain", "Conjure Weapons", 
        "Conjure Bricks", "Fence", "Banshee", "Fort", "Pixies", "Defence", 
        "Reserve", "Saboteur", "Crush Weapons"
    ]
    
    discard_priority = [
        "Wall", "Base", "Tower", "Babylon",
        "Archer", "Knight", "Rider", "Platoon", "Attack",
        "Dragon", "Crush Bricks"
    ] + prefer_not_to_discard + absolutely_never_discard
    
    # Remove absolutely_never_discard cards from consideration
    available_cards = [card for card in player.cards if card.name not in absolutely_never_discard]
    
    if not available_cards:
        debug_print("Computer has only absolutely essential cards. Forced to discard one.")
        return [random.choice(player.cards)]
    
    # Discard cards not in the prefer_not_to_discard list first
    cards_to_discard = [card for card in available_cards if card.name not in prefer_not_to_discard]
    
    if not cards_to_discard:
        # If we must discard a preferred card, choose the least valuable
        cards_to_discard = available_cards
    
    sorted_cards = sorted(cards_to_discard, key=lambda card: discard_priority.index(card.name))
    return sorted_cards[:min(len(sorted_cards), DISCARD_MAX)]



def is_panic_mode(player, opponent):
    # Previous checks
    if opponent.tower_height >= TOWER_WIN_HEIGHT - 5:
        debug_print("Panic: Opponent close to winning height")
        return True
    
    potential_win_cards = ["Fort", "Babylon", "Wain"]
    for card_name in potential_win_cards:
        card_template = next((ct for ct in CARD_TYPES if ct.name == card_name), None)
        if card_template and opponent.can_afford(card_template.create_card(opponent)):
            debug_print(f"Panic: Opponent can afford {card_name}")
            return True
    
    if opponent.bricks >= 30 or opponent.weapons >= 30 or opponent.crystals >= 30:
        debug_print("Panic: Opponent has high resources")
        return True
    
    # New vulnerability checks
    if player.tower_height <= 10 and opponent.weapons >= 15:  # Assuming SWAT costs 15 weapons
        debug_print("Panic: Vulnerable to SWAT")
        return True
    
    total_defense = player.tower_height + player.fence_height
    if total_defense <= 32 and opponent.weapons >= 28:  # Assuming Banshee attack is 32 and costs 28 weapons
        debug_print("Panic: Vulnerable to Banshee")
        return True
    
    if total_defense <= 25 and opponent.crystals >= 21:  # Assuming Dragon attack is 25 and costs 21 crystals
        debug_print("Panic: Vulnerable to Dragon")
        return True
    
    return False


def handle_panic_mode(player, opponent, playable_cards):
    total_defense = player.tower_height + player.fence_height
    
    def parse_effect(effect, keyword):
        for part in effect.split(';'):
            if keyword in part:
                return int(part.split(keyword)[1].split()[0])
        return 0

    # Enhanced priority actions in panic mode
    panic_priorities = [
        ("Emergency Defense", lambda c: (parse_effect(c.effect, "castle +") + parse_effect(c.effect, "fence +")) > 
                                        (TOWER_WIN_HEIGHT - player.tower_height)),
        ("SWAT", lambda c: c.name == "Swat"),
        ("Crush Weapons", lambda c: c.name == "Crush Weapons" and opponent.weapons >= 15),
        ("Crush Crystals", lambda c: c.name == "Crush Crystals" and opponent.crystals >= 21),
        ("Thief", lambda c: c.name == "Thief"),
        ("Saboteur", lambda c: c.name == "Saboteur"),
        ("Strong Defense", lambda c: parse_effect(c.effect, "castle +") >= 8 or parse_effect(c.effect, "fence +") >= 8),
        ("Any Defense", lambda c: "castle +" in c.effect or "fence +" in c.effect),
        ("Attack", lambda c: "attack" in c.effect),
    ]
    
    for priority_name, condition in panic_priorities:
        matching_cards = [card for card in playable_cards if condition(card)]
        if matching_cards:
            if priority_name in ["Emergency Defense", "Strong Defense", "Any Defense"]:
                chosen_card = max(matching_cards, key=lambda c: parse_effect(c.effect, "castle +") + 
                                                                parse_effect(c.effect, "fence +"))
            elif "attack" in priority_name.lower():
                chosen_card = max(matching_cards, key=lambda c: parse_effect(c.effect, "attack "))
            else:
                chosen_card = matching_cards[0]  # For non-numeric effects, just choose the first matching card
            
            debug_print(f"Panic mode: Choosing {priority_name} action with card {chosen_card.name}")
            return "play", chosen_card
    
    debug_print("No suitable panic action found. Falling back to normal strategy.")
    return None



def play_turn(player, opponent):
    debug_print(f"Starting turn for {'Human' if player.is_human else 'Computer'}")
    debug_print(f"Player resources: Bricks: {player.bricks}, Weapons: {player.weapons}, Crystals: {player.crystals}")

    global current_player, center_card, game_just_loaded

    if not game_just_loaded:
        player.resources_added_this_turn = False
        player.add_resources()
    else:
        game_just_loaded = False

    if DEBUG_MODE:
        debug_center_card_y = DEBUG_CARD_PLAY_Y
    else:
        debug_center_card_y = CENTER_CARD_Y

    draw_game(CENTER_CARD_X, debug_center_card_y)

    if player.is_human:
        # Human player's turn
        waiting_for_move = True
        cards_to_discard = []
        while waiting_for_move:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    save_game()
                    return False  # End the game
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    # Check if the click is in the player indicator area
                    if y < 50 and WIDTH // 2 - 100 < x < WIDTH // 2 + 100:
                        if event.button == 3 and PASSES_ALLOWED:  # only pass, if right-clicked AND if passes are allowed
                            pass_sound_high.play()
                            pygame.time.wait(100)  # Wait for 100ms
                            pass_sound_low.play()
                            debug_print("Human player passed their turn")
                            waiting_for_move = False
                    elif 0 <= (x - 10) // (CARD_WIDTH + 10) < len(player.cards) and y > HEIGHT - CARD_HEIGHT - 10:
                        card_index = (x - 10) // (CARD_WIDTH + 10)
                        if event.button == 1:  # Left click
                            if not cards_to_discard:  # Only allow playing if no cards are selected for discard
                                if player.can_afford(player.cards[card_index]):
                                    card = player.cards[card_index]
                                    animate_card_to_center(card, 10 + card_index * (CARD_WIDTH + 10), HEIGHT - CARD_HEIGHT - 10)
                                    result = play_card(player, opponent, card)
                                    if result in ["win", "double_win"]:
                                        return result
                                    waiting_for_move = False
                        elif event.button == 3:  # Right click
                            card = player.cards[card_index]
                            if card in cards_to_discard:
                                cards_to_discard.remove(card)
                                card.selected_for_discard = False
                            elif len(cards_to_discard) < DISCARD_MAX:
                                cards_to_discard.append(card)
                                card.selected_for_discard = True
                    elif event.button == 3 and y > HEIGHT * 2 // 3:  # Right click in green area
                        if cards_to_discard:
                            for card in cards_to_discard:
                                player.cards.remove(card)
                                player.draw_card()
                            cards_to_discard = []
                            waiting_for_move = False
            
            draw_game(CENTER_CARD_X, debug_center_card_y)
            clock.tick(60)

    else:
        debug_print("Computer is taking its turn")
        # Computer player's turn (Smart Bot)
        action, cards = smart_bot_play(player, opponent)
        if action == "pass":
            pass_sound_high.play()
            pygame.time.wait(100)  # Wait for 100ms
            pass_sound_low.play()
            debug_print("Computer player passed their turn")
        elif action == "discard":
            center_card = cards  # Store discarded cards
            for card in cards:
                player.cards.remove(card)
                player.draw_card()
            
            if DEBUG_MODE:
                # Display discarded cards
                draw_game(CENTER_CARD_X, debug_center_card_y)
                pygame.time.wait(3000)  # Wait for 3 seconds to show discarded cards
            
            center_card = None  # Clear center card after displaying
        else:  # action == "play"
            card = cards  # In this case, cards is actually a single card
            card_index = player.cards.index(card)
            animate_card_to_center(card, WIDTH - (CARD_WIDTH + 10) * (MAX_CARDS - card_index), HEIGHT * 2 // 3 + 10)
            result = play_card(player, opponent, card)
            if result in ["win", "double_win"]:
                return result
        
        pygame.time.wait(1000)  # Wait for 1 second to make the computer's move visible

    debug_print(f"Ending turn for {'Human' if player.is_human else 'Computer'}")
    current_player = opponent
    return True



def display_end_game_message(winner):
    global game_over, running  # Add running to the global variables

    if game_over:
        return  # If the game is already over, don't display the message or update the score again

    game_over = True  # Set the game as over

    font = pygame.font.Font(None, 74)
    if winner == "Computer":
        text = font.render("Computer wins!", True, (255, 0, 0))  # Red text
    else:
        text = font.render("Human wins!", True, (0, 255, 0))  # Green text
    
    text_rect = text.get_rect(center=(WIDTH/2, 25))
    
    # Update and read the score
    score = read_score()
    score[winner.lower()] += 1
    write_score(score)
    
    # Create score text
    score_font = pygame.font.Font(None, 24)
    score_text = score_font.render(f"Ongoing match score: {score['human']} - {score['computer']}", True, BLACK)
    score_rect = score_text.get_rect(center=(WIDTH/2, 75))
    
    # Draw the current game state
    draw_game(CENTER_CARD_X, CENTER_CARD_Y)
    
    # Draw a semi-transparent background for the text to ensure readability
    background_rect = pygame.Rect(0, 0, WIDTH, 100)
    background_surface = pygame.Surface((WIDTH, 100), pygame.SRCALPHA)
    pygame.draw.rect(background_surface, (0, 0, 0, 128), background_rect)
    screen.blit(background_surface, (0, 0))
    
    # Draw the win message and score
    screen.blit(text, text_rect)
    screen.blit(score_text, score_rect)
    
    # Add instruction text
    instruction_font = pygame.font.Font(None, 36)
    instruction_text = instruction_font.render("Click or press any key to exit", True, WHITE)
    instruction_rect = instruction_text.get_rect(center=(WIDTH/2, HEIGHT - 50))
    screen.blit(instruction_text, instruction_rect)
    
    pygame.display.flip()
    
    # Wait for a key press or mouse click
    waiting_for_input = True
    while waiting_for_input:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                waiting_for_input = False
                running = False  # Set running to False to end the game
            elif event.type == pygame.QUIT:
                waiting_for_input = False
                running = False
                pygame.quit()
                return

    # Small delay to prevent accidental double-clicks from immediately starting a new game
    pygame.time.wait(300)



# Main game loop
running = True
game_over = False
clock = pygame.time.Clock()

# Check for savegame and ask to load
if os.path.exists('cw_savegame.pkl'):
    screen.fill(SKY_BLUE)
    font = pygame.font.Font(None, 36)
    text = font.render("Load saved game? (Y/N)", True, BLACK)
    text_rect = text.get_rect(center=(WIDTH/2, HEIGHT/2))
    screen.blit(text, text_rect)
    pygame.display.flip()
    
    waiting_for_input = True
    while waiting_for_input:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_y:
                    load_game()
                    waiting_for_input = False
                elif event.key == pygame.K_n:
                    waiting_for_input = False
            elif event.type == pygame.QUIT:
                running = False
                waiting_for_input = False



while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_game()
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                save_game()
                running = False

    if not game_over:
        if current_player.is_human:
            result = play_turn(human_player, computer_player)
        else:
            result = play_turn(computer_player, human_player)
        
        if result == "win":
            winner = "Human" if current_player.is_human else "Computer"
            display_end_game_message(winner)
        elif result == "double_win":
            winner = "Human" if current_player.is_human else "Computer"
            display_end_game_message(f"{winner} (Double Win)")
        elif result == False:
            running = False
        
        # Check win conditions for tower height
        if not game_over:
            if human_player.tower_height >= TOWER_WIN_HEIGHT:
                display_end_game_message("Human")
            elif computer_player.tower_height >= TOWER_WIN_HEIGHT:
                display_end_game_message("Computer")
            elif human_player.tower_height <= 0:
                display_end_game_message("Computer")
            elif computer_player.tower_height <= 0:
                display_end_game_message("Human")

        if DEBUG_MODE:
            debug_center_card_y = HEIGHT // 2 - CARD_HEIGHT // 2 - 100  # Adjust this value as needed
        else:
            debug_center_card_y = CENTER_CARD_Y

        draw_game(CENTER_CARD_X, debug_center_card_y)

    clock.tick(60)

pygame.quit()



