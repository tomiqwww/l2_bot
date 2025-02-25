from app.handlers.base import BaseHandler

STATE_IDLE = 0
STATE_TARGET_PET = 1
STATE_KILL_PET = 2
STATE_RES_PET = 3
STATE_RESUME_FARM = 4
KILL_PET_MANA_LIMIT = 7

PET_TAG = "Pet"


class PetManaHandler(BaseHandler):
    current_state = STATE_IDLE

    def __init__(self, keyboard, pet_status_parser, farm_logic, pausable_logics):
        super().__init__(keyboard)
        self.farm_logic = farm_logic
        self.KEY_TARGET_PET = keyboard.KEY_F7
        self.KEY_KILL_PET = keyboard.KEY_F8
        self.KEY_RES_PET = keyboard.KEY_F9
        self.KEY_CLEAR_TARGET = keyboard.KEY_ESC
        self.pet_status_parser = pet_status_parser
        self.pausable_logics = pausable_logics

        self.pet_hp, self.pet_mp, self.alive = None, None, None

    def _on_tick(self, screen_rgb, current_time, last_action_delta):
        action_performed = self.handle_state(last_action_delta, screen_rgb)

        if action_performed:
            self.last_action_time = current_time

    def handle_state(self, last_action_delta, screen_rgb):
        self.pet_hp, self.pet_mp = self.pet_status_parser.parse_image(screen_rgb)
        self.alive = True if self.pet_hp > 0 else False

        if self.current_state == STATE_IDLE and not self.farm_logic.has_target and (
                self.pet_hp <= 0 or self.pet_mp <= KILL_PET_MANA_LIMIT):

            for logic in self.pausable_logics:
                logic.pause()

            self.current_state = STATE_TARGET_PET
            return True

        if self.current_state == STATE_TARGET_PET and last_action_delta >= 1:
            self.keyboard.press(self.KEY_TARGET_PET)
            self.current_state = STATE_KILL_PET
            self.write_log(PET_TAG, "Pet in target")
            return True

        if self.current_state == STATE_KILL_PET and last_action_delta >= 1:
            self.keyboard.press(self.KEY_KILL_PET)
            self.current_state = STATE_RES_PET
            self.write_log(PET_TAG, "Killing pet")
            return True

        if self.current_state == STATE_RES_PET and last_action_delta >= 1:
            if self.alive:
                return False

            self.write_log(PET_TAG, "Killed. Res the pet")
            self.keyboard.press(self.KEY_RES_PET)
            self.current_state = STATE_RESUME_FARM
            return True

        if self.current_state == STATE_RESUME_FARM and last_action_delta >= 1:
            if not self.alive:
                self.write_log(PET_TAG, "Not alive wait it")
                if last_action_delta > 65:
                    self.current_state = STATE_TARGET_PET
                    return True

                return False

            self.keyboard.press(self.KEY_CLEAR_TARGET)
            self.current_state = STATE_IDLE
            self.write_log(PET_TAG, "Pet is alive. Continue farm")

            for logic in self.pausable_logics:
                logic.resume()

            return True

        return False
