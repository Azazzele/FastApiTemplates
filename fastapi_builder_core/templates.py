from jinja2 import Template

# Шаблон роутера (поддерживает и синхронный SQLite, и асинхронный Postgres)
ROUTER_TEMPLATE = Template("""from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_db
from . import schemas, models
{% if require_auth -%}
from app.auth import get_current_user
{%- endif %}

router = APIRouter(prefix="/{{ module }}", tags=["{{ module }}"])

@router.{{ method|lower }}("{{ path }}", response_model={{ response_model_name }}, summary="{{ summary }}")
async def {{ endpoint_name }}(
    {%- if has_body %}payload: schemas.{{ request_model_name }}, {% endif -%}
    {% if db_type == 'postgres' %}db: AsyncSession = Depends(get_db){% else %}db: Session = Depends(get_db){% endif %}
    {%- if require_auth %}, current_user: dict = Depends(get_current_user){% endif -%}
):
    \"\"\"
    {{ summary }}
    \"\"\"
    {% if method == 'POST' -%}
    # Автоматический CRUD создания записи в БД
    db_item = models.{{ module_model_name }}(**payload.model_dump())
    db.add(db_item)
    {% if db_type == 'postgres' %}await db.commit()
    await db.refresh(db_item){% else %}db.commit()
    db.refresh(db_item){% endif %}
    return db_item
    {%- elif method == 'GET' and '{id}' in path -%}
    # Автоматическое получение записи из БД по id
    {% if db_type == 'postgres' -%}
    import sqlalchemy as sa
    result = await db.execute(sa.select(models.{{ module_model_name }}).filter(models.{{ module_model_name }}.id == id))
    db_item = result.scalars().first()
    {%- else -%}
    db_item = db.query(models.{{ module_model_name }}).filter(models.{{ module_model_name }}.id == id).first()
    {%- endif %}
    if not db_item:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    return db_item
    {%- else -%}
    # TODO: Реализовать кастомную бизнес-логику
    return {}
    {%- endif %}
""")

SCHEMA_TEMPLATE = Template("""from pydantic import BaseModel
from typing import Optional, List

class {{ model_name }}(BaseModel):
{%- for field in fields %}
    {{ field.name }}: {% if not field.required %}Optional[{{ field.type }}] = None{% else %}{{ field.type }}{% endif %}
{%- else %}
    pass
{%- endfor %}
""")


DB_MODEL_TEMPLATE = Template("""from sqlalchemy import Column, Integer, String, Boolean, Float
from app.database import Base

class {{ module_model_name }}(Base):
    __tablename__ = "{{ table_name }}"

    id = Column(Integer, primary_key=True, index=True)
{%- for field in fields %}
    {{ field.name }} = Column({% if field.type == 'str' %}String{% elif field.type == 'int' %}Integer{% elif field.type == 'float' %}Float{% elif field.type == 'bool' %}Boolean{% endif %})
{%- endfor %}
""")

TEST_TEMPLATE = Template("""import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_{{ endpoint_name }}_success():
    \"\"\"
    Автоматический тест для эндпоинта {{ method }} {{ path }}
    \"\"\"
    {% if method == 'POST' -%}
    payload = {
        {%- for field in fields %}
        "{{ field.name }}": {% if field.type == 'str' %}"test_val"{% elif field.type == 'int' %}1{% elif field.type == 'float' %}1.0{% elif field.type == 'bool' %}True{% endif %},
        {%- endfor %}
    }
    headers = {"Authorization": "Bearer test_token"} if {{ require_auth }} else None
    response = client.post("/{{ module }}{{ path }}", json=payload, headers=headers)
    
    if {{ require_auth }}:
        assert response.status_code == 401
    else:
        assert response.status_code in [200, 201]
        
    {%- else -%}
    headers = {"Authorization": "Bearer test_token"} if {{ require_auth }} else None
    response = client.{{ method|lower }}("/{{ module }}{{ path }}", headers=headers)
    
    if {{ require_auth }}:
        assert response.status_code == 401
    else:
        assert response.status_code == 200
    {%- endif %}
""")

DOCKERFILE_TEMPLATE = """FROM python:3.11-slim
WORKDIR /code
RUN apt-get update && apt-get install -y --no-install-recommends gcc build-essential && rm -rf /var/lib/apt/lists/*
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./app /code/app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

# Динамический docker-compose, добавляющий Postgres, если он выбран
DOCKER_COMPOSE_TEMPLATE = Template("""version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./app:/code/app
    environment:
      - ENV=development
      {% if db_type == 'postgres' -%}
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/fastapi_db
      {%- endif %}
    depends_on:
      {% if db_type == 'postgres' -%}
      - db
      {%- else -%}
      []
      {%- endif %}
    restart: always

  {% if db_type == 'postgres' -%}
  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=fastapi_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

volumes:
  postgres_data:
  {%- endif %}
""")
