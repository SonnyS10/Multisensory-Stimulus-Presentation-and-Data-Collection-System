import time 
while True:
    try:
        clock = time.time()
        print("Current time in seconds since the Epoch:", clock)
    except Exception as e:
        print(f"Error occurred: {e}. Retrying...")