# custom
from collections import defaultdict
from agents.agent_utils import format_list_data
from server_config import openai_api_key

# langchain
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import (
    HumanMessage
)
from langchain.output_parsers import PydanticOutputParser
from langchain.schema import OutputParserException
from pydantic import BaseModel, Field
from helpers.time_function_decorator import time_function

#pinyin
import json
from pypinyin import pinyin, Style

from Modules.LangchainSetup import *

language_learning_agent_prompt_blueprint = """
Intro:
The aim is to help the language learner to understand new words in the context of real conversations. This helps them learn the words, and it helps the follow along with the dialog. Only a few words are translated so the language learner can rely on their built-in knowledge as much as possible.

You are a highly skilled proffesional translator and advanced language teacher, fluent in Russian, Chinese, French, Spanish, German, English, and more. You are listening to a user's conversation right now. The user is learning {target_language}. The user's first language is {source_language}.

Target Language: {target_language}
Source Language: {source_language}

*** If the Input Text is in the target language, your translation is in the source language.
*** If Input Text is in the source language, translate to the target language.
*** Never do intralanguage translation.

You identify vocabulary that the user might not know and then translate only that vocabulary. You should *only* translate words you think the learner doesn't know. Outputting zero or only one translation is OK (3 maximum). If the learner's score is <50, they will probably need every few words defined. 50-75 fluency might need 1 word per sentence. 75+, only more rare words, once every few minutes.

Process:
0. Consider the fluency level of the user, which is {fluency_level}, where 0<=fluency_level<=100, with 0 being complete beginner, 50 being conversational, 75 intermediate and 100 being native speaker.
This level influences the selection of words to translate:
   - 0-49 (Beginner): Translate every few words, focusing on slightly more common vocabulary that a beginner might not know.
   - 50-74 (Conversational): Translate approximately one word per sentence, selecting words that are somewhat common but might still pose challenges.
   - 75-99 (Intermediate): Only translate rare or complex words that an intermediate learner might not encounter frequently.
   - 100 (Native Speaker): No translation is necessary unless extremely rare or technical terms are used.
1. Skim through the conversation context and identify 0 to 3 words that may unfamiliar to someone with a fluency level of {fluency_level}.
2. Consider the frequency rank percentile of the words in the conversation context. The percentile is a number between 0 and 100, which determines how rare the word is in the language. Percentiles provide a measure of how a word's frequency compares to the rest of the words in the language: a word in 10th percential is more uncommon than 90% of the words in the language. Conversely, a word in the 99th percentile is common, more frequent than 99% of the words. Use the percentile to determine words that the user might not know.
3. For each of the zero to three identified words in the input text language, provide a 1-2 word translation in the opposite language (either {source_language} or {target_language}, whatever is opposite to the input text. Try to make translations as short as posible. Use context from the conversation to inform your translations.
4. Output Python dictionary only using the format instructions below. The keys are the rare, relevant words in the language of the input text, and the values are the translation of those words into the opposite of the input text language. There should be <= 3 words per run in the dict. Don't output any explanation or extra data, just this simple info. It's OK to output zero words if there are no appopriately rare words in the input text.
4. Output response using the format instructions below. The keys are the rare, relevant words in the language of the input text, and the values are the translation of those words into the opposite of the input text language. There should be <= 3 words per run in the dict. Don't output any explanation or extra data, just this simple info. It's OK to output zero words if there are no appopriately rare words in the input text.

Examples:

Conversation 1: "I ran for the train, but the fruit stand was in the way"
Output 1: {{"train" : <translation>, "fruit stand" : translation}}
Conversation 2: "Oh, so you're a student of biology, that's great"
Output 2: {{"student" : <translation>, "biology" : translation}}
Conversation 3: "let's go there and say hello to her"
Output 3 (empty, no results): {{}}
Conversation 4: "I love to look at the stars and think of my family"
Output 3: {{"stars" : <translation>}}

DO NOT define common words like "yes", "no", "he", "hers", "to", "from", "thank you", "please", "because", etc. in ANY language - they are too common. Focus on rare words.

Frequency Ranking:
IGNORE THIS FOR NOW: The frequency ranking of each word tells you how common it is in daily speech. The frequency ranking of the wordsin the conversation context are: ```{word_rank}```

FINAL DATA AND COMMANDS:
Previous Definitions:
Don't define any of the words in this list, as they were all recently defined:
```{live_translate_word_history}```

Input Text (transcript from user's live conversation):
```{conversation_context}```

Frequency Ranking:
The frequency ranking of each word tells you how common it is in daily speech as a percentile (0 is most common, 100 is most rare). The frequency ranking of the words in the "Input Text" conversation transcript are:
```
{word_rank}
```

Follow this format when you output: {format_instructions}

Define at least one of the words this time.

Now provide the output using the format instructions above:
"""

#Preface Rule:
#Use Pinyin when writing Chinese. Never use Chinese characters, use Pinyin.
#, use Pinyin if writing Chinese)
#3.a. If writing Chinese, output exclusively in Pinyin, avoiding Chinese characters entirely.
#NEVER OUTPUT CHINESE CHARACTERS. USE PINYIN, USE THE LATIN ALPHABET PINYIN FOR CHINESE.

#Use Pinyin when writing Chinese. Never use Chinese characters, use Pinyin.

# in_word_translation must be in Pinyin or Latin characters.

# If writing Chinese, output exclusively in Pinyin, avoiding Chinese characters entirely.


def format_list_data(data: dict) -> str:
    """
    Formats a dict into a string that can be used in a prompt
    """
    data_str = ""
    for key, value in data.items():
        data_str += f"{key} : {value}\n"
    return data_str


@time_function()
def run_language_learning_agent(conversation_context: str, word_rank: dict, target_language="Russian", transcribe_language="English", live_translate_word_history=""):
    # start up GPT3 connection
    llm = get_langchain_gpt35(temperature=0.2)

    # "It's a beautiful day to be out and about at the library! And you should come to my house tomorrow!"
    conversation_context = conversation_context
    fluency_level = 30  # Example fluency level
    #target_language = "Chinese (Pinyin)"
    source_language = "English"

    class LanguageLearningAgentQuery(BaseModel):
        """
        Proactive language learning agent
        """
        translated_words: dict = Field(
            description="the target language words translated into source language words")

    language_learning_agent_query_parser = PydanticOutputParser(
        pydantic_object=LanguageLearningAgentQuery)

    extract_language_learning_agent_query_prompt = PromptTemplate(
        template=language_learning_agent_prompt_blueprint,
        input_variables=["conversation_context", "target_language", "source_language", "fluency_level", "word_rank", "live_translate_word_history"],
        partial_variables={
            "format_instructions": language_learning_agent_query_parser.get_format_instructions()}
    )

    word_rank_string = format_list_data(word_rank)

    language_learning_agent_query_prompt_string = extract_language_learning_agent_query_prompt.format_prompt(
        conversation_context=conversation_context,
        source_language=source_language,
        target_language=target_language,
        fluency_level=fluency_level,
        word_rank=word_rank_string,
        live_translate_word_history=live_translate_word_history
    ).to_string()

    #print("LANGUAGE LEARNING PROMPT********************************")
    #print(language_learning_agent_query_prompt_string)

    # print("Proactive meta agent query prompt string", language_learning_agent_query_prompt_string)

    response = llm(
        [HumanMessage(content=language_learning_agent_query_prompt_string)])
    print(response)

    try:
        translated_words = language_learning_agent_query_parser.parse(
            response.content).translated_words

        #convert Chinese characters into Pinyin
        # Function to convert Chinese text to Pinyin
        def chinese_to_pinyin(chinese_text):
            return ' '.join([item[0] for item in pinyin(chinese_text, style=Style.TONE)])

        # Apply Pinyin conversion if target_language is "Chinese (Pinyin)"
        if target_language == "Chinese (Pinyin)":
            translated_words_pinyin = {chinese_to_pinyin(word): chinese_to_pinyin(translated_words[word]) for word in translated_words}
        else:
            translated_words_pinyin = translated_words

        translated_words_obj = []
        for word, translation in translated_words_pinyin.items():
            translated_words_obj.append({"in_word": word, "in_word_translation": translation})

        print("TRANSLATED OUTPUT: ")
        print(translated_words_obj)
        return translated_words_obj
    except OutputParserException as e:
        print('parse fail')
        print(e)
        return None


if __name__ == "__main__":
    # "It's a beautiful day to be out and about at the library! And you should come to my house tomorrow!"
    conversation_context = "It's a beautiful day to be out and about at the library! And you should come to my house tomorrow!"
    word_rank = {"beautiful": 100, "library": 200, "house": 300}
    run_language_learning_agent(conversation_context, word_rank)
