from asaa import core

import pytest


@pytest.fixture
def questionnaire():
    return core.create_questionnaire()


def test_include_conditional_question(questionnaire):
    question = questionnaire.next_question()
    assert question.id == 'AUTHN_REQUIRED'

    questionnaire.answer(question.id, "y")
    next_question = questionnaire.next_question()
    assert next_question.id == 'AUTHN_OIDC'


def test_exclude_conditional_question(questionnaire):
    question = questionnaire.next_question()
    assert question.id == 'AUTHN_REQUIRED'

    questionnaire.answer(question.id, "n")
    next_question = questionnaire.next_question()
    assert next_question.id == 'SAST'
