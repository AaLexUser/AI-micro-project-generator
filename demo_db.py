from config.db_config import Base, engine, SessionLocal
from repo.sqlalchemy_repos import SAStudentRepo, SATaskRepo
from model.models import Student, Task


def init_db():
    # Создаём таблицы
    Base.metadata.create_all(bind=engine)


def run_demo():
    with SessionLocal() as session:
        students = SAStudentRepo(session)
        tasks = SATaskRepo(session)

        # создаём студента
        st = students.create()
        session.flush()  # чтобы st.id появился

        # создаём задачи
        t1 = tasks.create(description="SQL JOIN mini-case")
        t2 = tasks.create(description="pandas groupby case")
        session.flush()

        # выдаём задачи студенту
        students.assign_task(st.id, t1.id)
        students.assign_task(st.id, t2.id)

        # завершаем одну задачу
        students.mark_finished(st.id, t1.id)

        session.commit()

        # читаем открытые задачи
        open_tasks = students.list_tasks(st.id, open_only=True)
        print("Открытые задачи:", [t.description for t in open_tasks])


if __name__ == "__main__":
    init_db()
    run_demo()
