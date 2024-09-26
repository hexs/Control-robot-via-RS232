import pygame
import pygame_gui
import requests
from pygame_gui.core import ObjectID


class Control_Robot_Window:
    def __init__(self, rect=None, manager=None):
        self.rect = pygame.Rect((50, 50), (600, 300)) if rect is None else rect
        self.manager = manager
        self.url = 'http://127.0.0.1:5000'
        self.window = pygame_gui.elements.UIWindow(
            self.rect, self.manager,
            window_display_title='Robot Control Panel'
        )
        self.current_position_vel = {f'0{i}': 0 for i in range(1, 5)}
        self.set_buttons()

    def set_buttons(self):
        button_width, button_height = 100, 30
        label_width = 80
        jog_button_width = 40

        # Top row buttons
        self.top_buttons = [
            ('alarm_reset', 'Alarm Reset'),
            ('servo_on', 'Servo ON'),
            ('servo_off', 'Servo OFF'),
            ('home', 'Home'),
            ('current_position', 'Current Position')
        ]

        for i, (name, text) in enumerate(self.top_buttons):
            setattr(self, f'{name}_button', pygame_gui.elements.UIButton(
                pygame.Rect((5 + i * (button_width + 5), 5), (button_width, button_height)),
                text, container=self.window
            ))

        # Jog controls
        for i in range(1, 5):
            setattr(self, f's{i}_label', pygame_gui.elements.UILabel(
                pygame.Rect((5, 40 + (i - 1) * 35), (label_width, button_height)),
                f'S{i}: 0', container=self.window
            ))
            setattr(self, f'l{i}_button', pygame_gui.elements.UIButton(
                pygame.Rect((label_width + 10, 40 + (i - 1) * 35), (jog_button_width, button_height)),
                '<', container=self.window,
                object_id=ObjectID(class_id=f'@l{i}_button', object_id=f'#l{i}')
            ))
            setattr(self, f'r{i}_button', pygame_gui.elements.UIButton(
                pygame.Rect((label_width + jog_button_width + 15, 40 + (i - 1) * 35),
                            (jog_button_width, button_height)),
                '>', container=self.window,
                object_id=ObjectID(class_id=f'@r{i}_button', object_id=f'#r{i}')
            ))

        # Move To and Set To controls
        self.move_to_entry = pygame_gui.elements.UITextEntryLine(
            pygame.Rect((5, 200), (button_width, button_height)),
            container=self.window, initial_text='0'
        )
        self.move_to_button = pygame_gui.elements.UIButton(
            pygame.Rect((button_width + 10, 200), (button_width, button_height)),
            'Move To', container=self.window
        )
        self.set_to_button = pygame_gui.elements.UIButton(
            pygame.Rect((2 * button_width + 15, 200), (button_width, button_height)),
            'Set To', container=self.window
        )

    def update_position(self, position_vel):
        self.current_position_vel = position_vel
        for i in range(1, 5):
            getattr(self, f's{i}_label').set_text(f"S{i}: {self.current_position_vel[f'0{i}']}")

    def send_request(self, endpoint, method='post', **kwargs):
        try:
            response = getattr(requests, method)(f"{self.url}/api/{endpoint}", **kwargs)
            response.raise_for_status()
            print(f"{endpoint.capitalize()} request sent successfully")
            return response.json() if method == 'get' else None
        except requests.RequestException as e:
            print(f"Error sending {endpoint} request: {e}")
            return None

    def jog_request(self, slave, positive_side, move):
        self.send_request('jog', json={
            "slave": slave,
            "positive_side": positive_side,
            "move": move
        })

    def events(self, events):
        for event in events:
            if event.type == pygame_gui.UI_BUTTON_START_PRESS:
                if event.ui_element in [getattr(self, f'l{i}_button') for i in range(1, 5)]:
                    slave = f"0{event.ui_object_id[-1]}"
                    self.jog_request(slave, False, True)
                elif event.ui_element in [getattr(self, f'r{i}_button') for i in range(1, 5)]:
                    slave = f"0{event.ui_object_id[-1]}"
                    self.jog_request(slave, True, True)

            elif event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element in [getattr(self, f'{d}{i}_button') for d in 'lr' for i in range(1, 5)]:
                    slave = f"0{event.ui_object_id[-1]}"
                    positive_side = event.ui_object_id[-2] == 'r'
                    self.jog_request(slave, positive_side, False)
                elif event.ui_element == self.alarm_reset_button:
                    self.send_request("alarm_reset")
                elif event.ui_element in [self.servo_on_button, self.servo_off_button]:
                    self.send_request("servo", json={"on": event.ui_element == self.servo_on_button})
                elif event.ui_element == self.home_button:
                    self.send_request("home")
                elif event.ui_element == self.current_position_button:
                    self.get_current_position()
                elif event.ui_element == self.move_to_button:
                    self.move_to()
                elif event.ui_element == self.set_to_button:
                    self.set_to()

    def get_current_position(self):
        position = self.send_request('current_position', method='get')
        if position:
            self.update_position(position)

    def move_to(self):
        try:
            row = int(self.move_to_entry.get_text())
            self.send_request("move_to", json={"row": row})
        except ValueError:
            print("Invalid row number")

    def set_to(self):
        print("Set to functionality not implemented yet")


if __name__ == '__main__':
    pygame.init()
    pygame.display.set_caption('Robot Control')
    window_surface = pygame.display.set_mode((800, 600))
    manager = pygame_gui.UIManager((800, 600))

    robot_window = Control_Robot_Window(None, manager)

    background = pygame.Surface((800, 600))
    background.fill(manager.ui_theme.get_colour('dark_bg'))

    clock = pygame.time.Clock()

    running = True
    while running:
        time_delta = clock.tick(60) / 1000.0
        events = pygame.event.get()

        robot_window.events(events)
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            manager.process_events(event)

        manager.update(time_delta)
        window_surface.blit(background, (0, 0))
        manager.draw_ui(window_surface)
        pygame.display.update()
