import threading
import queue

class TaskQueue:
    """
    A TaskQueue class that manages tasks in a separate thread.

    This class provides a simple way to queue tasks and execute them asynchronously
    using a single worker thread. Tasks added to the queue are functions that will
    be executed by the worker thread.

    Attributes:
        tasks (queue.Queue): A queue that stores the tasks to be executed.
        thread (threading.Thread): The worker thread that executes tasks from the queue.

    Methods:
        __init__(self): Initializes a new instance of the TaskQueue class, starts the worker thread.
        _worker(self): The worker method that runs in a separate thread and executes tasks from the queue.
        add_task(self, task): Adds a task to the queue for execution by the worker thread.
    """
    def __init__(self):
        """
        Initializes a new instance of the TaskQueue class.

        This constructor creates a new queue for tasks and starts a daemon worker thread
        that will execute those tasks.
        """
        self.tasks = queue.Queue()
        self.thread = threading.Thread(target=self._worker)
        self.thread.daemon = True
        self.thread.start()

    def _worker(self):
        """
        The worker method that runs in a separate thread.

        This method continuously retrieves tasks from the queue and executes them.
        If a `None` task is retrieved, the loop breaks, effectively stopping the thread.
        """
        while True:
            task = self.tasks.get()
            if task is None:
                break
            try:
                task()
            finally:
                self.tasks.task_done()

    def add_task(self, task):
        """
        Adds a task to the queue for execution by the worker thread.

        Parameters:
            task (callable): The task to be added to the queue. It should be a callable with no arguments.
        """
        self.tasks.put(task)






# Example usage:
import time

def example_task(num):
    print(f"\nTask {num} is running")
    time.sleep(2)
    print(f"Task {num} is done")

if __name__ == "__main__":
    task_queue = TaskQueue()
    i = 0

    while True:
        input(">> ")
        task_queue.add_task(example_task(i))
        i += 1
    
    print("Tasks have been added")
