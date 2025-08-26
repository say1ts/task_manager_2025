import pytest
from unittest.mock import AsyncMock
from uuid_extensions import uuid7
from app.task_manager import TaskService, TaskNotFoundError
from app.task_manager.schemas import TaskCreate, TaskUpdate, TaskStatus, Task

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_task_repository():
    """Фикстура, создающая мок-объект для TaskSQLAlchemyRepository."""
    return AsyncMock()


@pytest.fixture
def task_service(mock_task_repository):
    """Фикстура, создающая экземпляр TaskService с мок-репозиторием."""
    return TaskService(mock_task_repository)


@pytest.fixture
def sample_user_id():
    """Фикстура, предоставляющая UUID для пользователя."""
    return uuid7()


@pytest.fixture
def sample_task(sample_user_id):
    """Фикстура, создающая образец DTO Task."""
    return Task(
        task_id=uuid7(),
        title="Sample Task",
        description="A description",
        status=TaskStatus.CREATED,
        user_id=sample_user_id,
    )


async def test_get_all_tasks(
    task_service: TaskService, mock_task_repository, sample_user_id, sample_task
):
    """Тест успешного получения всех задач для пользователя."""
    mock_task_repository.get_all.return_value = [sample_task]
    result = await task_service.get_all_tasks(user_id=sample_user_id)
    mock_task_repository.get_all.assert_called_once_with(user_id=sample_user_id)
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], Task)
    assert result[0].task_id == sample_task.task_id
    assert result[0].title == sample_task.title


async def test_get_task_by_id_success(
    task_service: TaskService, mock_task_repository, sample_user_id, sample_task
):
    """Тест успешного получения задачи по ID."""
    mock_task_repository.get_by_id.return_value = sample_task
    result = await task_service.get_task_by_id(
        task_id=sample_task.task_id, user_id=sample_user_id
    )
    mock_task_repository.get_by_id.assert_called_once_with(
        task_id=sample_task.task_id, user_id=sample_user_id
    )
    assert isinstance(result, Task)
    assert result.title == sample_task.title
    assert result.task_id == sample_task.task_id


async def test_get_task_by_id_not_found(
    task_service: TaskService, mock_task_repository, sample_user_id
):
    """Тест получения несуществующей задачи."""
    non_existent_id = uuid7()
    mock_task_repository.get_by_id.side_effect = TaskNotFoundError(non_existent_id)
    with pytest.raises(TaskNotFoundError):
        await task_service.get_task_by_id(
            task_id=non_existent_id, user_id=sample_user_id
        )


async def test_create_task(
    task_service: TaskService, mock_task_repository, sample_user_id, sample_task
):
    """Тест успешного создания задачи."""
    task_data = TaskCreate(
        title="New Task", description="New Desc", status=TaskStatus.CREATED
    )
    mock_task_repository.create.return_value = sample_task
    result = await task_service.create_task(task_data=task_data, user_id=sample_user_id)
    mock_task_repository.create.assert_called_once_with(
        task_data, user_id=sample_user_id
    )
    assert isinstance(result, Task)
    assert result.task_id == sample_task.task_id


@pytest.mark.parametrize(
    "update_data, expected_title, expected_description, expected_status",
    [
        (
            TaskUpdate(title="Updated Title"),
            "Updated Title",
            "A description",
            TaskStatus.CREATED,
        ),
        (
            TaskUpdate(description="New Description"),
            "Sample Task",
            "New Description",
            TaskStatus.CREATED,
        ),
        (
            TaskUpdate(status=TaskStatus.COMPLETED),
            "Sample Task",
            "A description",
            TaskStatus.COMPLETED,
        ),
    ],
    ids=["update_title", "update_description", "update_status"],
)
async def test_update_task_success(
    task_service: TaskService,
    mock_task_repository,
    sample_user_id,
    sample_task,
    update_data,
    expected_title,
    expected_description,
    expected_status,
):
    """Тест успешного обновления задачи с разными входными данными."""
    updated_task = Task(
        task_id=sample_task.task_id,
        title=expected_title,
        description=expected_description,
        status=expected_status,
        user_id=sample_task.user_id,
    )
    mock_task_repository.update.return_value = updated_task
    result = await task_service.update_task(
        task_id=sample_task.task_id, update_data=update_data, user_id=sample_user_id
    )
    mock_task_repository.update.assert_called_once_with(
        sample_task.task_id, sample_user_id, update_data
    )
    assert isinstance(result, Task)
    assert result.title == expected_title
    assert result.description == expected_description
    assert result.status == expected_status


async def test_update_task_not_found(
    task_service: TaskService, mock_task_repository, sample_user_id
):
    """Тест обновления несуществующей задачи."""
    update_data = TaskUpdate(title="Updated Title")
    non_existent_id = uuid7()
    mock_task_repository.update.side_effect = TaskNotFoundError(non_existent_id)
    with pytest.raises(TaskNotFoundError):
        await task_service.update_task(
            task_id=non_existent_id, update_data=update_data, user_id=sample_user_id
        )


async def test_delete_task_success(
    task_service: TaskService, mock_task_repository, sample_user_id, sample_task
):
    """Тест успешного удаления задачи."""
    mock_task_repository.delete.return_value = None
    await task_service.delete_task(task_id=sample_task.task_id, user_id=sample_user_id)
    mock_task_repository.delete.assert_called_once_with(
        task_id=sample_task.task_id, user_id=sample_user_id
    )


async def test_delete_task_not_found(
    task_service: TaskService, mock_task_repository, sample_user_id
):
    """Тест удаления несуществующей задачи."""
    non_existent_id = uuid7()
    mock_task_repository.delete.side_effect = TaskNotFoundError(non_existent_id)
    with pytest.raises(TaskNotFoundError):
        await task_service.delete_task(task_id=non_existent_id, user_id=sample_user_id)
