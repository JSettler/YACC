"""
YACC - Yet Another Castlewars Clone - put under [GNU Affero GPLv3] license
---------------------------------------------------------------------------

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
import logging


# Initialize Pygame
pygame.init()

# Set up the display
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()


DEBUG_MODE = False      # if false: only CRITICAL level events will be logged
SHOW_COMPUTER_CARDS = False  # if true: check if AI works as desired


# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_GREEN = (0, 100, 0)
BLUE_GREY = (100, 100, 150)
BROWN = (139, 69, 19)
SKY_BLUE = (0, 120, 155)  # (135, 206, 235)
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
TOWER_WIN_HEIGHT = 100  # 1000  # 100
MAX_CARDS = 8   # old CW-default: 8   # max.15, due to graphical constraints
DISCARD_MAX = 1    # how many cards a player can throw away at maximum, per each turn  (max: the amount of cards in the hand)

PASSES_ALLOWED = False  # Set this to False if passes are not valid moves


discarded_cards = None


# Add this near the top of your script, with other global variables
game_just_loaded = False


def set_sound_volume(volume):
    for sound in sound_effects.values():
        sound.set_volume(volume)
    pass_sound_high.set_volume(volume)
    pass_sound_low.set_volume(volume)


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

set_sound_volume(0.3)  # Adjust this value between 0.0 and 1.0 to find the right volume


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


    # Draw center card (played by computer) or discarded cards
    if center_card:
        draw_card_on_screen(center_card, center_card_x, center_card_y, show_face=True, playable=True, dimmed=False)
    elif discarded_cards:
        for i, card in enumerate(discarded_cards):
            x = center_card_x - (len(discarded_cards) - 1) * CARD_WIDTH // 2 + i * CARD_WIDTH
            draw_card_on_screen(card, x, center_card_y, show_face=True, playable=False, dimmed=True)
        small_font = pygame.font.Font(None, 20)
        info_text = small_font.render("(computer discarded)", True, BLACK)
        info_rect = info_text.get_rect(center=(WIDTH // 2, center_card_y - 20))
        screen.blit(info_text, info_rect)


    pygame.display.flip()



def save_game():
    game_state = {
        'human_player': human_player,
        'computer_player': computer_player,
        'current_player': current_player,
        'center_card': center_card,
        'discarded_cards': discarded_cards,
        'game_just_loaded': game_just_loaded
    }
    with open('cw_savegame.pkl', 'wb') as f:
        pickle.dump(game_state, f)
    logging.debug("Game saved successfully")


def load_game():
    global human_player, computer_player, current_player, center_card, discarded_cards, game_just_loaded, bot
    try:
        with open('cw_savegame.pkl', 'rb') as f:
            game_state = pickle.load(f)
        
        human_player = game_state['human_player']
        computer_player = game_state['computer_player']
        current_player = game_state['current_player']
        center_card = game_state['center_card']
        discarded_cards = game_state['discarded_cards']
        game_just_loaded = True

        # Recreate the bot with the loaded game state
        bot = SimpleBot(computer_player, human_player)

        logging.debug("Game loaded successfully")
        logging.debug(f"Loaded human player resources - Bricks: {human_player.bricks}, Weapons: {human_player.weapons}, Crystals: {human_player.crystals}")
        logging.debug(f"Loaded computer player resources - Bricks: {computer_player.bricks}, Weapons: {computer_player.weapons}, Crystals: {computer_player.crystals}")
        return True
    except FileNotFoundError:
        logging.debug("No saved game found")
        return False
    except Exception as e:
        logging.error(f"Error loading game: {str(e)}")
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
    # Subtract the cost first
    cost_value = int(card.cost.split()[0])
    cost_type = card.cost.split()[1]
    if cost_type == 'brick':
        player.bricks -= cost_value
    elif cost_type == 'sword':
        player.weapons -= cost_value
    elif cost_type == 'crystal':
        player.crystals -= cost_value
    

    card.play_sound()

    win_by_height = False
    win_by_destruction = False

    effects = card.effect.split(';')
    for effect in effects:
        effect = effect.strip()

        if "castle +" in effect:
            value = int(effect.split("+")[1].split()[0])
            player.tower_height += value

            if player.tower_height >= TOWER_WIN_HEIGHT:
                win_by_height = True
        elif "fence +" in effect:
            value = int(effect.split("+")[1].split()[0])
            player.fence_height += value
        elif "enemy castle" in effect:
            value = int(effect.split("-")[1].split()[0])
            old_height = opponent.tower_height
            opponent.tower_height = max(0, opponent.tower_height - value)

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

        elif "transfer enemy stocks" in effect:     # thief card
            # Store original resource values for player A
            starting_bricks = player.bricks
            starting_weapons = player.weapons
            starting_crystals = player.crystals
            
            # Process bricks
            B_bricks = opponent.bricks
            opponent.bricks = max(0, B_bricks - 5)
            transfer_bricks = min(5, B_bricks)
            sum_bricks = starting_bricks + transfer_bricks
            player.bricks = sum_bricks
            
            # Process weapons
            B_weapons = opponent.weapons
            opponent.weapons = max(0, B_weapons - 5)
            transfer_weapons = min(5, B_weapons)
            sum_weapons = starting_weapons + transfer_weapons
            player.weapons = sum_weapons
            
            # Process crystals
            B_crystals = opponent.crystals
            opponent.crystals = max(0, B_crystals - 5)
            transfer_crystals = min(5, B_crystals)
            sum_crystals = starting_crystals + transfer_crystals
            player.crystals = sum_crystals


        elif "enemy stocks" in effect:
            value = abs(int(effect.split()[-1]))  # Use abs() to ensure a positive value
            for resource in ["bricks", "weapons", "crystals"]:
                current_value = getattr(opponent, resource)
                new_value = max(0, current_value - value)
                reduction = current_value - new_value
                setattr(opponent, resource, new_value)



    # Special card effects
    if card.name in ["Crush Bricks", "Crush Weapons", "Crush Crystals"]:
        resource = card.name.split()[1].lower()
        current_value = getattr(opponent, resource)
        new_value = max(0, current_value - 8)
        reduction = current_value - new_value
        setattr(opponent, resource, new_value)

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


    player.cards.remove(card)
    player.draw_card()

    if win_by_height and win_by_destruction:
        return "double_win"
    elif win_by_height or win_by_destruction:
        return "win"
    else:
        return True



def play_turn(player, opponent):
    global current_player, center_card, game_just_loaded, discarded_cards

    if not game_just_loaded:
        player.resources_added_this_turn = False
        player.add_resources()
    else:
        game_just_loaded = False

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
                    if 0 <= (x - 10) // (CARD_WIDTH + 10) < len(player.cards) and y > HEIGHT - CARD_HEIGHT - 10:
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

        discarded_cards = None  # Clear discarded cards when human makes a move
        center_card = None  # Clear center card when human makes a move

    else:  # Computer's turn
        logging.debug("Computer's turn starting")
        logging.debug(f"Computer resources - Bricks: {player.bricks}, Weapons: {player.weapons}, Crystals: {player.crystals}")
        
        action, card_index = bot.choose_action()

        if action == "play":
            card = player.cards[card_index]
            
            logging.debug(f"Bot decided to play: {card.name}")
            
            if bot.can_afford(card):
                logging.debug(f"Playing card: {card.name}")
                animate_card_to_center(card, WIDTH - (CARD_WIDTH + 10) * (MAX_CARDS - card_index), HEIGHT * 2 // 3 + 10)
                
                logging.debug(f"Resources before playing card - Bricks: {player.bricks}, Weapons: {player.weapons}, Crystals: {player.crystals}")
                
                result = play_card(player, opponent, card)
                
                logging.debug(f"Resources after playing card - Bricks: {player.bricks}, Weapons: {player.weapons}, Crystals: {player.crystals}")
                
                center_card = card
                discarded_cards = None
                if result in ["win", "double_win"]:
                    return result
            else:
                logging.warning(f"Attempted to play unaffordable card: {card.name}")
                action = "discard"

        if action == "discard":
            card_index = bot.choose_discard()[1]
            discarded_card = player.cards[card_index]
            logging.debug(f"Bot is discarding card: {discarded_card.name}")
            player.cards.pop(card_index)
            player.draw_card()
            discarded_cards = [discarded_card]
            center_card = None

        draw_game(CENTER_CARD_X, debug_center_card_y)
        pygame.display.flip()
        pygame.time.wait(1000)

    logging.debug("Turn ended")
    logging.debug(f"Final resources - Bricks: {player.bricks}, Weapons: {player.weapons}, Crystals: {player.crystals}")
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



# possible log levels: DEBUG, INFO, WARNING, ERROR, and CRITICAL

if DEBUG_MODE:
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
else:
    logging.basicConfig(level=logging.CRITICAL, format='%(asctime)s - %(levelname)s - %(message)s')


class SimpleBot:
    def __init__(self, player, opponent):
        self.player = player
        self.opponent = opponent

    def can_afford(self, card):
        cost_value = int(card.cost.split()[0])
        cost_type = card.cost.split()[1]
        
        if cost_type == 'brick':
            return self.player.bricks >= cost_value
        elif cost_type == 'sword':
            return self.player.weapons >= cost_value
        elif cost_type == 'crystal':
            return self.player.crystals >= cost_value
        return False

    def get_playable_cards(self):
        playable = []
        for i, card in enumerate(self.player.cards):
            if self.can_afford(card):
                if card.name == "Reserve" and self.player.fence_height < 4:
                    continue
                playable.append(i)
        return playable

    def is_under_threat(self):
        return (self.opponent.tower_height >= TOWER_WIN_HEIGHT - 20 or 
                self.player.tower_height <= 20 or 
                self.opponent.weapons >= self.player.tower_height + self.player.fence_height)

    def choose_action(self):
        playable_cards = self.get_playable_cards()
        logging.debug(f"Playable cards: {[self.player.cards[i].name for i in playable_cards]}")
        logging.debug(f"Bot resources - Bricks: {self.player.bricks}, Weapons: {self.player.weapons}, Crystals: {self.player.crystals}")
        logging.debug(f"Bot tower: {self.player.tower_height}, Bot fence: {self.player.fence_height}")
        logging.debug(f"Opponent tower: {self.opponent.tower_height}, Opponent weapons: {self.opponent.weapons}")

        if playable_cards:
            try:
                # Prioritize survival if under threat
                if self.is_under_threat():
                    defense_cards = [i for i in playable_cards if "castle +" in self.player.cards[i].effect or "fence +" in self.player.cards[i].effect]
                    if defense_cards:
                        best_defense = max(defense_cards, key=lambda i: int(self.player.cards[i].effect.split("+")[1].split()[0]))
                        logging.debug(f"Playing defense card: {self.player.cards[best_defense].name}")
                        return "play", best_defense

                # Prioritize resource generation if resources are low
                if min(self.player.bricks, self.player.weapons, self.player.crystals) < 20:
                    generator_cards = [i for i in playable_cards if any(x in self.player.cards[i].effect for x in ["builders +", "soldiers +", "mages +"])]
                    if generator_cards:
                        logging.debug(f"Playing generator card: {self.player.cards[generator_cards[0]].name}")
                        return "play", generator_cards[0]

                # Play high-impact cards if not in immediate danger
                if self.player.tower_height > 30 and self.player.tower_height + self.player.fence_height > self.opponent.weapons:
                    high_impact_cards = [i for i in playable_cards if self.player.cards[i].name in ["Curse", "Babylon", "Dragon", "Banshee"]]
                    if high_impact_cards:
                        logging.debug(f"Playing high-impact card: {self.player.cards[high_impact_cards[0]].name}")
                        return "play", high_impact_cards[0]

                # Play cards that damage opponent's castle or resources if we have a good defense
                if self.player.tower_height > 40 and self.player.fence_height > 10:
                    attack_cards = [i for i in playable_cards if "enemy" in self.player.cards[i].effect]
                    if attack_cards:
                        best_attack = max(attack_cards, key=lambda i: int(self.player.cards[i].effect.split()[-1]))
                        logging.debug(f"Playing attack card: {self.player.cards[best_attack].name}")
                        return "play", best_attack

                # If none of the above, play the card that gives the most immediate benefit
                best_card = max(playable_cards, key=lambda i: self.evaluate_card_benefit(self.player.cards[i]))
                logging.debug(f"Playing best benefit card: {self.player.cards[best_card].name}")
                return "play", best_card

            except Exception as e:
                logging.error(f"Error in choose_action: {str(e)}")
                # If there's an error, fall back to playing the first playable card
                logging.debug(f"Falling back to first playable card: {self.player.cards[playable_cards[0]].name}")
                return "play", playable_cards[0]
        
        # If no playable cards, we must discard
        logging.debug("Bot is forced to discard")
        return self.choose_discard()



    def evaluate_card_benefit(self, card):
        benefit = 0
        effects = card.effect.split(';')
        for effect in effects:
            effect = effect.strip()
            if "castle +" in effect:
                benefit += int(effect.split("+")[1].split()[0]) * 2
            elif "fence +" in effect:
                benefit += int(effect.split("+")[1].split()[0])
            elif "attack" in effect:
                benefit += int(effect.split()[-1]) * 1.5
            elif any(x in effect for x in ["builders +", "soldiers +", "mages +"]):
                benefit += 15
            elif "enemy" in effect:
                benefit += int(effect.split()[-1]) * 1.5
        return benefit


    def choose_discard(self):
        cards_to_keep = ["School", "Recruit", "Sorcerer", "Curse", "Babylon", "Dragon", "Banshee"]
        discard_candidates = [i for i, card in enumerate(self.player.cards) if card.name not in cards_to_keep]
        
        logging.debug(f"Discard candidates: {[self.player.cards[i].name for i in discard_candidates]}")
        
        if discard_candidates:
            discard_index = min(discard_candidates, key=lambda i: int(self.player.cards[i].cost.split()[0]))
        else:
            discard_index = min(range(len(self.player.cards)), key=lambda i: int(self.player.cards[i].cost.split()[0]))
        
        logging.debug(f"Bot is discarding card: {self.player.cards[discard_index].name}")
        return "discard", discard_index



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
                    if load_game():
                        bot = SimpleBot(computer_player, human_player)  # Recreate bot with loaded state
                    else:
                        # Initialize a new game if load fails
                        human_player = Player(True)
                        computer_player = Player(False)
                        current_player = human_player
                        bot = SimpleBot(computer_player, human_player)
                        for _ in range(MAX_CARDS):
                            human_player.draw_card()
                            computer_player.draw_card()
                    waiting_for_input = False
                elif event.key == pygame.K_n:
                    # Initialize a new game
                    human_player = Player(True)
                    computer_player = Player(False)
                    current_player = human_player
                    bot = SimpleBot(computer_player, human_player)
                    for _ in range(MAX_CARDS):
                        human_player.draw_card()
                        computer_player.draw_card()
                    waiting_for_input = False
            elif event.type == pygame.QUIT:
                running = False
                waiting_for_input = False
else:
    # Initialize a new game if no save file exists
    human_player = Player(True)
    computer_player = Player(False)
    current_player = human_player
    bot = SimpleBot(computer_player, human_player)
    for _ in range(MAX_CARDS):
        human_player.draw_card()
        computer_player.draw_card()



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


        debug_center_card_y = CENTER_CARD_Y
        draw_game(CENTER_CARD_X, debug_center_card_y)

    clock.tick(60)

pygame.quit()


