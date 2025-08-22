from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from app.task_manager.schemas import TaskCreate, TaskResponse, TaskUpdate
from app.task_manager.service import TaskNotFoundError
from app.task_manager.dependencies import TaskServiceDep
from app.auth.dependencies import CurrentUser

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task: TaskCreate, service: TaskServiceDep, current_user: CurrentUser
):
    return await service.create_task(task, user_id=current_user.id)


@router.get("/", response_model=list[TaskResponse])
async def get_all_tasks(service: TaskServiceDep, current_user: CurrentUser):
    return await service.get_all_tasks(user_id=current_user.id)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_by_id(
    task_id: UUID, service: TaskServiceDep, current_user: CurrentUser
):
    try:
        return await service.get_task_by_id(task_id, user_id=current_user.id)
    except TaskNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    update: TaskUpdate,
    service: TaskServiceDep,
    current_user: CurrentUser,
):
    try:
        return await service.update_task(task_id, update, user_id=current_user.id)
    except TaskNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID, service: TaskServiceDep, current_user: CurrentUser
):
    try:
        await service.delete_task(task_id, user_id=current_user.id)
    except TaskNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
