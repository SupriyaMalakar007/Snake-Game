import random
import pygame
import sys
import cv2
import mediapipe as mp
import time

from pygame.locals import *

# ---------------- INIT ----------------
pygame.init()

INFO = pygame.display.Info()
WIDTH, HEIGHT = INFO.current_w, INFO.current_h

CELL = 20
FPS = 15

SCREEN = pygame.display.set_mode((WIDTH, HEIGHT), FULLSCREEN)
pygame.display.set_caption("Hand Snake Fullscreen")

CLOCK = pygame.time.Clock()
FONT = pygame.font.Font(None, 50)

# colors
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)

HEAD = 0

# ---------------- CAMERA ----------------
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(3, 640)
cap.set(4, 480)

if not cap.isOpened():
    print("❌ Camera not working")
    sys.exit()

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_draw = mp.solutions.drawing_utils

# ---------------- CONTROL ----------------
prev_x, prev_y = None, None
direction = "RIGHT"
last_change = 0

def get_direction(cx, cy):
    global prev_x, prev_y, direction, last_change

    if prev_x is None:
        prev_x, prev_y = cx, cy
        return direction

    dx = cx - prev_x
    dy = cy - prev_y

    prev_x, prev_y = cx, cy

    if abs(dx) < 25 and abs(dy) < 25:
        return direction

    if time.time() - last_change < 0.15:
        return direction

    new_dir = direction

    if abs(dx) > abs(dy):
        new_dir = "RIGHT" if dx > 0 else "LEFT"
    else:
        new_dir = "DOWN" if dy > 0 else "UP"

    opposite = {
        "LEFT": "RIGHT",
        "RIGHT": "LEFT",
        "UP": "DOWN",
        "DOWN": "UP"
    }

    if new_dir != opposite[direction]:
        direction = new_dir
        last_change = time.time()

    return direction

# ---------------- RESET ----------------
def reset():
    snake = [
        {'x': 20, 'y': 20},
        {'x': 19, 'y': 20},
        {'x': 18, 'y': 20}
    ]

    apple = {
        'x': random.randint(5, WIDTH // CELL - 5),
        'y': random.randint(5, HEIGHT // CELL - 5)
    }

    return snake, apple, 0, "RIGHT"

snake, apple, score, direction = reset()
game_over = False

# ---------------- MAIN LOOP ----------------
while True:

    # -------- EVENTS --------
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()

        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                pygame.quit()
                sys.exit()

            if event.key == K_r and game_over:
                snake, apple, score, direction = reset()
                game_over = False

    # -------- CAMERA --------
    success, frame = cap.read()

    if not success or frame is None:
        print("⚠️ Camera frame failed")
        continue

    frame = cv2.flip(frame, 1)

    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    cx, cy = None, None

    if result.multi_hand_landmarks:
        for handLms in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, handLms, mp_hands.HAND_CONNECTIONS)

            cx = int(handLms.landmark[8].x * w)
            cy = int(handLms.landmark[8].y * h)

    if cx is not None and cy is not None and not game_over:
        get_direction(cx, cy)

    # -------- GAME LOGIC --------
    if not game_over:

        x = snake[HEAD]['x']
        y = snake[HEAD]['y']

        if direction == "RIGHT":
            x += 1
        elif direction == "LEFT":
            x -= 1
        elif direction == "UP":
            y -= 1
        elif direction == "DOWN":
            y += 1

        snake.insert(0, {'x': x, 'y': y})

        # food
        if x == apple['x'] and y == apple['y']:
            score += 1
            apple = {
                'x': random.randint(0, WIDTH // CELL - 1),
                'y': random.randint(0, HEIGHT // CELL - 1)
            }
        else:
            snake.pop()

        # collision
        if (x < 0 or x >= WIDTH // CELL or
            y < 0 or y >= HEIGHT // CELL):
            game_over = True

        for b in snake[1:]:
            if b['x'] == x and b['y'] == y:
                game_over = True

    # -------- DRAW CAMERA --------
    frame = cv2.resize(frame, (WIDTH, HEIGHT))
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
    SCREEN.blit(frame, (0, 0))

    # -------- DRAW SNAKE --------
    for i, part in enumerate(snake):
        color = YELLOW if i == 0 else GREEN
        pygame.draw.rect(
            SCREEN,
            color,
            pygame.Rect(part['x'] * CELL, part['y'] * CELL, CELL, CELL)
        )

    # -------- DRAW APPLE --------
    pygame.draw.rect(
        SCREEN,
        RED,
        pygame.Rect(apple['x'] * CELL, apple['y'] * CELL, CELL, CELL)
    )

    # -------- SCORE --------
    score_text = FONT.render(f"Score: {score}", True, WHITE)
    SCREEN.blit(score_text, (20, 20))

    # -------- GAME OVER --------
    if game_over:
        text = FONT.render("GAME OVER - Press R to Restart", True, WHITE)
        SCREEN.blit(text, (WIDTH//2 - 300, HEIGHT//2))

    pygame.display.update()
    CLOCK.tick(FPS)

# cleanup
cap.release()
cv2.destroyAllWindows()
pygame.quit()
