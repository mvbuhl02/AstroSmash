class ScoreManager:
    def __init__(self):
        self.score = 0
        self.high_score = 0
        self.wave = 1
        self.load_high_score()
        
    def load_high_score(self):
        try:
            with open('highscore.dat', 'rb') as f:
                self.high_score = int.from_bytes(f.read(), 'big')
        except:
            self.high_score = 0
            
    def save_high_score(self):
        if self.score > self.high_score:
            self.high_score = self.score
            with open('highscore.dat', 'wb') as f:
                f.write(self.high_score.to_bytes(4, 'big'))
    
    def increase_wave(self):
        self.wave += 1
        
    def add_score(self, points):
        self.score += points