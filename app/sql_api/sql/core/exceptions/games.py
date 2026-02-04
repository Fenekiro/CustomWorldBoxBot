class GameNotFoundError(Exception):
    def __init__(self):
        self.message = "Game was not found in database, make sure that game_id is valid"
        super().__init__(self.message)
