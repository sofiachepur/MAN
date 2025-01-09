from flask import Flask, request, render_template

app = Flask(__name__)


def parse_input(data):
    lines = data.strip().split("\n")
    # Перевірка правильності введення
    if not lines[0].startswith("Кількість голосів:"):
        raise ValueError("Перша строка повинна починатися з 'Кількість голосів:'")
    # Отримуємо кількість голосів
    vote_counts = list(map(int, lines[0].replace("Кількість голосів:", "").strip().split()))
    if not lines[1].startswith("Впорядкування кандидатів:"):
        raise ValueError("Друга строка повинна починатися з 'Впорядкування кандидатів:'")
    # Отримуємо впорядкування кандидатів
    rankings = [line.strip().split() for line in lines[2:]]
    if len(vote_counts) != len(rankings):
        raise ValueError("Кількість голосів не відповідає кількості впорядкувань.")
    return vote_counts, rankings


# Абсолютна більшість (з першого рядка впорядкування)
def absolute_majority(vote_counts, rankings):
    # Тільки перший рядок з впорядкуванням кандидатів
    first_line_ranking = rankings[0]
    # Підрахунок голосів для кожного кандидата на першому місці
    total_votes = sum(vote_counts)  # Загальна кількість голосів
    aggregated_results = {}

    # Підрахунок загальних голосів для кожного кандидата з урахуванням повторень
    for i, candidate in enumerate(first_line_ranking):
        if candidate not in aggregated_results:
            aggregated_results[candidate] = 0
        aggregated_results[candidate] += vote_counts[i]

    # Перевіряємо, чи є кандидат з більш ніж половиною голосів
    for candidate, count in aggregated_results.items():
        if count > total_votes / 2:
            return candidate

    # Якщо такого кандидата немає
    return "немає"


# Відносна більшість (з першого рядка впорядкування)
def relative_majority(vote_counts, rankings):
    # Тільки перший рядок з впорядкуванням кандидатів
    first_line_ranking = rankings[0]
    # Підрахунок голосів для кожного кандидата на першому місці
    aggregated_results = {}

    # Підрахунок загальних голосів для кожного кандидата з урахуванням повторень
    for i, candidate in enumerate(first_line_ranking):
        if candidate not in aggregated_results:
            aggregated_results[candidate] = 0
        aggregated_results[candidate] += vote_counts[i]

    # Знаходимо максимальну кількість голосів
    max_votes = max(aggregated_results.values())

    # Переможці з найбільшою кількістю голосів
    winners = [candidate for candidate, votes in aggregated_results.items() if votes == max_votes]

    # Повертаємо список переможців або одного, якщо їх лише один
    return winners if len(winners) > 1 else winners[0]


def borda_method(vote_counts, rankings):
    # Перетворення ранжувань зі стовпців у рядки
    rankings_by_columns = list(zip(*rankings))  # Транспонування

    # Унікальні кандидати
    candidates = {candidate for ranking in rankings_by_columns for candidate in ranking}
    borda_scores = {candidate: 0 for candidate in candidates}

    # Підрахунок очок
    for i, ranking in enumerate(rankings_by_columns):
        for j, candidate in enumerate(ranking):
            borda_scores[candidate] += vote_counts[i] * (len(ranking) - j - 1)

    # Повернення кандидата з максимальним балом
    return max(borda_scores, key=borda_scores.get)


def pairwise_comparison(candidate, other_candidate, rankings, vote_counts):
    candidate_wins = 0
    other_candidate_wins = 0
    for i, ranking in enumerate(rankings):
        # Якщо обидва кандидати є в списку
        if candidate in ranking and other_candidate in ranking:
            if ranking.index(candidate) < ranking.index(other_candidate):
                candidate_wins += vote_counts[i]
            else:
                other_candidate_wins += vote_counts[i]
        # Якщо один кандидат відсутній у списку
        elif candidate in ranking:
            candidate_wins += vote_counts[i]  # Вважаємо перемогу кандидата
        elif other_candidate in ranking:
            other_candidate_wins += vote_counts[i]  # Вважаємо перемогу іншого кандидата
    return candidate_wins, other_candidate_wins


def condorcet(vote_counts, rankings):
    candidates = {candidate for ranking in rankings for candidate in ranking}
    defeats = {candidate: 0 for candidate in candidates}
    for candidate in candidates:
        for other_candidate in candidates:
            if candidate != other_candidate:
                candidate_wins, other_candidate_wins = pairwise_comparison(candidate, other_candidate, rankings,
                                                                           vote_counts)
                if candidate_wins > other_candidate_wins:
                    defeats[candidate] += 1
                elif other_candidate_wins > candidate_wins:
                    defeats[other_candidate] += 1
    max_wins = max(defeats.values())
    winners = sorted([candidate for candidate, wins in defeats.items() if wins == max_wins])
    if len(winners) > 1:
        return winners[0]
    return "немає"


def copeland(vote_counts, rankings):
    candidates = {candidate for ranking in rankings for candidate in ranking}
    scores = {candidate: 0 for candidate in candidates}
    for candidate in candidates:
        for other_candidate in candidates:
            if candidate != other_candidate:
                candidate_wins, other_candidate_wins = pairwise_comparison(candidate, other_candidate, rankings,
                                                                           vote_counts)
                if candidate_wins > other_candidate_wins:
                    scores[candidate] += 1
                elif other_candidate_wins > candidate_wins:
                    scores[other_candidate] += 1
    max_score = max(scores.values())
    winners = sorted([candidate for candidate, score in scores.items() if score == max_score])
    if len(winners) > 1:
        return winners[0]
    return "немає"


def simpson(vote_counts, rankings):
    candidates = {candidate for ranking in rankings for candidate in ranking}
    simpson_scores = {candidate: 0 for candidate in candidates}
    for i, ranking in enumerate(rankings):
        for j, candidate in enumerate(ranking):
            simpson_scores[candidate] += vote_counts[i] * (len(ranking) - j - 1) * (len(ranking) - j)
    return max(simpson_scores, key=simpson_scores.get)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        data = request.form["votes"]
        method = request.form["method"]
        try:
            vote_counts, rankings = parse_input(data)
            if method == "absolute_majority":
                result = absolute_majority(vote_counts, rankings)
            elif method == "relative_majority":
                result = relative_majority(vote_counts, rankings)
            elif method == "borda":
                result = borda_method(vote_counts, rankings)
            elif method == "condorcet":
                result = condorcet(vote_counts, rankings)
            elif method == "copeland":
                result = copeland(vote_counts, rankings)
            elif method == "simpson":
                result = simpson(vote_counts, rankings)
            else:
                result = "Невідомий метод"
            return render_template("results.html", result=result)
        except Exception as e:
            return render_template("index.html", error=str(e))
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
