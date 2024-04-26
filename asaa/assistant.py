import os
import time
import json

import openai

from . import core


client = openai.OpenAI()

model = os.environ.get("ASAA_OPENAI_MODEL", "gpt-3.5-turbo")

questionnaire = core.create_questionnaire()
first_question = questionnaire.next_question()

instructions = """
You are an assistant who helps teams assess and improve the security posture
of their applications.

You will ask the user a series of questions about their application and
collect the answers to those questions before providing the user with an
overall score once all the questions have been answered.

To do this, you will have access to a function called 'next'. This
function will step you through the questions you need to get the user to
answer. The 'next' function also allows you to record the answer to the
current question while fetching the next question.

Along with the next question to be answered, the 'next' function returns a
list of valid answers for that question. Each answer has a 'short' form, which
is the string that must be provided as the answer, and a 'long' form, which is
a more detailed description of the answer. If the answer supplied to the 'next'
function is not one of the valid answers then the 'next' function will return
an error.

When all questions have been answered the 'next' function will return a score
and a list of up to 3 questions. The score is given as a percentage of the
maximum possible total based on the users answers and represents an assessment
of the application's security posture. The list of questions is a list of the
3 questions where an improvement would have the biggest positive impact on the
application's security posture. This response indicates the end of the
assessment - you should present the user with their score as well as providing
some recommendations to the user based on the questions highlighted for
improvement. Please provide specific recommendations based on the questions
highlighted - don't just repeat the questions to the user.

It is important that you do not misinterpret the answers the user provides. If
there is any ambiguity in the answers the user provides you should not assume
their meaning; instead you should ask the user to clarify their answer.

Introduce yourself as the Application Secuity Assessment Assistant and explain
that you will ask a series of questions to understand the security posture of
the users app.
"""

instructions += f"Start with the first question which is: '{first_question}'"

assistant = client.beta.assistants.create(
    name='assistant',
    instructions=instructions,
    model=model,
    tools=[{
        'type': 'function',
        'function': {
            'name': 'next',
            'parameters': {
                'type': 'object',
                'properties': {
                    'question_id': {
                        'type': 'string',
                        'description': ('The ID of the question that this '
                                        'answer relates to'),
                        'example': 'AUTH_REQUIRED'
                    },
                    'answer': {
                        'type': 'string',
                        'description': 'The answer to the question',
                        'example': 'y'
                    }
                }
            },
            'description': ('Records the answer if provided, and returns the '
                            'next relevant question. If all questions have '
                            'been answered then an overall score is returned, '
                            'together with the top 3 questions where an '
                            'improvement would have the biggest positive '
                            'impact on the apps security posture.')
        }
    }]
)

thread = client.beta.threads.create()


def next(question_id, answer):
    try:
        questionnaire.answer(question_id, answer)
    except ValueError:
        return {
            'error': 'Invalid answer'
        }
    next_question = questionnaire.next_question()
    if next_question:
        return {
            'question': next_question.question,
            'options': [{
                'short': o.short,
                'long': o.long,
            } for o in next_question.options],
            'question_id': next_question.id,
        }
    else:
        return {
            'score': questionnaire.score(),
            'recommendations': questionnaire.recommendations()
        }


def wait_for(run):
    while run.status in ['queued', 'in_progress', 'cancelling']:
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
    return run


def call(fn):
    args = json.loads(fn.arguments)
    if fn.name == 'next':
        question_id = args.get('question_id', None)
        answer = args.get('answer', None)
        return next(question_id=question_id, answer=answer)
    raise Exception(f'Unknown function {fn.name}')


def run_assistant():
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id
    )
    run = wait_for(run)
    if run.status == 'completed':
        for msg in client.beta.threads.messages.list(thread_id=thread.id):
            return msg.content[0].text.value
    elif run.status == 'requires_action':
        tool_outputs = [
            (tc.id, call(tc.function))
            for tc in run.required_action.submit_tool_outputs.tool_calls
            if tc.type == 'function'
        ]
        run = client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread.id,
            run_id=run.id,
            tool_outputs=[{
                'tool_call_id': tc_id,
                'output': json.dumps(tc_output)
            } for tc_id, tc_output in tool_outputs]
        )
        run = wait_for(run)

        if run.status == 'completed':
            for msg in client.beta.threads.messages.list(thread_id=thread.id):
                return msg.content[0].text.value
        else:
            raise Exception(f'Unexpected run status {run.status}')
    else:
        raise Exception(f'Unexpected run status {run.status}')


def start():
    return run_assistant()


def process_response(response):
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role='user',
        content=response
    )
    return run_assistant()
