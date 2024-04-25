import dataclasses

import yaml


@dataclasses.dataclass
class Question:
    id: str
    question: str
    options: list
    conditions: list = None

    def score(self, answer):
        for option in self.options:
            if option.short == answer:
                return option.score
        raise ValueError(f'Invalid answer: {answer}')

    def max_score(self):
        scores = [option.score for option in self.options if option.score]
        if scores:
            return max(scores)

    def is_relevant(self, answers):
        if not self.conditions:
            return True

        for c in self.conditions:
            id, required_answer = c[0], c[1]
            if id not in answers:
                return False
            if answers[id][0] != required_answer:
                return False
        return True


@dataclasses.dataclass
class Option:
    short: str
    long: str
    score: int = None


def y_n(y_score=None, n_score=None):
    return [Option('y', 'Yes', y_score), Option('n', 'No', n_score)]


@dataclasses.dataclass
class Questionnaire:
    questions: list[Question]
    answers: dict[str, tuple[str, int, int]] = dataclasses.field(
        default_factory=dict
    )

    def next_question(self):
        for q in self.questions:
            if q.id not in self.answers and q.is_relevant(self.answers):
                return q
        return None

    def answer(self, question_id, answer):
        question = next(filter(lambda q: q.id == question_id, self.questions))
        self.answers[question_id] = (answer,
                                     question.score(answer),
                                     question.max_score())

    def score(self):
        total_score = sum([
            score for _, score, _ in self.answers.values() if score
        ])
        max_score = sum([
            max_score for _, _, max_score in self.answers.values() if max_score
        ])
        return round(total_score / max_score * 100)

    def recommendations(self):
        deltas = [
            (id, max - score) for id, (_, score, max) in self.answers.items()
            if max
        ]
        deltas = [(id, delta) for id, delta in deltas if delta > 0]
        deltas = sorted(deltas, key=lambda x: x[1], reverse=True)
        q_map = {q.id: q for q in self.questions}
        return [q_map[id].question for id, _ in deltas[:3]]


def load_question_data():
    with open('asaa/questions.yaml') as f:
        return yaml.safe_load(f)


def load_questions():
    return [
        Question(
            id=item['id'],
            question=item['question'],
            conditions=[(c['question_id'], c['answer'])
                        for c in item.get('conditions', [])],
            options=[Option(o['short'], o['long'], o.get('score', None))
                     for o in item['options']]
        ) for item in load_question_data()['questions']
    ]


def create_questionnaire():
    return Questionnaire(load_questions())
