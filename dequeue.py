from collections import deque

def process_queue(my_queue):
    """
    Processes a queue until it is empty, keeping track of the last element.

    Args:
        my_queue: A deque (double-ended queue) representing the queue.

    Returns:
        The last element that was in the queue, or None if the queue was initially empty.
    """
    last = None  # Initialize 'last' to None
    print(f"Initial queue: {my_queue}") # Print initial queue

    while my_queue:  # While the queue is not empty
        last = my_queue.popleft()  # Remove the first element and store it in 'last'
        print(f"Dequeued: {last}, Current queue: {my_queue}") # Print what is dequeued and current queue

    print(f"Final value of 'last': {last}") # Print the final value of last
    return last

if __name__ == "__main__":
    # Create a queue using a deque
    my_queue = deque([1, 2, 3, 4, 5])

    # Process the queue
    last_element = process_queue(my_queue)

    # Print the result
    if last_element is not None:
        print(f"The last element in the queue was: {last_element}")
    else:
        print("The queue was empty.")

    print("\n--- Example with an empty queue ---")
    empty_queue = deque()
    last_element_empty = process_queue(empty_queue)
    if last_element_empty is None:
        print("The queue was empty.")
