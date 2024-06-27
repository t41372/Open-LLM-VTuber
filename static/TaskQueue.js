class TaskQueue {
    constructor() {
        this.queue = [];
        this.running = false;
        this.taskInterval = 3000;
    }

    addTask(task) {
        this.queue.push(task);
        this.runNextTask();
    }

    clearQueue() {
        this.queue = [];
    }

    async runNextTask() {
        if (this.running || this.queue.length === 0) {
            if (this.queue.length === 0) {
                console.log("Queue is empty");
            }
            return;
        }

        this.running = true;
        const task = this.queue.shift();
        try {
            await task();
        } catch (error) {
            console.error('Task failed', error);
        }
        this.running = false;
        setTimeout(() => this.runNextTask(), this.taskInterval);
        // this.runNextTask();
    }
}

// export default TaskQueue;
const taskQueue = new TaskQueue()