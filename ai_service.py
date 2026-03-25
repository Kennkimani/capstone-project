import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API"))

async def generate_feedback(Topic, question, student_answer, correct_answers, is_correct):

    if is_correct:
        prompt = f"""
        A student answered correctly.

        Topic: {Topic}
        Question: {question}

        Praise the student and give a slightly harder challenge question.
        """

    else:
        prompt = f"""
        A student answered incorrectly.

        Topic: {Topic}
        Question: {question}
        Student Answer: {student_answer}
        Correct Answer: {correct_answers}

        Explain why the answer is wrong in simple terms.
        Provide a short example to help them understand.
        """

    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content



async def generate_question(topic, difficulty):

    prompt = f"""
    Generate one quiz question.

    Topic: {topic}
    Difficulty: {difficulty} 

    Return the response in this format:

    Question: <question>
    Correct Answer: <answer>
    """

    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content