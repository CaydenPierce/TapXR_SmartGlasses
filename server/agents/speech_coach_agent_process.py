import time
import traceback
import asyncio

# custom
from DatabaseHandler import DatabaseHandler
from agents.speech_coach_agent import run_speech_coach_agent
from server_config import openai_api_key
from logger_config import logger
from constants import SPEECH_AGENT

run_period = 20
transcript_back_time = run_period * 1.1
total_transcript_context_time = 5 * 60
minimum_topic_time = 20 #the minimum amount of time since last topic change for a new topic chnage


def speech_coach_agent_processing_loop():
    FILLER_WORDS = 0
    print("START SPEECH COACH AGENT PROCESSING LOOP")
    dbHandler = DatabaseHandler(parent_handler=False)
    loop = asyncio.get_event_loop()

    while True:
        if not dbHandler.ready:
            print("dbHandler not ready")
            time.sleep(0.1)
            continue

        # wait for some transcripts to load in
        time.sleep(5)

        try:
            pLoopStartTime = time.time()
            # Check for new transcripts
            # print("RUNNING ADHD STMB LOOP")
            newTranscripts = dbHandler.get_recent_transcripts_from_last_nseconds_for_all_users(
                n=transcript_back_time)

            words_to_show = None
            for transcript in newTranscripts:
                if not dbHandler.get_user_feature_enabled(transcript['user_id'], SPEECH_AGENT): continue                
                # ADD FOLLOWING LINE LATER                
                ctime = time.time()
                user_id = transcript['user_id']

        
                transcript, _, _ = dbHandler.get_transcripts_from_last_nseconds_for_user_as_string(user_id, n=transcript_back_time)
            
                try:
                    # number_of_filler_words = int(number_of_filler_words)
                    number_of_filler_words = run_speech_coach_agent(transcript)                    
                    FILLER_WORDS += int(number_of_filler_words)
                    print("NUMBER OF FILLER WORDS SO FAR: ", FILLER_WORDS)
                except Exception as e:
                    print("Failed to convert number of filler words to int")
                    print(e)
                    print(number_of_filler_words)

                loop_time = time.time() - ctime
                print(f"RAN SPEECH COACH AGENT IN : {loop_time}")

        except Exception as e:
            print("Exception in SPEECH COACH loop...:")
            print(e)
            traceback.print_exc()

        finally:
            # lock.release()
            pLoopEndTime = time.time()
            #print("=== language leanring loop completed in {} seconds overall ===".format(
            #    round(pLoopEndTime - pLoopStartTime, 2)))

        #run again after delay for run_period
        time.sleep(max(0, run_period - (pLoopEndTime - pLoopStartTime)))
