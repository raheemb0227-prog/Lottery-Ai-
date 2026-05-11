import pandas as pd
from collections import Counter, defaultdict

class LotteryForecastEngine:
    def __init__(self, df, game="pick3", state=None, draw=None):
        self.df = df.copy()
        self.df["number"] = self.df["number"].astype(str)

        if game == "pick3":
            self.length = 3
            self.max_number = 1000
        elif game == "pick4":
            self.length = 4
            self.max_number = 10000
        else:
            raise ValueError("game must be pick3 or pick4")

        self.game = game
        self.df = self.df[self.df["game"].str.lower() == game.lower()]

        if state:
            self.df = self.df[self.df["state"].str.upper() == state.upper()]

        if draw and draw.lower() != "both":
            self.df = self.df[self.df["draw"].str.lower() == draw.lower()]

        self.df["number"] = self.df["number"].str.zfill(self.length)
        self.numbers = self.df["number"].tolist()

        if len(self.numbers) < 10:
            raise ValueError("Not enough results found. Need at least 10 previous draws.")

    def digit_score(self, number):
        all_digits = Counter("".join(self.numbers))
        recent_digits = Counter("".join(self.numbers[-30:]))
        return sum(all_digits[d] for d in number) + (sum(recent_digits[d] for d in number) * 2)

    def position_score(self, number):
        pos = [Counter() for _ in range(self.length)]
        for n in self.numbers:
            for i, d in enumerate(n):
                pos[i][d] += 1
        return sum(pos[i][d] * 3 for i, d in enumerate(number))

    def pair_score(self, number):
        pairs = Counter()
        for n in self.numbers:
            for i in range(len(n) - 1):
                pairs[n[i:i+2]] += 1
            if len(n) >= 3:
                pairs[n[0] + n[-1]] += 1
        score = 0
        for i in range(len(number) - 1):
            score += pairs[number[i:i+2]] * 2.5
        if len(number) >= 3:
            score += pairs[number[0] + number[-1]] * 1.5
        return score

    def sum_score(self, number):
        sums = Counter(sum(map(int, n)) for n in self.numbers)
        return sums[sum(map(int, number))] * 2

    def root_sum_score(self, number):
        def root(n):
            s = sum(map(int, n))
            while s > 9:
                s = sum(map(int, str(s)))
            return s
        roots = Counter(root(n) for n in self.numbers)
        return roots[root(number)] * 2

    def gap_score(self, number):
        if number not in self.numbers:
            return 12
        last_seen = len(self.numbers) - 1 - self.numbers[::-1].index(number)
        gap = len(self.numbers) - last_seen
        return min(gap / 4, 25)

    def pattern_bonus(self, number):
        score = 0
        if len(set(number)) == 1:
            score += 14
        elif len(set(number)) < len(number):
            score += 8
        if number == number[::-1]:
            score += 6
        digits = list(map(int, number))
        if all(digits[i] + 1 == digits[i+1] for i in range(len(digits)-1)):
            score += 10
        if all(digits[i] - 1 == digits[i+1] for i in range(len(digits)-1)):
            score += 10
        return score

    def markov_score(self, number):
        transitions = defaultdict(Counter)
        for i in range(len(self.numbers) - 1):
            transitions[self.numbers[i]][self.numbers[i + 1]] += 1
        last_num = self.numbers[-1]
        return transitions[last_num][number] * 30

    def total_score(self, number):
        return (
            self.digit_score(number)
            + self.position_score(number)
            + self.pair_score(number)
            + self.sum_score(number)
            + self.root_sum_score(number)
            + self.gap_score(number)
            + self.pattern_bonus(number)
            + self.markov_score(number)
        )

    def predict(self, top_n=25):
        scores = {}
        for i in range(self.max_number):
            number = str(i).zfill(self.length)
            scores[number] = self.total_score(number)
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]

    def boxed(self, top_n=15):
        straight = self.predict(150)
        boxed = {}
        for num, score in straight:
            key = "".join(sorted(num))
            boxed[key] = boxed.get(key, 0) + score
        return sorted(boxed.items(), key=lambda x: x[1], reverse=True)[:top_n]

    def backtest(self, top_n=25, max_tests=100):
        original = self.numbers.copy()
        if len(original) < 60:
            return {"tested_draws": 0, "straight_hit_rate": 0, "boxed_hit_rate": 0}

        start = max(30, len(original) - max_tests)
        straight_hits = 0
        boxed_hits = 0
        total = 0

        for i in range(start, len(original)):
            self.numbers = original[:i]
            actual = original[i]
            preds = [x[0] for x in self.predict(top_n)]
            boxed_preds = {"".join(sorted(x)) for x in preds}

            if actual in preds:
                straight_hits += 1
            if "".join(sorted(actual)) in boxed_preds:
                boxed_hits += 1
            total += 1

        self.numbers = original
        return {
            "tested_draws": total,
            "straight_hit_rate": round((straight_hits / total) * 100, 2),
            "boxed_hit_rate": round((boxed_hits / total) * 100, 2),
        }