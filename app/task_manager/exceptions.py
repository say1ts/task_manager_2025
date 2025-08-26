from uuid import UUID


class TaskServiceError(Exception):
    pass


class TaskNotFoundError(TaskServiceError):
    def __init__(self, task_id: UUID):
        self.task_id = task_id
        super().__init__(f"Task with id {task_id} not found.")
