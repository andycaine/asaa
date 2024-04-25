# asaa

The Application Security Assessment Assistant.

## Description

`asaa` helps you evaluate the security posture of your application by chatting with an AI assistant and answering a series of questions. At the end of the assessment `asaa` will give you a score and possibly some recommendations for improving your app's security posture.

At the core of `asaa` is a questionnaire represented as a state machine. The series of questions is determined by the answers given; questions that are not relevant based on the answers previously given are not asked. When all answers are provided, the state machine can provide a score (based on a predetermined weighting for each possible answer), and a list of the (up to) 3 questions where an improvement would have the biggest impact on the overall score.

`asaa` used the ChatGPT Assistants API to provide a conversational interface on top of this state machine. The ChatGPT assistant has access to functions that allow it to fetch the next question to ask, record answers and retrieve the score and top questions for improvement.

## Getting started

You will need an [Open AI API](https://openai.com/blog/openai-api) key to run `asaa`. This needs to be set as an environment variable (I recommend using [direnv](https://direnv.net/)):

```bash
export OPENAI_API_KEY=<YOUR-KEY-HERE>
```

You can also set the model to use:

```bash
export ASAA_OPENAI_MODEL="gpt-4-turbo"
```

The default is `gpt-3.5-turbo`.

I recommend installing into a virtualenv:

```bash
python -mvenv .venv
source .venv/bin/activate
```

Install using pip:

```bash
pip install -r requirements.txt
```

This installs the `asaa` CLI. To start an assessment:
```bash
asaa start
```
